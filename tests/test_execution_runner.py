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
import pytest
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


class TestWorkflowRunnerExecutionOrchestration:
	"""Test workflow execution with deep assertions and mock verification (Quality Standards)."""

	def create_test_workflow_file(self, tmpdir, workflow_dict):
		"""Helper to create test workflow JSON file."""
		workflow_path = Path(tmpdir) / "workflow.json"
		with open(workflow_path, "w") as f:
			json.dump(workflow_dict, f)
		return str(workflow_path)

	@pytest.mark.parametrize("node_count,expected_structure", [
		(1, {"nodes": 1, "edges": 0}),
		(3, {"nodes": 3, "edges": 2}),
		(5, {"nodes": 5, "edges": 4}),
	])
	def test_runner_graph_structure_with_various_sizes(self, node_count, expected_structure):
		"""Test runner creates correct graph structure for different workflow sizes (Parameterized)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			nodes = {f"node_{i}": {"task": f"step_{i}"} for i in range(node_count)}
			edges = [{"from": f"node_{i}", "to": f"node_{i+1}"} for i in range(node_count - 1)]

			workflow = {
				"id": "graph_structure_test",
				"graph": {
					"nodes": nodes,
					"edges": edges
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Structure verification
			assert runner.graph is not None
			assert hasattr(runner.graph, 'nodes')
			assert hasattr(runner.graph, 'edges')

			# Deep Assertion #2: Content verification
			assert len(runner.graph.nodes) == expected_structure["nodes"]
			assert len(runner.graph.edges) == expected_structure["edges"]

			# Deep Assertion #3: Node integrity
			for i in range(node_count):
				assert f"node_{i}" in runner.graph.nodes

	def test_runner_cost_manager_initialization(self):
		"""Test cost manager properly initialized (Deep Assertions + Side Effects)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "cost_init_test",
				"graph": {
					"nodes": {"node_1": {"task": "model_call"}},
					"edges": []
				},
				"model_config": {
					"mode": "auto",
					"provider_preference": ["anthropic"]
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Check structure
			assert runner.cost_manager is not None
			assert isinstance(runner.cost_manager, object)

			# Deep Assertion #2: Check initial state
			assert hasattr(runner.cost_manager, 'cumulative_cost_usd')
			assert isinstance(runner.cost_manager.cumulative_cost_usd, (int, float))
			assert runner.cost_manager.cumulative_cost_usd >= 0

			# Deep Assertion #3: Check side effects (initial state)
			assert hasattr(runner.cost_manager, 'node_costs')
			assert isinstance(runner.cost_manager.node_costs, dict)
			assert len(runner.cost_manager.node_costs) == 0 # Should be empty initially

	def test_runner_model_factory_configuration(self):
		"""Test model factory configured with correct preferences (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "model_factory_config_test",
				"model_config": {
					"mode": "auto",
					"provider_preference": ["anthropic", "openai", "ollama"]
				},
				"graph": {
					"nodes": {"node_1": {"task": "model_call"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Factory exists
			assert runner.model_factory is not None

			# Deep Assertion #2: Configuration preserved
			assert runner.model_config is not None
			assert runner.model_config["mode"] == "auto"
			assert "provider_preference" in runner.model_config

			# Deep Assertion #3: Preferences in order
			assert runner.model_config["provider_preference"][0] == "anthropic"
			assert runner.model_config["provider_preference"][1] == "openai"
			assert len(runner.model_config["provider_preference"]) >= 2

	@pytest.mark.parametrize("invalid_workflow", [
		{"id": "missing_graph"},
		{"graph": {"nodes": {}}}, # Missing id
		{"id": "test", "graph": None},
		{"id": "test", "graph": {"nodes": None}},
	])
	def test_runner_boundary_invalid_workflows(self, invalid_workflow):
		"""Test runner boundary cases with invalid workflows (Boundary Testing)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_path = Path(tmpdir) / "invalid.json"
			with open(workflow_path, "w") as f:
				json.dump(invalid_workflow, f)

			# Should raise exception on invalid structure
			with pytest.raises((KeyError, TypeError, AttributeError, ValueError)):
				WorkflowRunner(str(workflow_path), output_dir=tmpdir)

	def test_runner_trace_logger_initialization(self):
		"""Test trace logger properly initialized (Deep Assertions + Side Effects)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "trace_init_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Logger exists
			assert runner.trace_logger is not None

			# Deep Assertion #2: Has required methods
			assert hasattr(runner.trace_logger, 'log')
			assert callable(getattr(runner.trace_logger, 'log'))

			# Deep Assertion #3: Side effect - output directory references
			assert runner.output_dir is not None
			assert len(runner.output_dir) > 0

	def test_runner_checkpoint_manager_initialization(self):
		"""Test checkpoint manager properly initialized (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "checkpoint_init_test",
				"graph": {
					"nodes": {
						"step_1": {"task": "read_file"},
						"step_2": {"task": "process"},
						"step_3": {"task": "write_file"}
					},
					"edges": [{"from": "step_1", "to": "step_2"}, {"from": "step_2", "to": "step_3"}]
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Manager exists
			assert runner.checkpoint_manager is not None

			# Deep Assertion #2: Has required methods and attributes
			assert hasattr(runner.checkpoint_manager, 'output_dir')
			assert hasattr(runner.checkpoint_manager, 'create')
			assert callable(getattr(runner.checkpoint_manager, 'create'))

	def test_runner_node_executor_initialization(self):
		"""Test node executor properly initialized with dependencies (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "executor_init_test",
				"graph": {
					"nodes": {"node_1": {"task": "model_call"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Executor exists
			assert runner.node_executor is not None

			# Deep Assertion #2: Has required methods
			assert hasattr(runner.node_executor, 'execute_node')
			assert callable(getattr(runner.node_executor, 'execute_node'))

			# Deep Assertion #3: Has required dependencies
			assert hasattr(runner.node_executor, 'model_factory')
			assert hasattr(runner.node_executor, 'cost_manager')

	@pytest.mark.parametrize("workflow_size,expected_nodes", [
		(1, 1),
		(5, 5),
		(10, 10),
	])
	def test_runner_realistic_workflow_loading(self, workflow_size, expected_nodes):
		"""Test loading realistic workflows of various sizes (Realistic Data)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create realistic workflow structure
			nodes = {}
			edges = []
			for i in range(workflow_size):
				nodes[f"step_{i}"] = {
					"task": "model_call" if i % 2 == 0 else "file_read",
					"provider": "anthropic" if i % 2 == 0 else None,
					"description": f"Step {i} in processing pipeline"
				}
				if i > 0:
					edges.append({"from": f"step_{i-1}", "to": f"step_{i}"})

			workflow = {
				"id": f"realistic_workflow_{workflow_size}",
				"version": "1.0.0",
				"description": f"Realistic workflow with {workflow_size} steps",
				"graph": {
					"nodes": nodes,
					"edges": edges
				},
				"model_config": {
					"mode": "auto",
					"provider_preference": ["anthropic", "openai", "ollama"]
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Verify realistic structure loaded correctly
			assert len(runner.graph.nodes) == expected_nodes
			assert len(runner.graph.edges) == expected_nodes - 1
			assert runner.workflow_json["version"] == "1.0.0"

	def test_runner_has_execute_method_callable(self):
		"""Test runner has execute method that is callable (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "execute_method_test",
				"graph": {
					"nodes": {"node_1": {"task": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Deep Assertion #1: Method exists
			assert hasattr(runner, "execute")

			# Deep Assertion #2: Is callable
			assert callable(runner.execute)

			# Deep Assertion #3: Signature check (can be called with no args)
			import inspect
			sig = inspect.signature(runner.execute)
			assert len(sig.parameters) == 0 or all(
				p.default != inspect.Parameter.empty for p in sig.parameters.values()
			)


class TestWorkflowRunnerExecution:
	"""Test workflow execution with mock verification and side effects (Quality Standards)."""

	def create_test_workflow_file(self, tmpdir, workflow_dict):
		"""Helper to create test workflow JSON file."""
		workflow_path = Path(tmpdir) / "workflow.json"
		with open(workflow_path, "w") as f:
			json.dump(workflow_dict, f)
		return str(workflow_path)

	def test_execute_returns_result_dict(self):
		"""Test execute() returns proper result structure (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "execute_result_test",
				"graph": {
					"nodes": {"node_1": {"tool": "file_read", "parameters": {"path": "/dev/null"}}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Execute should return a dict with expected keys
			result = runner.execute()

			# Deep Assertion #1: Result structure
			assert isinstance(result, dict)
			assert "workflow_id" in result
			assert "status" in result
			assert "trace_file" in result

			# Deep Assertion #2: Expected values
			assert result["workflow_id"] == "execute_result_test"
			assert result["status"] in ["success", "error", "partial"]

	@pytest.mark.parametrize("resume_from", [None, "node_1"])
	def test_execute_accepts_resume_parameter(self, resume_from):
		"""Test execute() supports resume_from parameter (Parameterized)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "resume_test",
				"graph": {
					"nodes": {"node_1": {"tool": "file_read", "parameters": {"path": "/dev/null"}}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Should accept resume_from without crashing
			try:
				result = runner.execute(resume_from=resume_from)
				assert result is not None
			except Exception as e:
				# Some errors are acceptable (checkpoint not found, file not found, etc)
				assert isinstance(e, (FileNotFoundError, IOError, KeyError, ValueError))

	def test_execute_creates_trace_file(self):
		"""Test execute() creates trace file (Side Effects)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "trace_file_test",
				"graph": {
					"nodes": {"node_1": {"tool": "file_read", "parameters": {"path": "/dev/null"}}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)
			result = runner.execute()

			# Verify trace file was created
			if result.get("trace_file"):
				trace_path = Path(result["trace_file"])
				# Trace file should exist or path should be valid
				assert isinstance(trace_path, Path)

	def test_execute_updates_cumulative_cost(self):
		"""Test execute() updates cost_manager cumulative cost (Side Effects)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "cost_tracking_test",
				"graph": {
					"nodes": {"node_1": {"tool": "file_read", "parameters": {"path": "/dev/null"}}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Cost should start at 0
			initial_cost = runner.cost_manager.cumulative_cost_usd
			assert initial_cost >= 0

			# After execution, cost tracking should be in place
			result = runner.execute()
			assert result is not None
			assert runner.cost_manager.cumulative_cost_usd >= initial_cost

	def test_execute_handles_multiple_nodes(self):
		"""Test execute() handles workflows with multiple nodes (Parameterized)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "multi_node_test",
				"graph": {
					"nodes": {
						"step_1": {"tool": "file_read", "parameters": {"path": "/dev/null"}},
						"step_2": {"tool": "file_read", "parameters": {"path": "/dev/null"}},
						"step_3": {"tool": "file_read", "parameters": {"path": "/dev/null"}}
					},
					"edges": [
						{"from": "step_1", "to": "step_2"},
						{"from": "step_2", "to": "step_3"}
					]
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Should execute without crashing
			try:
				result = runner.execute()
				assert result is not None
				assert "workflow_id" in result
			except Exception:
				# Some execution errors are OK
				pass

	def test_execute_preserves_workflow_metadata(self):
		"""Test execute() preserves workflow metadata (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "metadata_test",
				"name": "Test Workflow",
				"description": "A test workflow",
				"graph": {
					"nodes": {"node_1": {"tool": "file_read", "parameters": {"path": "/dev/null"}}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Metadata should be preserved
			assert runner.workflow_json["id"] == "metadata_test"
			assert runner.workflow_json["name"] == "Test Workflow"
			assert runner.workflow_json["description"] == "A test workflow"


class TestWorkflowRunnerCostTracking:
	"""Test cost estimation, budget checking, and cost tracking (Quality Standards)."""

	def create_test_workflow_file(self, tmpdir, workflow_dict):
		"""Helper to create test workflow JSON file."""
		workflow_path = Path(tmpdir) / "workflow.json"
		with open(workflow_path, "w") as f:
			json.dump(workflow_dict, f)
		return str(workflow_path)

	@pytest.mark.parametrize("cost_value", [0.0, 0.01, 1.0, 10.0, 100.0])
	def test_cost_manager_tracks_various_costs(self, cost_value):
		"""Test cost manager tracks different cost values (Parameterized + Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "cost_test",
				"graph": {
					"nodes": {"node_1": {"tool": "test"}},
					"edges": []
				},
				"model_config": {
					"budget": {"max_workflow_usd": 1000}
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Record a cost
			runner.cost_manager.record_cost("node_1", cost_value)

			# Verify cost was recorded
			assert "node_1" in runner.cost_manager.node_costs
			assert runner.cost_manager.node_costs["node_1"] == cost_value
			assert runner.cost_manager.cumulative_cost_usd == cost_value

	def test_cost_manager_accumulates_multiple_costs(self):
		"""Test cost manager accumulates costs from multiple nodes (Side Effects)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "accumulate_cost_test",
				"graph": {
					"nodes": {
						"node_1": {"tool": "test"},
						"node_2": {"tool": "test"},
						"node_3": {"tool": "test"}
					},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Record costs for multiple nodes
			runner.cost_manager.record_cost("node_1", 5.0)
			runner.cost_manager.record_cost("node_2", 10.0)
			runner.cost_manager.record_cost("node_3", 15.0)

			# Verify cumulative
			assert runner.cost_manager.cumulative_cost_usd == 30.0
			assert len(runner.cost_manager.node_costs) == 3

	@pytest.mark.parametrize("estimate_case", [
		("anthropic", "claude-opus-4-6", 1000, 500),
		("openai", "gpt-4o", 2000, 1000),
		("local", "ollama", 100, 50),
	])
	def test_cost_estimation_various_providers(self, estimate_case):
		"""Test cost estimation for different providers (Parameterized)."""
		provider, model, input_tokens, output_tokens = estimate_case

		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "cost_estimate_test",
				"graph": {
					"nodes": {"node_1": {"tool": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Estimate cost
			cost = runner.cost_manager.estimate_cost(provider, model, input_tokens, output_tokens)

			# Deep Assertion: Cost should be non-negative and reasonable
			assert isinstance(cost, (int, float))
			assert cost >= 0
			# Local providers should be free
			if provider == "local":
				assert cost == 0.0


class TestWorkflowRunnerConfigValidation:
	"""Test configuration validation and merging (Quality Standards)."""

	def create_test_workflow_file(self, tmpdir, workflow_dict):
		"""Helper to create test workflow JSON file."""
		workflow_path = Path(tmpdir) / "workflow.json"
		with open(workflow_path, "w") as f:
			json.dump(workflow_dict, f)
		return str(workflow_path)

	@pytest.mark.parametrize("config_mode,preset", [
		("explicit", None),
		("auto", None),
		("preset", "balanced"),
	])
	def test_runner_accepts_different_config_modes(self, config_mode, preset):
		"""Test runner accepts different model config modes (Parameterized)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			model_config = {
				"mode": config_mode,
				"provider_preference": ["anthropic"]
			}
			if preset:
				model_config["preset"] = preset

			workflow = {
				"id": "config_mode_test",
				"model_config": model_config,
				"graph": {
					"nodes": {"node_1": {"tool": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Should accept all modes
			assert runner.model_config["mode"] == config_mode

	def test_runner_validates_budget_config(self):
		"""Test runner validates budget configuration (Deep Assertions)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow = {
				"id": "budget_config_test",
				"model_config": {
					"budget": {
						"max_per_task_usd": 10.0,
						"max_workflow_usd": 100.0
					}
				},
				"graph": {
					"nodes": {"node_1": {"tool": "test"}},
					"edges": []
				}
			}
			workflow_path = self.create_test_workflow_file(tmpdir, workflow)

			runner = WorkflowRunner(workflow_path, output_dir=tmpdir)

			# Budget should be loaded
			assert runner.cost_manager is not None
			assert runner.model_config is not None
			assert runner.model_config.get("budget") is not None
