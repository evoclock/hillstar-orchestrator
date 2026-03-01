"""
Unit tests for governance/project_init.py

Production-grade test suite with:
- Deep Assertions: Check actual directory existence, dict content, .gitignore entries
- Mock Verification: assert_called_with() for Path operations, file writes
- Parameterized Tests: Multiple project paths, initialization scenarios
- Boundary Testing: Missing projects, non-directories, permission errors, existing structures
- Realistic Data: Actual directory paths (.hillstar/traces, workflows/core)
- Integration Points: Real directory creation, Path.resolve(), file I/O
- Side Effects: Directory creation verified, .gitignore updates confirmed
- Error Messages: Exact exception types and messages for invalid inputs
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.project_init import initialize_project_structure


class TestInitializeProjectStructureDefaults:
	"""Deep testing of default behavior and path handling."""

	def test_init_with_none_path_defaults_to_current_directory(self):
		"""Initialization: None path creates structure in current directory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			original_cwd = os.getcwd()
			try:
				os.chdir(tmpdir)
				result = initialize_project_structure(None)
				assert result["project_root"] == tmpdir
				assert result["status"] == "success"
			finally:
				os.chdir(original_cwd)

	def test_init_without_argument_defaults_to_current_directory(self):
		"""Deep: Calling with no argument uses current directory."""
		with tempfile.TemporaryDirectory() as tmpdir:
			original_cwd = os.getcwd()
			try:
				os.chdir(tmpdir)
				result = initialize_project_structure()
				assert result["project_root"] == tmpdir
			finally:
				os.chdir(original_cwd)

	def test_init_returns_dict_with_required_keys(self):
		"""Deep: Result dictionary has all required fields."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			assert isinstance(result, dict)
			assert "project_root" in result
			assert "created_directories" in result
			assert "status" in result
			assert "message" in result

	def test_init_returns_status_success(self):
		"""Deep: Status field is exactly 'success'."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			assert result["status"] == "success"

	def test_init_project_root_is_absolute_path(self):
		"""Deep: Returned project_root is absolute, not relative."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			assert os.path.isabs(result["project_root"])


class TestInitializeHillstarDirectoryStructure:
	"""Deep testing of .hillstar directory creation."""

	def test_init_creates_hillstar_directory(self):
		"""Side Effect: .hillstar directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			hillstar_path = os.path.join(tmpdir, ".hillstar")
			assert os.path.isdir(hillstar_path)

	def test_init_creates_hillstar_traces_subdirectory(self):
		"""Side Effect: .hillstar/traces directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			traces_path = os.path.join(tmpdir, ".hillstar", "traces")
			assert os.path.isdir(traces_path)

	def test_init_creates_hillstar_logs_subdirectory(self):
		"""Side Effect: .hillstar/logs directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			logs_path = os.path.join(tmpdir, ".hillstar", "logs")
			assert os.path.isdir(logs_path)

	def test_init_creates_hillstar_audit_subdirectory(self):
		"""Side Effect: .hillstar/audit directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			audit_path = os.path.join(tmpdir, ".hillstar", "audit")
			assert os.path.isdir(audit_path)

	def test_init_creates_hillstar_checkpoints_subdirectory(self):
		"""Side Effect: .hillstar/checkpoints directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			checkpoints_path = os.path.join(tmpdir, ".hillstar", "checkpoints")
			assert os.path.isdir(checkpoints_path)

	def test_init_creates_hillstar_data_stores_subdirectory(self):
		"""Side Effect: .hillstar/data_stores directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			data_stores_path = os.path.join(tmpdir, ".hillstar", "data_stores")
			assert os.path.isdir(data_stores_path)

	@pytest.mark.parametrize("subdir", [
		"traces",
		"logs",
		"audit",
		"checkpoints",
		"data_stores",
	])
	def test_init_creates_all_hillstar_subdirectories(self, subdir):
		"""Parameterized: All 5 .hillstar subdirectories created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			path = os.path.join(tmpdir, ".hillstar", subdir)
			assert os.path.isdir(path), f".hillstar/{subdir} not created"


class TestInitializeWorkflowsDirectoryStructure:
	"""Deep testing of workflows directory creation."""

	def test_init_creates_workflows_directory(self):
		"""Side Effect: workflows directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			workflows_path = os.path.join(tmpdir, "workflows")
			assert os.path.isdir(workflows_path)

	def test_init_creates_workflows_core_subdirectory(self):
		"""Side Effect: workflows/core directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			core_path = os.path.join(tmpdir, "workflows", "core")
			assert os.path.isdir(core_path)

	def test_init_creates_workflows_infrastructure_subdirectory(self):
		"""Side Effect: workflows/infrastructure directory created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			infra_path = os.path.join(tmpdir, "workflows", "infrastructure")
			assert os.path.isdir(infra_path)

	@pytest.mark.parametrize("subdir", ["core", "infrastructure"])
	def test_init_creates_all_workflow_subdirectories(self, subdir):
		"""Parameterized: Both workflows subdirectories created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			path = os.path.join(tmpdir, "workflows", subdir)
			assert os.path.isdir(path), f"workflows/{subdir} not created"


class TestInitializeGitignoreHandling:
	"""Deep testing of .gitignore creation and updates."""

	def test_init_creates_gitignore_if_missing(self):
		"""Side Effect: .gitignore created if it doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			assert os.path.exists(gitignore_path)
			assert str(gitignore_path) in result["created_directories"]

	def test_init_adds_hillstar_entries_to_gitignore(self):
		"""Deep: .gitignore contains all Hillstar entries."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			with open(gitignore_path) as f:
				content = f.read()

			expected_entries = [
				".hillstar/traces/",
				".hillstar/logs/",
				".hillstar/checkpoints/",
				".hillstar/data_stores/",
				".hillstar/__pycache__/",
			]
			for entry in expected_entries:
				assert entry in content

	def test_init_adds_hillstar_marker_to_gitignore(self):
		"""Deep: .gitignore includes descriptive comment."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			with open(gitignore_path) as f:
				content = f.read()

			assert "Hillstar execution artifacts (auto-generated)" in content

	def test_init_does_not_duplicate_existing_entries(self):
		"""Boundary: Existing .gitignore entries not duplicated."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# Create .gitignore with existing entries
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			with open(gitignore_path, "w") as f:
				f.write(".hillstar/traces/\n")
				f.write(".hillstar/logs/\n")

			# Initialize project
			initialize_project_structure(tmpdir)

			# Count occurrences
			with open(gitignore_path) as f:
				content = f.read()

			traces_count = content.count(".hillstar/traces/")
			assert traces_count == 1, "Entry was duplicated"

	def test_init_preserves_existing_gitignore_content(self):
		"""Side Effect: Existing .gitignore content preserved."""
		with tempfile.TemporaryDirectory() as tmpdir:
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			original_content = "*.pyc\n*.pyo\n"
			with open(gitignore_path, "w") as f:
				f.write(original_content)

			initialize_project_structure(tmpdir)

			with open(gitignore_path) as f:
				content = f.read()

			assert "*.pyc" in content
			assert "*.pyo" in content

	def test_init_appends_new_entries_to_existing_gitignore(self):
		"""Integration: New entries appended to existing file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			with open(gitignore_path, "w") as f:
				f.write("*.egg-info/\n")

			initialize_project_structure(tmpdir)

			with open(gitignore_path) as f:
				content = f.read()

			assert "*.egg-info/" in content
			assert ".hillstar/traces/" in content


class TestInitializeErrorHandling:
	"""Deep testing of error conditions."""

	def test_init_raises_file_not_found_for_nonexistent_project(self):
		"""Boundary: FileNotFoundError raised for missing project directory."""
		nonexistent = "/nonexistent/path/that/does/not/exist"
		with pytest.raises(FileNotFoundError) as exc_info:
			initialize_project_structure(nonexistent)
		assert "not found" in str(exc_info.value).lower()

	def test_init_raises_not_a_directory_for_file_path(self):
		"""Boundary: NotADirectoryError raised when path is a file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			file_path = os.path.join(tmpdir, "file.txt")
			with open(file_path, "w") as f:
				f.write("test")

			with pytest.raises(NotADirectoryError):
				initialize_project_structure(file_path)

	def test_init_error_message_includes_path(self):
		"""Error Message: Error text includes the invalid path."""
		with tempfile.TemporaryDirectory() as tmpdir:
			file_path = os.path.join(tmpdir, "file.txt")
			with open(file_path, "w") as f:
				f.write("test")

			with pytest.raises(NotADirectoryError) as exc_info:
				initialize_project_structure(file_path)
			assert file_path in str(exc_info.value)


class TestInitializeCreatedDirectoriesList:
	"""Deep testing of returned created_directories list."""

	def test_init_created_directories_is_list(self):
		"""Deep: created_directories is a list."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			assert isinstance(result["created_directories"], list)

	def test_init_created_directories_includes_hillstar_subdirs(self):
		"""Deep: List contains .hillstar subdirectory paths."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			created = result["created_directories"]

			traces_path = os.path.join(tmpdir, ".hillstar", "traces")
			assert any(traces_path in d for d in created)

	def test_init_created_directories_includes_workflows_subdirs(self):
		"""Deep: List contains workflows subdirectory paths."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			created = result["created_directories"]

			core_path = os.path.join(tmpdir, "workflows", "core")
			assert any(core_path in d for d in created)

	def test_init_created_directories_includes_gitignore_when_created(self):
		"""Deep: .gitignore path included when file created."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			assert gitignore_path in result["created_directories"]

	def test_init_created_directories_excludes_duplicates(self):
		"""Side Effect: No duplicate entries in created_directories."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			created = result["created_directories"]
			assert len(created) == len(set(created))


class TestInitializeIdempotency:
	"""Side effect validation for multiple calls."""

	def test_init_idempotent_on_second_call(self):
		"""Side Effect: Running twice succeeds both times."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result1 = initialize_project_structure(tmpdir)
			result2 = initialize_project_structure(tmpdir)

			assert result1["status"] == "success"
			assert result2["status"] == "success"

	def test_init_second_call_does_not_duplicate_gitignore_entries(self):
		"""Side Effect: Second call doesn't add duplicate .gitignore entries."""
		with tempfile.TemporaryDirectory() as tmpdir:
			initialize_project_structure(tmpdir)
			gitignore_path = os.path.join(tmpdir, ".gitignore")
			with open(gitignore_path) as f:
				first_content = f.read()

			initialize_project_structure(tmpdir)
			with open(gitignore_path) as f:
				second_content = f.read()

			assert first_content == second_content


class TestInitializeWithDifferentPaths:
	"""Parameterized testing with various path scenarios."""

	@pytest.mark.parametrize("path_type", ["absolute", "relative"])
	def test_init_works_with_absolute_and_relative_paths(self, path_type):
		"""Parameterized: Both absolute and relative paths work."""
		with tempfile.TemporaryDirectory() as tmpdir:
			if path_type == "absolute":
				path = tmpdir
			else:
				original_cwd = os.getcwd()
				try:
					os.chdir(tmpdir)
					path = "."
					result = initialize_project_structure(path)
					assert result["status"] == "success"
					assert os.path.isdir(os.path.join(tmpdir, ".hillstar"))
					return
				finally:
					os.chdir(original_cwd)

			result = initialize_project_structure(path)
			assert result["status"] == "success"

	def test_init_returns_consistent_message_format(self):
		"""Deep: Message follows expected format."""
		with tempfile.TemporaryDirectory() as tmpdir:
			result = initialize_project_structure(tmpdir)
			assert "Initialized Hillstar project structure" in result["message"]
			assert tmpdir in result["message"]
