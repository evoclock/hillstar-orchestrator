# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

# Bounded iteration: an implementer-reviewer cycle that ends on success or on
# a stated maximum, expressed without a back edge.

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.graph import WorkflowGraph  # noqa: E402
from execution.loops import LoopError, compile_loops, condition_met  # noqa: E402
from execution.runner import WorkflowRunner  # noqa: E402


def _workflow(max_attempts=3, until=None):
	return {
		"id": "loop-test",
		"graph": {
			"nodes": {
				"seed": {"tool": "script_run", "input": "prepare"},
				"implement": {"tool": "model_call", "input": "write it {{ seed.output }}"},
				"review": {"tool": "model_call", "input": "review {{ implement.output }}"},
				"publish": {"tool": "file_write", "input": "{{ review.output }}"},
			},
			"edges": [
				{"from": "seed", "to": "implement"},
				{"from": "implement", "to": "review"},
				{"from": "review", "to": "publish"},
			],
			"loops": [
				{
					"id": "fix",
					"body": ["implement", "review"],
					"max_attempts": max_attempts,
					"until": until or {"node": "review", "contains": "sign-off"},
				}
			],
		},
	}


class TestCompilation:
	def test_expands_the_body_once_per_attempt(self):
		g = compile_loops(_workflow(max_attempts=3))["graph"]
		assert set(g["nodes"]) == {
			"seed", "publish",
			"implement", "review",
			"implement@2", "review@2",
			"implement@3", "review@3",
		}

	def test_leaves_a_workflow_without_loops_alone(self):
		w = _workflow()
		w["graph"].pop("loops")
		assert compile_loops(w)["graph"]["nodes"].keys() == w["graph"]["nodes"].keys()

	def test_the_result_is_a_dag_the_executor_accepts(self):
		# The whole point: iteration without a cycle.
		graph = WorkflowGraph(_workflow(max_attempts=3))
		order = graph.get_execution_order()
		assert order.index("implement") < order.index("review")
		assert order.index("review") < order.index("implement@2")
		assert order.index("review@3") < order.index("publish")

	def test_each_attempt_reads_its_own_predecessor(self):
		nodes = compile_loops(_workflow())["graph"]["nodes"]
		assert "{{ implement@2.output }}" in nodes["review@2"]["input"]
		assert "{{ implement@3.output }}" in nodes["review@3"]["input"]

	def test_a_reference_outside_the_body_is_not_rewritten(self):
		# seed runs once; every attempt should see the same value.
		nodes = compile_loops(_workflow())["graph"]["nodes"]
		assert "{{ seed.output }}" in nodes["implement@2"]["input"]

	def test_downstream_reads_the_final_attempt(self):
		g = compile_loops(_workflow(max_attempts=3))["graph"]
		assert {"from": "review@3", "to": "publish"} in g["edges"]

	# The edge and the reference must agree. They did not: publish waited on
	# attempt 3 while reading attempt 1, so a failed first attempt left the
	# template unresolved and written out literally.
	def test_a_node_outside_the_loop_reads_the_final_attempt(self):
		nodes = compile_loops(_workflow(max_attempts=3))["graph"]["nodes"]
		assert nodes["publish"]["input"] == "{{ review@3.output }}"

	def test_every_attempt_records_its_place(self):
		nodes = compile_loops(_workflow())["graph"]["nodes"]
		assert nodes["implement"]["loop"] == {"id": "fix", "attempt": 1, "of": 3}
		assert nodes["review@3"]["loop"] == {"id": "fix", "attempt": 3, "of": 3}

	def test_a_single_attempt_expands_to_the_plain_graph(self):
		g = compile_loops(_workflow(max_attempts=1))["graph"]
		assert set(g["nodes"]) == {"seed", "implement", "review", "publish"}


class TestBoundIsMandatory:
	# An unbounded loop in an agent graph is an unbounded bill, so it is not
	# expressible rather than discouraged.
	@pytest.mark.parametrize("attempts", [None, 0, -1, "many", 2.5])
	def test_refuses_a_loop_without_a_finite_bound(self, attempts):
		w = _workflow()
		w["graph"]["loops"][0]["max_attempts"] = attempts
		with pytest.raises(LoopError, match="max_attempts"):
			compile_loops(w)

	def test_refuses_a_body_naming_a_node_that_does_not_exist(self):
		w = _workflow()
		w["graph"]["loops"][0]["body"] = ["implement", "ghost"]
		with pytest.raises(LoopError, match="ghost"):
			compile_loops(w)

	def test_refuses_an_exit_check_outside_the_body(self):
		w = _workflow(until={"node": "publish", "contains": "x"})
		with pytest.raises(LoopError, match="not in the body"):
			compile_loops(w)

	def test_refuses_an_exit_check_with_no_test(self):
		w = _workflow(until={"node": "review"})
		with pytest.raises(LoopError, match="contains"):
			compile_loops(w)


class TestExitCondition:
	def test_met_when_the_output_contains_the_marker(self):
		assert condition_met({"node": "review", "contains": "sign-off"}, {"review": "VERDICT sign-off"})

	def test_reads_the_output_field_of_a_structured_result(self):
		assert condition_met({"node": "review", "contains": "sign-off"}, {"review": {"output": "sign-off"}})

	# An absent result is not evidence of success.
	def test_not_met_when_the_node_produced_nothing(self):
		assert not condition_met({"node": "review", "contains": "sign-off"}, {})

	def test_not_contains_inverts(self):
		assert condition_met({"node": "review", "not_contains": "revise"}, {"review": "sign-off"})
		assert not condition_met({"node": "review", "not_contains": "revise"}, {"review": "revise"})


class TestSkippingSatisfiedAttempts:
	def _run(self, outputs_by_node):
		graph = WorkflowGraph(_workflow(max_attempts=3))
		ran = []

		def executor(node_id, node, inputs):
			ran.append(node_id)
			return outputs_by_node.get(node_id, "revise: not yet")

		for node_id in graph.get_execution_order():
			graph.execute_node(node_id, executor)
		return ran, graph

	def test_later_attempts_are_skipped_once_the_loop_succeeds(self):
		ran, graph = self._run({"review": "VERDICT sign-off"})
		assert "implement@2" not in ran
		assert "review@3" not in ran

	# Downstream nodes read the LAST attempt, because that is the loop's result.
	# A skipped attempt therefore carries the result that satisfied the exit
	# condition; a marker there would hand the next node "skipped" instead of
	# the review that signed off.
	def test_a_skipped_attempt_carries_the_winning_result(self):
		_, graph = self._run({"review": "VERDICT sign-off"})
		assert graph.node_outputs["review@2"] == "VERDICT sign-off"
		assert graph.node_outputs["review@3"] == "VERDICT sign-off"

	def test_every_attempt_runs_when_nothing_succeeds(self):
		ran, _ = self._run({})
		assert "implement@2" in ran and "review@3" in ran

	def test_a_skip_is_visible_in_the_trace(self):
		_, graph = self._run({"review": "VERDICT sign-off"})
		skipped = [t for t in graph.trace if t["status"] == "skipped"]
		assert skipped and skipped[0]["reason"] == "loop exit condition already met"

	def test_stops_at_the_attempt_that_succeeds(self):
		ran, _ = self._run({"review@2": "VERDICT sign-off"})
		assert "implement@2" in ran
		assert "implement@3" not in ran


class TestFeedbackToTheNextAttempt:
	"""The reviewer's revisions must reach the next implementer attempt.

	Without this the loop is a retry of the identical prompt: the implementer
	never sees why it failed, so it reproduces the same defect and the extra
	attempts buy nothing.
	"""

	def _wf(self):
		w = _workflow(max_attempts=3)
		w["graph"]["nodes"]["implement"]["input"] = (
			"write it {{ seed.output }}\nPrevious review: {{ prev.review.output }}"
		)
		return w

	def test_the_second_attempt_reads_the_first_review(self):
		nodes = compile_loops(self._wf())["graph"]["nodes"]
		assert "{{ review.output }}" in nodes["implement@2"]["input"]

	def test_the_third_attempt_reads_the_second_review(self):
		nodes = compile_loops(self._wf())["graph"]["nodes"]
		assert "{{ review@2.output }}" in nodes["implement@3"]["input"]

	# Nothing has been reviewed on the first attempt.
	def test_the_first_attempt_has_no_dangling_reference(self):
		nodes = compile_loops(self._wf())["graph"]["nodes"]
		assert "prev." not in nodes["implement"]["input"]
		assert "{{" not in nodes["implement"]["input"].split("Previous review:")[1]

	def test_the_expansion_is_still_a_dag(self):
		graph = WorkflowGraph(self._wf())
		order = graph.get_execution_order()
		assert order.index("review") < order.index("implement@2")
		assert order.index("review@2") < order.index("implement@3")


class TestExitOnEvidenceAndOpinion:
	"""A loop that ends on the reviewer alone can exit on broken code.

	Measured: two reviewers signed off unanimously on code that failed two
	ground-truth cases. The loop stopped iterating with the defects in place,
	because nothing in its exit condition consulted what the code actually did.
	"""

	def _wf(self, attempts=3):
		return {
			"id": "evidence-loop",
			"graph": {
				"nodes": {
					"implement": {"tool": "model_call", "input": "write it"},
					"check": {"tool": "script_run", "input": "run it"},
					"review": {"tool": "model_call", "input": "review {{ implement.output }}"},
					"publish": {"tool": "file_write", "input": "{{ review.output }}"},
				},
				"edges": [
					{"from": "implement", "to": "check"},
					{"from": "check", "to": "review"},
					{"from": "review", "to": "publish"},
				],
				"loops": [{
					"id": "revise",
					"body": ["implement", "check", "review"],
					"max_attempts": attempts,
					"until": {"all_of": [
						{"node": "review", "contains": "sign-off"},
						{"node": "check", "contains": "PASS"},
					]},
				}],
			},
		}

	def _run(self, outputs):
		graph = WorkflowGraph(self._wf())
		ran = []

		def executor(node_id, node, inputs):
			ran.append(node_id)
			return outputs.get(node_id, "revise: not yet")

		for node_id in graph.get_execution_order():
			graph.execute_node(node_id, executor)
		return ran, graph

	def test_compiles_with_a_compound_condition(self):
		nodes = compile_loops(self._wf())["graph"]["nodes"]
		assert "implement@2" in nodes and "check@3" in nodes

	# The failure this prevents.
	def test_keeps_going_when_the_reviewer_signs_off_on_failing_code(self):
		ran, _ = self._run({"review": "VERDICT sign-off", "check": "FAIL: no_header"})
		assert "implement@2" in ran
		assert "implement@3" in ran

	def test_keeps_going_when_the_code_passes_but_the_reviewer_objects(self):
		ran, _ = self._run({"review": "revise", "check": "PASS: every case"})
		assert "implement@2" in ran

	def test_stops_when_evidence_and_opinion_agree(self):
		ran, _ = self._run({"review": "VERDICT sign-off", "check": "PASS: every case"})
		assert "implement@2" not in ran

	def test_a_single_condition_still_works(self):
		w = self._wf()
		w["graph"]["loops"][0]["until"] = {"node": "review", "contains": "sign-off"}
		nodes = compile_loops(w)["graph"]["nodes"]
		assert "review@3" in nodes

	def test_refuses_a_condition_naming_a_node_outside_the_body(self):
		w = self._wf()
		w["graph"]["loops"][0]["until"] = {"all_of": [{"node": "publish", "contains": "x"}]}
		with pytest.raises(LoopError, match="not in the body"):
			compile_loops(w)


class TestScriptRunFailurePropagation:
	def test_nonzero_script_run_fails_the_workflow(self, tmp_path):
		workflow = {
			"id": "script-failure",
			"graph": {
				"nodes": {
					"check": {
						"tool": "script_run",
						"parameters": {"script": "false"},
					}
				},
				"edges": [],
			},
		}
		workflow_path = tmp_path / "workflow.json"
		workflow_path.write_text(json.dumps(workflow))
		runner = WorkflowRunner(str(workflow_path), output_dir=str(tmp_path / "output"))

		with pytest.raises(Exception, match="script exited with return code 1"):
			runner.execute()
