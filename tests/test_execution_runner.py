#!/usr/bin/env python3
"""
Design test for execution/runner.py

Tests the WorkflowRunner for:
- Workflow loading and initialization
- Configuration validation and merging
- Component initialization (cost, config, model, node execution)
- Main execution orchestration
"""

import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, '..')

from execution.runner import WorkflowRunner


class TestWorkflowRunnerDesign:
	"""Design test suite for WorkflowRunner."""

	def create_test_workflow_file(self, tmpdir, workflow_dict):
		"""Helper to create test workflow JSON file."""
		workflow_path = Path(tmpdir) / "workflow.json"
		with open(workflow_path, "w") as f:
			json.dump(workflow_dict, f)
		return str(workflow_path)

	def test_runner_initialization(self):
		"""Test WorkflowRunner initializes with workflow."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "test_workflow",
				"graph": {
					"nodes": {
						"node_1": {"task": "read_file"}
					},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			assert runner is not None

	def test_runner_loads_workflow_json(self):
		"""Test runner loads workflow from file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "load_test",
				"graph": {
					"nodes": {
						"step_1": {"task": "process"},
						"step_2": {"task": "finalize"}
					},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Workflow JSON should be loaded
			assert runner.workflow_json is not None
			assert runner.workflow_json["id"] == "load_test"

	def test_runner_creates_output_directories(self):
		"""Test runner creates output directory structure."""
		with tempfile.TemporaryDirectory() as tmpdir:
			output_dir = Path(tmpdir) / "output"
			workflow = {
				"id": "output_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			WorkflowRunner(workflow_path, output_dir=str(output_dir))
			# Output directory should exist
			assert output_dir.exists()

	def test_runner_initializes_trace_logger(self):
		"""Test runner initializes trace logging."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "trace_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			assert runner.trace_logger is not None

	def test_runner_initializes_checkpoint_manager(self):
		"""Test runner initializes checkpoint management."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "checkpoint_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			assert runner.checkpoint_manager is not None

	def test_runner_has_cost_manager(self):
		"""Test runner has cost tracking."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "cost_test",
				"graph": {
					"nodes": {"node_1": {"task": "model_call"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Runner should have cost manager
			assert runner.cost_manager is not None

	def test_runner_validates_model_config(self):
		"""Test runner validates model configuration."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "config_test",
				"model_config": {
					"mode": "auto",
					"provider_preference": ["anthropic"]
				},
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Should validate config without error
			assert runner.model_config is not None

	def test_runner_initializes_graph(self):
		"""Test runner creates workflow graph."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "graph_test",
				"graph": {
					"nodes": {
						"node_1": {"task": "start"},
						"node_2": {"task": "end"}
					},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Should have workflow graph
			assert runner.graph is not None

	def test_runner_has_model_factory(self):
		"""Test runner has model factory for model selection."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "model_factory_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Should have model factory
			assert runner.model_factory is not None

	def test_runner_has_node_executor(self):
		"""Test runner has node executor."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "executor_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Should have node executor
			assert runner.node_executor is not None

	def test_runner_has_execute_method(self):
		"""Test runner has execute method."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "execute_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Should have execute method
			assert hasattr(runner, "execute")
			assert callable(runner.execute)

	def test_runner_supports_model_selection(self):
		"""Test runner supports model selection."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "model_selection_test",
				"model_config": {
					"mode": "auto",
					"provider_preference": ["anthropic", "openai", "ollama"]
				},
				"graph": {
					"nodes": {
						"node_1": {
							"task": "model_call",
							"task_type": "complex"
						}
					},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			# Should have model factory and config
			assert runner.model_factory is not None
			assert runner.model_config is not None

	def test_runner_stores_workflow_path(self):
		"""Test runner stores workflow path for reference."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "path_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			assert runner.workflow_path == workflow_path

	def test_runner_stores_output_dir(self):
		"""Test runner stores output directory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "output_dir_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			assert runner.output_dir == tmpdir


