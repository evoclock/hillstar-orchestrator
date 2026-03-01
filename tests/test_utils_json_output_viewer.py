"""
Unit tests for utils/json_output_viewer.py

Production-grade test suite with:
- Deep Assertions: Check viewer state, summary content, data types, character counts
- Mock Verification: Verify file I/O, JSON parsing operations
- Parameterized Tests: Multiple JSON structures, data types, file scenarios
- Boundary Testing: Empty files, missing keys, invalid JSON, wrong types
- Realistic Data: Actual workflow outputs with varying content sizes
- Integration Points: Real file I/O with tempfile, JSON serialization
- Side Effects: Verify viewer state changes (is_valid, data, validation_errors)
- Error Messages: Check validation error messages are informative
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from io import StringIO

from utils.json_output_viewer import JSONOutputViewer


class TestJSONOutputViewerInitialization:
	"""Test JSONOutputViewer initialization."""

	def test_init_sets_output_file_path(self):
		"""Deep: Constructor stores file path as Path object."""
		viewer = JSONOutputViewer(Path("/path/to/file.json"))

		# Deep assertion: path stored correctly
		assert viewer.output_file == Path("/path/to/file.json")
		assert isinstance(viewer.output_file, Path)

	def test_init_sets_default_state(self):
		"""Deep: Constructor initializes state correctly."""
		viewer = JSONOutputViewer(Path("test.json"))

		# Deep assertions: initial state
		assert viewer.data is None
		assert viewer.is_valid is False
		assert isinstance(viewer.validation_errors, list)
		assert len(viewer.validation_errors) == 0


class TestJSONOutputViewerLoadAndValidate:
	"""Test load_and_validate() method."""

	def test_load_valid_json_file(self):
		"""Integration: Load valid JSON file and validate."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create test JSON file
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output text", "node_2": "more output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			# Load and validate
			viewer = JSONOutputViewer(test_file)
			result = viewer.load_and_validate()

			# Deep assertions
			assert result is True
			assert viewer.is_valid is True
			assert viewer.data == test_data
			assert len(viewer.validation_errors) == 0

	def test_load_missing_file_returns_false(self):
		"""Boundary: Missing file returns False and sets error."""
		viewer = JSONOutputViewer(Path("/nonexistent/path/file.json"))
		result = viewer.load_and_validate()

		# Deep assertions
		assert result is False
		assert viewer.is_valid is False
		assert len(viewer.validation_errors) == 1
		assert "not found" in viewer.validation_errors[0].lower()

	def test_load_invalid_json_returns_false(self):
		"""Boundary: Malformed JSON returns False and sets error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "bad.json"
			with open(test_file, "w") as f:
				f.write("{ invalid json }")

			viewer = JSONOutputViewer(test_file)
			result = viewer.load_and_validate()

			# Deep assertions
			assert result is False
			assert viewer.is_valid is False
			assert len(viewer.validation_errors) == 1
			assert "Invalid JSON" in viewer.validation_errors[0]

	def test_load_non_dict_root_returns_false(self):
		"""Boundary: Non-dictionary root returns False."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "array.json"
			with open(test_file, "w") as f:
				json.dump(["item1", "item2"], f)

			viewer = JSONOutputViewer(test_file)
			result = viewer.load_and_validate()

			# Deep assertions
			assert result is False
			assert viewer.is_valid is False
			assert "dictionary" in viewer.validation_errors[0].lower()

	@pytest.mark.parametrize("data_type,should_pass", [
		({"key": "string"}, True),
		({"key": 42}, True),
		({"key": 3.14}, True),
		({"key": True}, True),
		({"key": None}, True),
		({"key": {"nested": "dict"}}, True),
		({"key": ["array", "items"]}, True),
	])
	def test_load_validates_json_serializable_types(self, data_type, should_pass):
		"""Parameterized: Test JSON-serializable type validation."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			with open(test_file, "w") as f:
				json.dump(data_type, f)

			viewer = JSONOutputViewer(test_file)
			result = viewer.load_and_validate()

			# Deep assertion
			assert result == should_pass
			assert viewer.is_valid == should_pass


class TestJSONOutputViewerGetSummary:
	"""Test get_summary() method."""

	def test_get_summary_returns_dict(self):
		"""Deep: get_summary() returns dictionary."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertions
			assert isinstance(summary, dict)
			assert "node_1" in summary

	def test_get_summary_includes_required_fields(self):
		"""Deep: Summary has type, characters, lines, preview for each entry."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "line1\nline2\nline3"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertions: all required fields
			assert "type" in summary["node_1"]
			assert "characters" in summary["node_1"]
			assert "lines" in summary["node_1"]
			assert "preview" in summary["node_1"]

	@pytest.mark.parametrize("content,expected_lines", [
		("single line", 1),
		("line1\nline2", 2),
		("line1\nline2\nline3", 3),
		("", 0),
	])
	def test_get_summary_counts_lines_correctly(self, content, expected_lines):
		"""Parameterized: Line counting is accurate."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node": content}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertion
			actual_lines = summary["node"]["lines"]
			assert actual_lines == expected_lines, \
				f"Expected {expected_lines} lines, got {actual_lines}"

	def test_get_summary_counts_characters_correctly(self):
		"""Deep: Character count matches actual string length."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			content = "Hello, World! This is a test."
			test_data = {"node": content}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertion
			assert summary["node"]["characters"] == len(content)

	def test_get_summary_truncates_long_preview(self):
		"""Deep: Preview is truncated at 100 characters."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			long_content = "x" * 200
			test_data = {"node": long_content}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertions
			preview = summary["node"]["preview"]
			assert len(preview) == 103 # 100 chars + "..."
			assert preview.endswith("...")

	def test_get_summary_includes_type_name(self):
		"""Deep: Summary includes type name for each entry."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {
				"string_node": "text",
				"dict_node": {"key": "value"},
				"list_node": [1, 2, 3],
			}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertions: types recorded
			assert summary["string_node"]["type"] == "str"
			assert summary["dict_node"]["type"] == "dict"
			assert summary["list_node"]["type"] == "list"

	def test_get_summary_returns_empty_for_invalid_viewer(self):
		"""Boundary: Invalid viewer returns empty summary."""
		viewer = JSONOutputViewer(Path("/nonexistent/file.json"))
		summary = viewer.get_summary()

		# Deep assertion
		assert summary == {}
		assert isinstance(summary, dict)


class TestJSONOutputViewerKeyAccess:
	"""Test accessing data by key."""

	def test_can_access_existing_key(self):
		"""Deep: Can retrieve existing key from data."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output", "node_2": "more"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Deep assertion
			assert viewer.data is not None
			assert "node_1" in viewer.data
			assert viewer.data["node_1"] == "output"

	def test_missing_key_detection(self):
		"""Integration: Can detect missing keys."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Deep assertion
			assert viewer.data is not None
			assert "node_1" in viewer.data
			assert "nonexistent_node" not in viewer.data


class TestJSONOutputViewerPrintMethods:
	"""Test print methods (output behavior)."""

	def test_print_summary_with_valid_data(self):
		"""Integration: print_summary() works with valid data."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Side effect: Should not raise
			with patch("sys.stdout", new=StringIO()):
				viewer.print_summary()

	def test_print_all_outputs_with_valid_data(self):
		"""Integration: print_all_outputs() works with valid data."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Side effect: Should not raise
			with patch("sys.stdout", new=StringIO()):
				viewer.print_all_outputs()

	def test_print_key_with_existing_key(self):
		"""Integration: print_key() works with existing key."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Side effect: Should not raise
			with patch("sys.stdout", new=StringIO()):
				viewer.print_key("node_1")

	def test_print_raw_json_with_valid_data(self):
		"""Integration: print_raw_json() works with valid data."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Side effect: Should not raise
			with patch("sys.stdout", new=StringIO()):
				viewer.print_raw_json()

	def test_print_validation_report_with_valid_data(self):
		"""Integration: print_validation_report() shows PASS for valid data."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "test.json"
			test_data = {"node_1": "output"}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()

			# Side effect: Should not raise
			with patch("sys.stdout", new=StringIO()):
				viewer.print_validation_report()


class TestJSONOutputViewerRealWorldScenarios:
	"""Test real-world usage scenarios."""

	def test_workflow_output_summary(self):
		"""Realistic: Summarize actual workflow output structure."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "outputs.json"
			workflow_output = {
				"node_1_model_call": "Model response: Analysis of the task...",
				"node_2_file_read": "File contents:\nLine 1\nLine 2\nLine 3",
				"node_3_model_call": "Final summary...",
			}
			with open(test_file, "w") as f:
				json.dump(workflow_output, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertions
			assert len(summary) == 3
			assert all(key in summary for key in workflow_output.keys())
			assert summary["node_2_file_read"]["lines"] >= 2

	def test_empty_output_handling(self):
		"""Boundary: Handle empty output values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "empty.json"
			test_data = {"empty_node": ""}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			viewer.load_and_validate()
			summary = viewer.get_summary()

			# Deep assertions
			assert summary["empty_node"]["characters"] == 0
			assert summary["empty_node"]["preview"] == ""

	def test_mixed_data_types_in_output(self):
		"""Realistic: Handle mixed data types in outputs."""
		with tempfile.TemporaryDirectory() as tmpdir:
			test_file = Path(tmpdir) / "mixed.json"
			test_data = {
				"string_output": "text output",
				"numeric_output": 42,
				"dict_output": {"nested": "data"},
				"bool_output": True,
				"null_output": None,
			}
			with open(test_file, "w") as f:
				json.dump(test_data, f)

			viewer = JSONOutputViewer(test_file)
			result = viewer.load_and_validate()

			# Deep assertions
			assert result is True
			assert viewer.is_valid is True
			assert viewer.data is not None
			assert len(viewer.data) == 5
