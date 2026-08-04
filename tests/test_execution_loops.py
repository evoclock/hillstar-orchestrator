# Bounded iteration: an implementer-reviewer cycle that ends on success or on
# a stated maximum, expressed without a back edge.

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from execution.graph import WorkflowGraph  # noqa: E402
from execution.loops import LoopError, compile_loops, condition_met  # noqa: E402


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
		assert graph.node_outputs["review@2"] == {"skipped": True}

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
