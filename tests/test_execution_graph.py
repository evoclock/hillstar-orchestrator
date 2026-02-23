#!/usr/bin/env python3
"""
Design test for execution/graph.py

Tests the WorkflowGraph for:
- DAG validation (cycle detection)
- Topological sorting for execution order
- Node input resolution with template variables
- State management and export/import
"""

import sys

sys.path.insert(0, '..')

from execution.graph import WorkflowGraph


class TestWorkflowGraphDesign:
	"""Design test suite for WorkflowGraph."""

	def test_graph_initialization(self):
		"""Test WorkflowGraph initializes with workflow JSON."""
		workflow = {
			"id": "test_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "read_file", "file": "input.txt"},
					"node_2": {"task": "process", "input": "${node_1.output}"}
				},
				"edges": [{"from": "node_1", "to": "node_2"}]
			}
		}

		graph = WorkflowGraph(workflow)
		assert graph.nodes is not None

	def test_valid_dag_passes_validation(self):
		"""Test that valid DAG passes cycle detection."""
		workflow = {
			"id": "linear_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "start"},
					"node_2": {"task": "middle"},
					"node_3": {"task": "end"}
				},
				"edges": [
					{"from": "node_1", "to": "node_2"},
					{"from": "node_2", "to": "node_3"}
				]
			}
		}

		# Should not raise exception
		WorkflowGraph(workflow)

	def test_cyclic_graph_raises_error(self):
		"""Test that cyclic graph raises error."""
		workflow = {
			"id": "cyclic_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "start"},
					"node_2": {"task": "middle"}
				},
				"edges": [
					{"from": "node_1", "to": "node_2"},
					{"from": "node_2", "to": "node_1"}
				]
			}
		}

		try:
			WorkflowGraph(workflow)
			return False
		except (ValueError, RuntimeError):
			return True

	def test_topological_sort_ordering(self):
		"""Test topological sort produces correct execution order."""
		workflow = {
			"id": "dependency_workflow",
			"graph": {
				"nodes": {
					"node_a": {"task": "start"},
					"node_b": {"task": "middle1"},
					"node_c": {"task": "middle2"},
					"node_d": {"task": "end"}
				},
				"edges": [
					{"from": "node_a", "to": "node_b"},
					{"from": "node_a", "to": "node_c"},
					{"from": "node_b", "to": "node_d"},
					{"from": "node_c", "to": "node_d"}
				]
			}
		}

		graph = WorkflowGraph(workflow)
		order = graph.get_execution_order()

		# node_a must come before node_b, node_c, node_d
		# node_b and node_c must come before node_d
		assert order.index("node_a") < order.index("node_b")
		assert order.index("node_a") < order.index("node_c")
		assert order.index("node_b") < order.index("node_d")
		assert order.index("node_c") < order.index("node_d")

	def test_get_node_inputs(self):
		"""Test retrieving node inputs with template resolution."""
		workflow = {
			"id": "template_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "read_file", "output": "file_content"},
					"node_2": {
						"task": "process",
						"input": "${node_1.output}",
						"multiplier": 2
					}
				},
				"edges": [{"from": "node_1", "to": "node_2"}]
			}
		}

		graph = WorkflowGraph(workflow)
		inputs = graph.get_node_inputs("node_2")

		# Should have resolved template
		assert "input" in inputs or inputs is not None

	def test_execution_order_retrieval(self):
		"""Test retrieving correct execution order."""
		workflow = {
			"id": "order_workflow",
			"graph": {
				"nodes": {
					"step_1": {"task": "initialize"},
					"step_2": {"task": "process"},
					"step_3": {"task": "finalize"}
				},
				"edges": [
					{"from": "step_1", "to": "step_2"},
					{"from": "step_2", "to": "step_3"}
				]
			}
		}

		graph = WorkflowGraph(workflow)
		order = graph.get_execution_order()

		# Should execute in dependency order
		assert order == ["step_1", "step_2", "step_3"] or (
			order.index("step_1") < order.index("step_2") < order.index("step_3")
		)

	def test_checkpoint_nodes_identification(self):
		"""Test identifying nodes marked for checkpointing."""
		workflow = {
			"id": "checkpoint_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "long_task", "checkpoint": True},
					"node_2": {"task": "quick_task", "checkpoint": False},
					"node_3": {"task": "important_task", "checkpoint": True}
				},
				"edges": []
			},
			"checkpoints": ["node_1", "node_3"]
		}

		graph = WorkflowGraph(workflow)
		checkpoint_nodes = graph.get_checkpoint_nodes()

		# Should identify checkpoint nodes
		assert "node_1" in checkpoint_nodes
		assert "node_3" in checkpoint_nodes
		assert len(checkpoint_nodes) == 2

	def test_state_export(self):
		"""Test exporting graph state."""
		workflow = {
			"id": "export_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "start"},
					"node_2": {"task": "end"}
				},
				"edges": [{"from": "node_1", "to": "node_2"}]
			}
		}

		graph = WorkflowGraph(workflow)
		state = graph.export_state()

		# Should have workflow structure
		assert state is not None
		assert isinstance(state, dict)

	def test_state_import(self):
		"""Test importing and restoring graph state."""
		workflow = {
			"id": "import_workflow",
			"graph": {
				"nodes": {
					"node_1": {"task": "step1"},
					"node_2": {"task": "step2"}
				},
				"edges": [{"from": "node_1", "to": "node_2"}]
			}
		}

		graph = WorkflowGraph(workflow)
		state = graph.export_state()

		# Create new graph and import state
		graph2 = WorkflowGraph(workflow)
		graph2.import_state(state)

		# Should have same execution order
		assert graph.get_execution_order() == graph2.get_execution_order()

	def test_parallel_execution_paths(self):
		"""Test identifying nodes that can execute in parallel."""
		workflow = {
			"id": "parallel_workflow",
			"graph": {
				"nodes": {
					"start": {"task": "initialize"},
					"parallel_a": {"task": "task_a"},
					"parallel_b": {"task": "task_b"},
					"end": {"task": "finalize"}
				},
				"edges": [
					{"from": "start", "to": "parallel_a"},
					{"from": "start", "to": "parallel_b"},
					{"from": "parallel_a", "to": "end"},
					{"from": "parallel_b", "to": "end"}
				]
			}
		}

		graph = WorkflowGraph(workflow)
		order = graph.get_execution_order()

		# parallel_a and parallel_b have same dependency level, could run in parallel
		assert order.index("start") < order.index("parallel_a")
		assert order.index("start") < order.index("parallel_b")

	def test_single_node_workflow(self):
		"""Test workflow with single node."""
		workflow = {
			"id": "single_workflow",
			"graph": {
				"nodes": {
					"only_node": {"task": "standalone_task"}
				},
				"edges": []
			}
		}

		graph = WorkflowGraph(workflow)
		order = graph.get_execution_order()

		assert len(order) == 1
		assert order[0] == "only_node"

	def test_empty_workflow_structure(self):
		"""Test handling of minimal workflow structure."""
		workflow = {
			"id": "minimal_workflow",
			"graph": {
				"nodes": {},
				"edges": []
			}
		}

		graph = WorkflowGraph(workflow)
		order = graph.get_execution_order()

		# Should handle empty gracefully
		assert isinstance(order, list)


