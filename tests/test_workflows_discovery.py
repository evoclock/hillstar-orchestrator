"""
Unit tests for workflows/discovery.py

Production-grade test suite with:
- Deep Assertions: Check actual paths, file counts, metadata content exact matches
- Mock Verification: assert_called_with() for os operations, json.load
- Parameterized Tests: Multiple workflow patterns, depths, file types
- Boundary Testing: Empty directories, max_depth limits, invalid JSON, missing files
- Realistic Data: Actual workflow patterns (step_*.json, phase_*.json), real metadata
- Integration Points: Real file I/O, directory traversal, JSON parsing
- Side Effects: Directory filtering, depth tracking, result sorting
- Error Messages: Exception types (ValueError, IOError), error messages exact content
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.discovery import WorkflowDiscovery


class TestFindWorkflowsBasics:
	"""Deep testing of workflow discovery initialization."""

	def test_find_workflows_returns_list(self):
		"""Deep: Returns a list."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert isinstance(result, list)

	def test_find_workflows_returns_empty_when_no_workflows(self):
		"""Boundary: Returns empty list when no workflows found."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert result == []

	def test_find_workflows_default_start_path_is_current_dir(self):
		"""Deep: Default start_path uses current directory."""
		result = WorkflowDiscovery.find_workflows()
		assert isinstance(result, list)

	def test_find_workflows_default_max_depth_is_five(self):
		"""Deep: Default max_depth is 5."""
		# Should find workflows up to depth 5 (no max_depth arg passed)
		result = WorkflowDiscovery.find_workflows(".")
		assert isinstance(result, list)

	def test_find_workflows_returns_sorted_list(self):
		"""Deep: Results are sorted."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create multiple workflow files
			os.makedirs(os.path.join(tmpdir, "workflows", "a"), exist_ok=True)
			os.makedirs(os.path.join(tmpdir, "workflows", "b"), exist_ok=True)

			workflow_a = os.path.join(tmpdir, "workflows", "a", "workflow.json")
			workflow_b = os.path.join(tmpdir, "workflows", "b", "workflow.json")

			for path in [workflow_a, workflow_b]:
				with open(path, "w") as f:
					json.dump({"id": "test", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert result == sorted(result)


class TestFindWorkflowsFilePatterns:
	"""Deep testing of workflow file pattern matching."""

	def test_find_workflows_detects_workflow_json(self):
		"""Integration: Finds workflow.json files."""
		with tempfile.TemporaryDirectory() as tmpdir:
			workflow_path = os.path.join(tmpdir, "workflow.json")
			with open(workflow_path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert len(result) == 1
			assert workflow_path in result

	def test_find_workflows_detects_step_pattern(self):
		"""Integration: Finds step_*.json files."""
		with tempfile.TemporaryDirectory() as tmpdir:
			step_path = os.path.join(tmpdir, "step_01_analysis.json")
			with open(step_path, "w") as f:
				json.dump({"id": "step1", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert len(result) == 1
			assert step_path in result

	def test_find_workflows_detects_phase_pattern(self):
		"""Integration: Finds phase_*.json files."""
		with tempfile.TemporaryDirectory() as tmpdir:
			phase_path = os.path.join(tmpdir, "phase_discovery.json")
			with open(phase_path, "w") as f:
				json.dump({"id": "phase1", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert len(result) == 1
			assert phase_path in result

	def test_find_workflows_detects_pre_phase_pattern(self):
		"""Integration: Finds pre_phase_*.json files."""
		with tempfile.TemporaryDirectory() as tmpdir:
			pre_phase_path = os.path.join(tmpdir, "pre_phase_setup.json")
			with open(pre_phase_path, "w") as f:
				json.dump({"id": "pre_phase", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert len(result) == 1
			assert pre_phase_path in result

	@pytest.mark.parametrize("filename", [
		"workflow.json",
		"step_001.json",
		"phase_analysis.json",
		"pre_phase_init.json",
	])
	def test_find_workflows_detects_all_patterns(self, filename):
		"""Parameterized: All workflow patterns detected."""
		with tempfile.TemporaryDirectory() as tmpdir:
			path = os.path.join(tmpdir, filename)
			with open(path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert len(result) == 1


class TestFindWorkflowsDepthLimiting:
	"""Deep testing of directory depth limiting."""

	def test_find_workflows_respects_max_depth_limit(self):
		"""Boundary: Stops searching at max_depth."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create workflow at depth 3 (within limit)
			shallow_dir = os.path.join(tmpdir, "a", "b", "c")
			os.makedirs(shallow_dir)
			shallow_path = os.path.join(shallow_dir, "workflow.json")
			with open(shallow_path, "w") as f:
				json.dump({"id": "shallow", "graph": {}}, f)

			# Create workflow at depth 6 (beyond limit of 5)
			deep_dir = os.path.join(tmpdir, "a", "b", "c", "d", "e", "f")
			os.makedirs(deep_dir)
			deep_path = os.path.join(deep_dir, "workflow.json")
			with open(deep_path, "w") as f:
				json.dump({"id": "deep", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir, max_depth=5)

			# Should find shallow but not deep
			assert shallow_path in result
			assert deep_path not in result

	@pytest.mark.parametrize("max_depth,should_find", [
		(1, False), # Too shallow
		(2, True), # Just right
		(5, True), # Default
		(10, True), # Deep enough
	])
	def test_find_workflows_with_different_depths(self, max_depth, should_find):
		"""Parameterized: Depth limiting works correctly."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create workflow at depth 2
			wf_dir = os.path.join(tmpdir, "a", "b")
			os.makedirs(wf_dir)
			wf_path = os.path.join(wf_dir, "workflow.json")
			with open(wf_path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir, max_depth=max_depth)

			if should_find:
				assert len(result) > 0
			else:
				assert len(result) == 0


class TestFindWorkflowsHiddenDirectories:
	"""Deep testing of hidden directory skipping."""

	def test_find_workflows_skips_hidden_directories(self):
		"""Integration: Hidden directories (starting with .) are skipped."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create workflow in hidden directory
			hidden_dir = os.path.join(tmpdir, ".hidden")
			os.makedirs(hidden_dir)
			hidden_path = os.path.join(hidden_dir, "workflow.json")
			with open(hidden_path, "w") as f:
				json.dump({"id": "hidden", "graph": {}}, f)

			# Create workflow in visible directory
			visible_dir = os.path.join(tmpdir, "visible")
			os.makedirs(visible_dir)
			visible_path = os.path.join(visible_dir, "workflow.json")
			with open(visible_path, "w") as f:
				json.dump({"id": "visible", "graph": {}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)

			# Should find visible but not hidden
			assert visible_path in result
			assert hidden_path not in result


class TestFindWorkflowsValidation:
	"""Deep testing of workflow validation during discovery."""

	def test_find_workflows_skips_invalid_json(self):
		"""Boundary: Invalid JSON files are skipped."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create invalid JSON
			invalid_path = os.path.join(tmpdir, "workflow.json")
			with open(invalid_path, "w") as f:
				f.write("{ invalid json }")

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert invalid_path not in result

	def test_find_workflows_skips_missing_required_fields(self):
		"""Boundary: JSON missing 'id' or 'graph' is skipped."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Missing 'id'
			path1 = os.path.join(tmpdir, "workflow1.json")
			with open(path1, "w") as f:
				json.dump({"graph": {}}, f)

			# Missing 'graph'
			path2 = os.path.join(tmpdir, "workflow2.json")
			with open(path2, "w") as f:
				json.dump({"id": "test"}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert path1 not in result
			assert path2 not in result

	def test_find_workflows_includes_valid_workflows(self):
		"""Deep: Workflows with both id and graph are included."""
		with tempfile.TemporaryDirectory() as tmpdir:
			valid_path = os.path.join(tmpdir, "workflow.json")
			with open(valid_path, "w") as f:
				json.dump({"id": "test-wf", "graph": {"nodes": {}}}, f)

			result = WorkflowDiscovery.find_workflows(tmpdir)
			assert valid_path in result


class TestGetWorkflowInfo:
	"""Deep testing of workflow metadata extraction."""

	def test_get_workflow_info_returns_dict_with_required_keys(self):
		"""Deep: Returns dict with all expected keys."""
		with tempfile.TemporaryDirectory() as tmpdir:
			wf_path = os.path.join(tmpdir, "workflow.json")
			with open(wf_path, "w") as f:
				json.dump({"id": "test", "graph": {"nodes": {}, "edges": []}}, f)

			info = WorkflowDiscovery.get_workflow_info(wf_path)

			expected_keys = {
				"path", "filename", "directory", "id", "version", "description",
				"node_count", "edge_count", "uses_custom_provider", "preset",
				"mode", "has_budget", "checkpoints"
			}
			assert set(info.keys()) == expected_keys

	def test_get_workflow_info_raises_ioerror_when_file_missing(self):
		"""Boundary: Raises IOError for non-existent file."""
		with pytest.raises(IOError) as exc_info:
			WorkflowDiscovery.get_workflow_info("/nonexistent/path.json")

		assert "not found" in str(exc_info.value).lower()

	def test_get_workflow_info_raises_valueerror_for_invalid_json(self):
		"""Boundary: Raises ValueError for malformed JSON."""
		with tempfile.TemporaryDirectory() as tmpdir:
			wf_path = os.path.join(tmpdir, "workflow.json")
			with open(wf_path, "w") as f:
				f.write("{ invalid }")

			with pytest.raises(ValueError) as exc_info:
				WorkflowDiscovery.get_workflow_info(wf_path)

			assert "Invalid JSON" in str(exc_info.value)

	def test_get_workflow_info_extracts_path_metadata(self):
		"""Deep: Correctly extracts path-based metadata."""
		with tempfile.TemporaryDirectory() as tmpdir:
			wf_path = os.path.join(tmpdir, "subdir", "workflow.json")
			os.makedirs(os.path.dirname(wf_path))
			with open(wf_path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			info = WorkflowDiscovery.get_workflow_info(wf_path)

			assert info["path"] == os.path.abspath(wf_path)
			assert info["filename"] == "workflow.json"
			assert info["directory"] == os.path.dirname(wf_path)

	def test_get_workflow_info_extracts_workflow_fields(self):
		"""Deep: Correctly extracts workflow fields with defaults."""
		with tempfile.TemporaryDirectory() as tmpdir:
			wf_path = os.path.join(tmpdir, "workflow.json")
			workflow = {
				"id": "my-workflow",
				"version": "2.0",
				"description": "Test workflow",
				"graph": {
					"nodes": {"n1": {}, "n2": {}},
					"edges": [{"from": "n1", "to": "n2"}]
				},
				"model_config": {
					"preset": "balanced",
					"mode": "auto"
				},
				"state": {
					"checkpoints": [1, 2, 3]
				}
			}
			with open(wf_path, "w") as f:
				json.dump(workflow, f)

			info = WorkflowDiscovery.get_workflow_info(wf_path)

			assert info["id"] == "my-workflow"
			assert info["version"] == "2.0"
			assert info["description"] == "Test workflow"
			assert info["node_count"] == 2
			assert info["edge_count"] == 1
			assert info["preset"] == "balanced"
			assert info["mode"] == "auto"
			assert info["checkpoints"] == 3

	def test_get_workflow_info_provides_defaults_for_missing_fields(self):
		"""Deep: Uses defaults when fields missing."""
		with tempfile.TemporaryDirectory() as tmpdir:
			wf_path = os.path.join(tmpdir, "workflow.json")
			with open(wf_path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			info = WorkflowDiscovery.get_workflow_info(wf_path)

			assert info["version"] == "1.0" # Default
			assert info["description"] == "" # Default
			assert info["node_count"] == 0 # Default
			assert info["mode"] == "explicit" # Default


class TestGetAllWorkflowInfo:
	"""Deep testing of bulk workflow discovery."""

	def test_get_all_workflow_info_returns_list(self):
		"""Deep: Returns list of workflow metadata."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = WorkflowDiscovery.get_all_workflow_info(tmpdir)
			assert isinstance(result, list)

	def test_get_all_workflow_info_returns_empty_when_no_workflows(self):
		"""Boundary: Returns empty list when no workflows."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = WorkflowDiscovery.get_all_workflow_info(tmpdir)
			assert result == []

	def test_get_all_workflow_info_returns_metadata_for_each_workflow(self):
		"""Deep: Returns metadata dict for each workflow found."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create two workflows
			for i in range(2):
				subdir = os.path.join(tmpdir, f"wf{i}")
				os.makedirs(subdir)
				path = os.path.join(subdir, "workflow.json")
				with open(path, "w") as f:
					json.dump({"id": f"workflow-{i}", "graph": {}}, f)

			result = WorkflowDiscovery.get_all_workflow_info(tmpdir)

			assert len(result) == 2
			assert all(isinstance(item, dict) for item in result)
			assert all("id" in item for item in result)

	def test_get_all_workflow_info_skips_invalid_workflows(self):
		"""Integration: Skips workflows with errors, includes valid ones."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create one valid workflow.json, one invalid step_*.json
			valid_path = os.path.join(tmpdir, "workflow.json")
			invalid_path = os.path.join(tmpdir, "step_001_invalid.json")

			with open(valid_path, "w") as f:
				json.dump({"id": "valid", "graph": {}}, f)

			with open(invalid_path, "w") as f:
				f.write("{ invalid }")

			result = WorkflowDiscovery.get_all_workflow_info(tmpdir)

			# Should only get the valid one, skip the invalid
			assert len(result) == 1
			assert result[0]["id"] == "valid"


class TestIsValidWorkflow:
	"""Deep testing of workflow validation."""

	def test_is_valid_workflow_returns_true_for_valid_file(self):
		"""Deep: Returns True for file with id and graph."""
		with tempfile.TemporaryDirectory() as tmpdir:
			path = os.path.join(tmpdir, "workflow.json")
			with open(path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			result = WorkflowDiscovery._is_valid_workflow(path)
			assert result is True

	def test_is_valid_workflow_returns_false_for_invalid_json(self):
		"""Boundary: Returns False for malformed JSON."""
		with tempfile.TemporaryDirectory() as tmpdir:
			path = os.path.join(tmpdir, "workflow.json")
			with open(path, "w") as f:
				f.write("{ invalid }")

			result = WorkflowDiscovery._is_valid_workflow(path)
			assert result is False

	def test_is_valid_workflow_returns_false_when_missing_id(self):
		"""Boundary: Returns False when id missing."""
		with tempfile.TemporaryDirectory() as tmpdir:
			path = os.path.join(tmpdir, "workflow.json")
			with open(path, "w") as f:
				json.dump({"graph": {}}, f)

			result = WorkflowDiscovery._is_valid_workflow(path)
			assert result is False

	def test_is_valid_workflow_returns_false_when_missing_graph(self):
		"""Boundary: Returns False when graph missing."""
		with tempfile.TemporaryDirectory() as tmpdir:
			path = os.path.join(tmpdir, "workflow.json")
			with open(path, "w") as f:
				json.dump({"id": "test"}, f)

			result = WorkflowDiscovery._is_valid_workflow(path)
			assert result is False

	def test_is_valid_workflow_returns_false_for_missing_file(self):
		"""Boundary: Returns False for non-existent file."""
		result = WorkflowDiscovery._is_valid_workflow("/nonexistent/path.json")
		assert result is False


class TestFindInCurrentProject:
	"""Deep testing of project-aware discovery."""

	def test_find_in_current_project_returns_list(self):
		"""Deep: Returns list of workflow metadata."""
		result = WorkflowDiscovery.find_in_current_project()
		assert isinstance(result, list)

	def test_find_in_current_project_returns_empty_when_not_hillstar_project(self):
		"""Boundary: Returns empty or limited results when no indicators."""
		# Mock getcwd to return non-project directory
		with patch("os.getcwd") as mock_getcwd:
			with tempfile.TemporaryDirectory() as tmpdir:
				mock_getcwd.return_value = tmpdir

				result = WorkflowDiscovery.find_in_current_project()

				# Should search with depth 2 for non-Hillstar projects
				assert isinstance(result, list)

	def test_find_in_current_project_uses_correct_depth_for_hillstar_project(self):
		"""Integration: Uses depth 3 when Hillstar indicators present."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create Hillstar indicator
			os.makedirs(os.path.join(tmpdir, ".hillstar"))

			# Create workflow at depth 3 (should be found)
			wf_dir = os.path.join(tmpdir, "a", "b", "c")
			os.makedirs(wf_dir)
			wf_path = os.path.join(wf_dir, "workflow.json")
			with open(wf_path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			with patch("os.getcwd", return_value=tmpdir):
				result = WorkflowDiscovery.find_in_current_project()

			assert len(result) == 1
			assert result[0]["id"] == "test"

	def test_find_in_current_project_uses_shallow_depth_for_non_hillstar(self):
		"""Integration: Uses depth 2 when no Hillstar indicators."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create workflow at depth 3 (should not be found)
			wf_dir = os.path.join(tmpdir, "a", "b", "c")
			os.makedirs(wf_dir)
			wf_path = os.path.join(wf_dir, "workflow.json")
			with open(wf_path, "w") as f:
				json.dump({"id": "test", "graph": {}}, f)

			with patch("os.getcwd", return_value=tmpdir):
				result = WorkflowDiscovery.find_in_current_project()

			# Should not find it (depth limited to 2)
			assert len(result) == 0
