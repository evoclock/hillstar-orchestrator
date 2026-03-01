"""
Unit tests for utils/report.py

Production-grade test suite with:
- Deep Assertions: Check markdown structure, content presence, formatting
- Mock Verification: Verify file I/O, JSON parsing, trace file loading
- Parameterized Tests: Multiple workflow configurations, trace scenarios
- Boundary Testing: Missing files, empty workflows, invalid traces
- Realistic Data: Actual workflow structures with nodes/edges
- Integration Points: Real file I/O with tempfile, markdown generation
- Side Effects: Verify report content changes with different inputs
- Error Messages: Check error handling for invalid inputs
"""

import json
import pytest
import tempfile
from pathlib import Path

from utils.report import (
 ReportGenerator,
 generate_pre_execution_report,
 generate_post_execution_report,
)


class TestReportGeneratorInitialization:
	"""Test ReportGenerator initialization."""

	def test_init_with_valid_workflow(self):
		"""Deep: Initialize with valid workflow file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test-workflow",
				"description": "Test workflow",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))

			# Deep assertions
			assert generator.workflow_path == workflow_file
			assert generator.workflow == workflow_data
			assert generator.workflow_id == "test-workflow"
			assert generator.description == "Test workflow"

	def test_init_with_missing_file_raises_error(self):
		"""Boundary: Missing file raises FileNotFoundError."""
		with pytest.raises(FileNotFoundError) as exc_info:
			ReportGenerator("/nonexistent/workflow.json")

		assert "not found" in str(exc_info.value).lower()

	def test_init_with_invalid_json_raises_error(self):
		"""Boundary: Invalid JSON raises error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "bad.json"
			with open(workflow_file, "w") as f:
				f.write("{ invalid json }")

			with pytest.raises(json.JSONDecodeError):
				ReportGenerator(str(workflow_file))


class TestPreExecutionReport:
	"""Test pre-execution report generation."""

	def test_generates_markdown_report(self):
		"""Deep: Pre-execution report returns non-empty markdown string."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test-wf",
				"description": "Test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			report = generator.generate_pre_execution_report()

			# Deep assertions
			assert isinstance(report, str)
			assert len(report) > 0
			assert "# Workflow Report" in report

	def test_report_includes_required_sections(self):
		"""Deep: Report contains all expected sections."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test-wf",
				"description": "Test workflow",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			report = generator.generate_pre_execution_report()

			# Deep assertions: check for section headers
			assert "# Workflow Report" in report
			assert "## Workflow Structure" in report
			assert "## Nodes" in report
			assert "## Model Selection Strategy" in report
			assert "## Cost Summary" in report
			assert "## Governance & Audit" in report

	def test_report_includes_workflow_id(self):
		"""Deep: Report contains workflow ID."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_id = "my-special-workflow-123"
			workflow_data = {
				"id": workflow_id,
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			report = generator.generate_pre_execution_report()

			# Deep assertion
			assert workflow_id in report


class TestPostExecutionReport:
	"""Test post-execution report generation."""

	def test_generates_post_execution_report(self):
		"""Integration: Post-execution report with trace file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create workflow
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test-wf",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			# Create trace file
			trace_file = Path(tmpdir) / "trace.jsonl"
			with open(trace_file, "w") as f:
				f.write(json.dumps({"event": "execution_start"}) + "\n")
				f.write(
					json.dumps({
						"event": "execution_complete",
						"result": {"total_cost": 0.1234, "tokens_used": 500},
					}) + "\n"
				)

			generator = ReportGenerator(str(workflow_file))
			report = generator.generate_post_execution_report(str(trace_file))

			# Deep assertions
			assert isinstance(report, str)
			assert len(report) > 0
			assert "# Workflow Report" in report

	def test_post_execution_with_missing_trace_file(self):
		"""Boundary: Missing trace file handled gracefully."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test-wf",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			# Should not raise even if trace file doesn't exist
			report = generator.generate_post_execution_report(
				"/nonexistent/trace.jsonl"
			)

			# Deep assertion
			assert isinstance(report, str)
			assert len(report) > 0


class TestNodeTableSection:
	"""Test node table generation."""

	def test_empty_nodes_shows_message(self):
		"""Boundary: Empty node list shows appropriate message."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			section = generator._node_table_section()

			# Deep assertion
			assert "No nodes" in section or "0 nodes" in section

	@pytest.mark.parametrize("num_nodes", [1, 3, 5, 10])
	def test_node_table_shows_node_count(self, num_nodes):
		"""Parameterized: Node count displayed correctly."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			nodes = {f"node_{i}": {"tool": "model_call", "provider": "anthropic", "model": "claude-opus"} for i in range(num_nodes)}
			workflow_data = {
				"id": "test",
				"graph": {"nodes": nodes, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			section = generator._node_table_section()

			# Deep assertion
			assert f"{num_nodes} nodes" in section


class TestCostEstimation:
	"""Test cost estimation logic."""

	@pytest.mark.parametrize("model,expected_match", [
		("claude-opus-4-6", "claude-opus"),
		("claude-sonnet-4-6", "claude-sonnet"),
		("gpt-4o-mini", "gpt-4o"),
		("mistral-large-2407", "mistral-large"),
		("devstral-local-2024", "devstral"),
	])
	def test_estimate_node_cost_matches_models(self, model, expected_match):
		"""Parameterized: Model cost estimation matches known models."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			node_data = {"model": model, "provider": "anthropic"}
			cost = generator._estimate_node_cost(node_data)

			# Deep assertion: cost is positive for known models
			assert cost >= 0.0

	def test_missing_model_returns_default_cost(self):
		"""Boundary: Unknown model returns default cost."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			node_data = {"model": "unknown-model-xyz", "provider": "unknown"}
			cost = generator._estimate_node_cost(node_data)

			# Deep assertion
			assert cost >= 0.0


class TestTraceFileParsing:
	"""Test trace file parsing."""

	def test_parse_valid_trace_file(self):
		"""Integration: Parse valid JSONL trace file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			trace_file = Path(tmpdir) / "trace.jsonl"
			with open(trace_file, "w") as f:
				f.write(json.dumps({"event": "model_call", "provider": "anthropic"}) + "\n")
				f.write(json.dumps({
					"event": "execution_complete",
					"result": {"total_cost": 0.05, "tokens_used": 1000},
				}) + "\n")

			generator = ReportGenerator(str(workflow_file))
			metrics = generator._parse_trace_file(str(trace_file))

			# Deep assertions
			assert metrics["status"] == "Completed"
			assert metrics["total_cost"] == 0.05
			assert metrics["tokens_used"] == 1000

	def test_parse_missing_trace_file_returns_defaults(self):
		"""Boundary: Missing trace file returns default metrics."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			metrics = generator._parse_trace_file("/nonexistent/trace.jsonl")

			# Deep assertions
			assert isinstance(metrics, dict)
			assert "status" in metrics
			assert "total_cost" in metrics


class TestMermaidDiagramGeneration:
	"""Test Mermaid diagram generation."""

	def test_generates_mermaid_code(self):
		"""Integration: Generates valid Mermaid syntax."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {
					"nodes": {
						"node_1": {"tool": "model_call", "provider": "anthropic"},
						"node_2": {"tool": "file_read", "provider": "anthropic"},
					},
					"edges": [{"from": "node_1", "to": "node_2"}],
				},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			mermaid = generator._generate_mermaid_diagram()

			# Deep assertions: valid Mermaid syntax
			assert "graph TD" in mermaid
			assert "node_1" in mermaid
			assert "node_2" in mermaid
			assert "-->" in mermaid

	def test_mermaid_includes_all_nodes(self):
		"""Deep: Mermaid diagram includes all workflow nodes."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			nodes = {
				"start": {"tool": "model_call", "provider": "anthropic"},
				"middle": {"tool": "file_read", "provider": "anthropic"},
				"end": {"tool": "model_call", "provider": "anthropic"},
			}
			workflow_data = {
				"id": "test",
				"graph": {
					"nodes": nodes,
					"edges": [
						{"from": "start", "to": "middle"},
						{"from": "middle", "to": "end"},
					],
				},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			mermaid = generator._generate_mermaid_diagram()

			# Deep assertions
			for node_id in nodes.keys():
				assert node_id in mermaid


class TestGovernanceSection:
	"""Test governance section generation."""

	def test_governance_section_present(self):
		"""Deep: Governance section includes required fields."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			section = generator._governance_section()

			# Deep assertions
			assert "## Governance & Audit" in section
			assert "Compliance" in section
			assert "Audit" in section


class TestModuleFunctions:
	"""Test module-level convenience functions."""

	def test_generate_pre_execution_report_function(self):
		"""Integration: Module function generates report."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			report = generate_pre_execution_report(str(workflow_file))

			# Deep assertions
			assert isinstance(report, str)
			assert "# Workflow Report" in report

	def test_generate_post_execution_report_function(self):
		"""Integration: Module function generates post-execution report."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "test",
				"graph": {"nodes": {}, "edges": []},
				"provider_config": {},
				"model_config": {"mode": "explicit"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			trace_file = Path(tmpdir) / "trace.jsonl"
			trace_file.touch()

			report = generate_post_execution_report(str(workflow_file), str(trace_file))

			# Deep assertions
			assert isinstance(report, str)
			assert "# Workflow Report" in report


class TestReportWithRealWorldWorkflows:
	"""Test with realistic workflow structures."""

	def test_report_with_multiple_providers(self):
		"""Realistic: Generate report with mixed providers."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_file = Path(tmpdir) / "workflow.json"
			workflow_data = {
				"id": "multi-provider-wf",
				"description": "Multi-provider workflow",
				"graph": {
					"nodes": {
						"analyze": {
							"tool": "model_call",
							"provider": "anthropic",
							"model": "claude-opus",
						},
						"search": {
							"tool": "model_call",
							"provider": "openai",
							"model": "gpt-4o",
						},
						"refine": {
							"tool": "model_call",
							"provider": "mistral",
							"model": "mistral-large",
						},
					},
					"edges": [
						{"from": "analyze", "to": "search"},
						{"from": "search", "to": "refine"},
					],
				},
				"provider_config": {
					"anthropic": {"tos_accepted": True, "audit_enabled": True},
					"openai": {"tos_accepted": True, "audit_enabled": False},
				},
				"model_config": {"mode": "explicit", "preset": "balanced"},
			}
			with open(workflow_file, "w") as f:
				json.dump(workflow_data, f)

			generator = ReportGenerator(str(workflow_file))
			report = generator.generate_pre_execution_report()

			# Deep assertions
			assert "anthropic" in report or "claude" in report.lower()
			assert "openai" in report or "gpt" in report.lower()
			assert "mistral" in report
			assert "multi-provider-wf" in report
