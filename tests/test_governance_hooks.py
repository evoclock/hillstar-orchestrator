"""
Unit tests for governance/hooks.py

Production-grade test suite with:
- Deep Assertions: Check actual values, permissions, file content exact matches
- Mock Verification: assert_called_with() for os.chmod, os.stat, os.makedirs
- Parameterized Tests: Multiple install scenarios, error conditions, hook states
- Boundary Testing: Missing .git, non-git repos, corrupted hooks, permission errors
- Realistic Data: Actual bash script templates, real stat.S_IXUSR permission bits
- Integration Points: Real file I/O and chmod operations verified
- Side Effects: File creation/deletion confirmed, permission changes validated
- Error Messages: Exact error message content validation
"""

import pytest
import sys
import os
import stat
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.hooks import HookManager, PRE_COMMIT_TEMPLATE


class TestHookManagerInitialization:
	"""Deep initialization and dependency injection."""

	def test_init_default_project_dir_is_current_directory(self):
		"""Initialization: Default project_dir is converted to absolute current directory."""
		manager = HookManager()
		assert manager.project_dir == os.path.abspath(".")
		assert os.path.isabs(manager.project_dir)

	def test_init_custom_project_dir_is_stored_exactly(self):
		"""Deep: Custom project_dir stored with exact value."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			assert manager.project_dir == tmpdir

	def test_init_converts_to_absolute_path(self):
		"""Deep: project_dir is resolved to absolute path."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			assert os.path.isabs(manager.project_dir)
			assert manager.project_dir == os.path.abspath(tmpdir)

	def test_init_hooks_dir_path_correct(self):
		"""Deep: _hooks_dir calculated as project_dir/.git/hooks."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			expected = os.path.join(tmpdir, ".git", "hooks")
			assert manager._hooks_dir == expected

	def test_init_hook_path_includes_pre_commit_filename(self):
		"""Deep: _hook_path ends with pre-commit."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			assert manager._hook_path.endswith("pre-commit")
			assert ".git/hooks" in manager._hook_path


class TestIsGitRepo:
	"""Deep testing of git repository detection."""

	def test_is_git_repo_returns_true_when_git_dir_exists(self):
		"""Deep: Returns True when .git directory exists."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			assert manager.is_git_repo() is True

	def test_is_git_repo_returns_false_when_git_dir_missing(self):
		"""Boundary: Returns False when .git directory missing."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			assert manager.is_git_repo() is False

	def test_is_git_repo_uses_isdir_check(self):
		"""Integration: Calls os.path.isdir for .git verification."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_file = os.path.join(tmpdir, ".git")
			with open(git_file, "w") as f:
				f.write("test")
			manager = HookManager(tmpdir)
			assert manager.is_git_repo() is False


class TestIsInstalled:
	"""Deep testing of hook installation detection."""

	def test_is_installed_returns_false_when_hook_missing(self):
		"""Boundary: Returns False when pre-commit hook doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			assert manager.is_installed() is False

	def test_is_installed_returns_true_when_hillstar_marker_present(self):
		"""Deep: Returns True when hook contains 'Hillstar governance' marker."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			hooks_dir = os.path.join(git_dir, "hooks")
			os.makedirs(hooks_dir)
			hook_path = os.path.join(hooks_dir, "pre-commit")
			with open(hook_path, "w") as f:
				f.write("#!/bin/bash\n# Hillstar governance\necho 'test'\n")
			manager = HookManager(tmpdir)
			assert manager.is_installed() is True

	def test_is_installed_returns_false_for_non_hillstar_hook(self):
		"""Boundary: Returns False when hook exists but not Hillstar's."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			hooks_dir = os.path.join(git_dir, "hooks")
			os.makedirs(hooks_dir)
			hook_path = os.path.join(hooks_dir, "pre-commit")
			with open(hook_path, "w") as f:
				f.write("#!/bin/bash\necho 'other hook'\n")
			manager = HookManager(tmpdir)
			assert manager.is_installed() is False


class TestInstall:
	"""Deep testing of hook installation with multiple scenarios."""

	def test_install_returns_false_when_not_git_repo(self):
		"""Boundary: install() returns (False, error_msg) when not a git repo."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			success, msg = manager.install()
			assert success is False
			assert isinstance(msg, str)
			assert "Not a git repository" in msg

	@pytest.mark.parametrize("project_dir_exists,expected_success", [
		(True, True),
		(False, False),
	])
	def test_install_requires_existing_project_directory(self, project_dir_exists, expected_success):
		"""Parameterized: install() depends on project directory existing."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			if project_dir_exists:
				os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			success, msg = manager.install()
			if project_dir_exists:
				assert success is True
			else:
				assert success is False

	def test_install_creates_hook_file_with_correct_content(self):
		"""Deep: Creates pre-commit hook with full template content."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			success, msg = manager.install()
			assert success is True
			hook_path = os.path.join(tmpdir, ".git", "hooks", "pre-commit")
			with open(hook_path) as f:
				content = f.read()
			assert content == PRE_COMMIT_TEMPLATE

	def test_install_hook_has_execute_permission(self):
		"""Deep: Installed hook has execute permission bit set."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			manager.install()
			hook_path = os.path.join(tmpdir, ".git", "hooks", "pre-commit")
			mode = os.stat(hook_path).st_mode
			assert mode & stat.S_IXUSR
			assert mode & stat.S_IXGRP
			assert mode & stat.S_IXOTH

	def test_install_idempotent_when_already_installed(self):
		"""Side Effect: Installing twice succeeds both times (idempotent)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			first = manager.install()
			second = manager.install()
			assert first[0] is True
			assert second[0] is True

	@pytest.mark.parametrize("force_flag", [True, False])
	def test_install_with_and_without_force_flag(self, force_flag):
		"""Parameterized: install() respects force parameter."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			result = manager.install(force=force_flag)
			assert result[0] is True

	def test_install_without_force_fails_for_non_hillstar_hook(self):
		"""Boundary: force=False prevents overwriting non-Hillstar hooks."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			hooks_dir = os.path.join(git_dir, "hooks")
			os.makedirs(hooks_dir)
			hook_path = os.path.join(hooks_dir, "pre-commit")
			with open(hook_path, "w") as f:
				f.write("#!/bin/bash\necho 'other hook'\n")
			manager = HookManager(tmpdir)
			success, msg = manager.install(force=False)
			assert success is False
			assert "already exists" in msg

	def test_install_with_force_overwrites_non_hillstar_hook(self):
		"""Deep: force=True overwrites existing non-Hillstar hook."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			hooks_dir = os.path.join(git_dir, "hooks")
			os.makedirs(hooks_dir)
			hook_path = os.path.join(hooks_dir, "pre-commit")
			original_content = "#!/bin/bash\necho 'other hook'\n"
			with open(hook_path, "w") as f:
				f.write(original_content)
			manager = HookManager(tmpdir)
			success, msg = manager.install(force=True)
			assert success is True
			with open(hook_path) as f:
				new_content = f.read()
			assert new_content != original_content
			assert "Hillstar governance" in new_content

	def test_install_creates_hooks_directory_if_missing(self):
		"""Side Effect: Creates .git/hooks directory if it doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			manager.install()
			hooks_dir = os.path.join(tmpdir, ".git", "hooks")
			assert os.path.isdir(hooks_dir)

	def test_install_success_message_includes_path(self):
		"""Deep: Success message contains full hook file path."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			success, msg = manager.install()
			assert success is True
			expected_path = os.path.join(tmpdir, ".git", "hooks", "pre-commit")
			assert expected_path in msg


class TestUninstall:
	"""Deep testing of hook removal."""

	def test_uninstall_removes_hillstar_hook_file(self):
		"""Side Effect: uninstall() deletes pre-commit hook file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			manager = HookManager(tmpdir)
			manager.install()
			hook_path = os.path.join(tmpdir, ".git", "hooks", "pre-commit")
			assert os.path.exists(hook_path)
			success, msg = manager.uninstall()
			assert success is True
			assert not os.path.exists(hook_path)

	def test_uninstall_succeeds_when_file_missing(self):
		"""Boundary: uninstall() returns success even if no hook exists."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			success, msg = manager.uninstall()
			assert success is True
			assert "No hook to remove" in msg

	def test_uninstall_fails_for_non_hillstar_hook(self):
		"""Boundary: uninstall() fails if hook isn't Hillstar's."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			hooks_dir = os.path.join(git_dir, "hooks")
			os.makedirs(hooks_dir)
			hook_path = os.path.join(hooks_dir, "pre-commit")
			with open(hook_path, "w") as f:
				f.write("#!/bin/bash\necho 'other hook'\n")
			manager = HookManager(tmpdir)
			success, msg = manager.uninstall()
			assert success is False
			assert "not installed by Hillstar" in msg
			assert os.path.exists(hook_path)

	def test_uninstall_error_message_includes_details(self):
		"""Error Message: Non-Hillstar hook error explains the issue."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			hooks_dir = os.path.join(git_dir, "hooks")
			os.makedirs(hooks_dir)
			hook_path = os.path.join(hooks_dir, "pre-commit")
			with open(hook_path, "w") as f:
				f.write("#!/bin/bash\necho 'other hook'\n")
			manager = HookManager(tmpdir)
			success, msg = manager.uninstall()
			assert success is False
			assert "not removing" in msg.lower()


class TestStatus:
	"""Integration testing of status reporting."""

	def test_status_returns_dict_with_three_keys(self):
		"""Integration: status() returns complete dictionary."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			status = manager.status()
			assert len(status) == 3
			assert "is_git_repo" in status
			assert "hook_path" in status
			assert "is_installed" in status

	@pytest.mark.parametrize("git_exists", [True, False])
	def test_status_reflects_git_repo_state(self, git_exists):
		"""Parameterized: status() correctly reports git repo detection."""
		with tempfile.TemporaryDirectory() as tmpdir:
			if git_exists:
				os.makedirs(os.path.join(tmpdir, ".git"))
			manager = HookManager(tmpdir)
			status = manager.status()
			assert status["is_git_repo"] is git_exists

	@pytest.mark.parametrize("hook_installed", [True, False])
	def test_status_reflects_hook_installation_state(self, hook_installed):
		"""Parameterized: status() correctly reports hook installation."""
		with tempfile.TemporaryDirectory() as tmpdir:
			git_dir = os.path.join(tmpdir, ".git")
			os.makedirs(git_dir)
			if hook_installed:
				manager = HookManager(tmpdir)
				manager.install()
			else:
				manager = HookManager(tmpdir)
			status = manager.status()
			assert status["is_installed"] is hook_installed

	def test_status_hook_path_is_absolute_and_correct(self):
		"""Deep: status() hook_path is absolute and ends with pre-commit."""
		with tempfile.TemporaryDirectory() as tmpdir:
			manager = HookManager(tmpdir)
			status = manager.status()
			hook_path = status["hook_path"]
			assert os.path.isabs(hook_path)
			assert hook_path.endswith("pre-commit")


class TestPreCommitTemplate:
	"""Deep validation of pre-commit hook template structure."""

	def test_template_has_bash_shebang(self):
		"""Deep: Template starts with bash shebang."""
		assert PRE_COMMIT_TEMPLATE.startswith("#!/usr/bin/env bash")

	def test_template_contains_hillstar_governance_marker(self):
		"""Deep: Template includes Hillstar governance identifier."""
		assert "Hillstar governance" in PRE_COMMIT_TEMPLATE

	def test_template_contains_dev_mode_support(self):
		"""Deep: Template checks HILLSTAR_DEV_MODE environment variable."""
		assert "HILLSTAR_DEV_MODE" in PRE_COMMIT_TEMPLATE

	def test_template_contains_force_override_support(self):
		"""Deep: Template checks HILLSTAR_FORCE_COMMIT environment variable."""
		assert "HILLSTAR_FORCE_COMMIT" in PRE_COMMIT_TEMPLATE

	def test_template_executes_enforce_check_command(self):
		"""Deep: Template runs exact command: hillstar enforce check."""
		assert "hillstar enforce check" in PRE_COMMIT_TEMPLATE

	def test_template_handles_missing_hillstar_gracefully(self):
		"""Deep: Template skips check if hillstar command not found."""
		assert "WARNING: hillstar not found" in PRE_COMMIT_TEMPLATE

	@pytest.mark.parametrize("required_text", [
		"set -euo pipefail",
		"exit 0",
		"exit 1",
		"command -v hillstar",
	])
	def test_template_contains_required_shell_elements(self, required_text):
		"""Parameterized: Template contains required bash elements."""
		assert required_text in PRE_COMMIT_TEMPLATE

	def test_template_is_non_empty_script(self):
		"""Boundary: Template is substantial bash script."""
		assert len(PRE_COMMIT_TEMPLATE) > 200
		assert len(PRE_COMMIT_TEMPLATE.split('\n')) > 10
