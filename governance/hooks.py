"""
Script
------
hooks.py

Path
----
python/hillstar/governance/hooks.py

Purpose
-------
Git hook management: install, remove, and verify pre-commit hooks that
enforce Hillstar workflow execution before allowing commits.

Inputs
------
- project_dir: path to the git repository root

Outputs
-------
- .git/hooks/pre-commit script that calls `hillstar enforce check`

Assumptions
-----------
- Git repository exists at project_dir
- hillstar CLI is on PATH

Parameters
----------
- project_dir: str

Failure Modes
-------------
- .git/hooks/ does not exist: not a git repo
- pre-commit hook already exists: prompts before overwriting

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
"""

from __future__ import annotations

import os
import stat


PRE_COMMIT_TEMPLATE = """\
#!/usr/bin/env bash
# Hillstar governance pre-commit hook
# Auto-installed by: hillstar enforce install
# DO NOT EDIT — managed by Hillstar governance module

set -euo pipefail

# Check if development mode is active
DEV_MODE_FLAG=""
if [[ "${HILLSTAR_DEV_MODE:-0}" == "1" ]]; then
	DEV_MODE_FLAG="--dev"
fi

# Allow bypass with env var
if [[ "${HILLSTAR_FORCE_COMMIT:-0}" == "1" ]]; then
	echo "[hillstar] Force commit override active. Skipping governance check."
	exit 0
fi

# Check if hillstar is available
if ! command -v hillstar &> /dev/null; then
	echo "[hillstar] WARNING: hillstar not found on PATH, skipping governance check."
	exit 0
fi

# Run governance check (with --dev flag if HILLSTAR_DEV_MODE=1)
echo "[hillstar] Checking workflow execution compliance..."
if hillstar enforce check $DEV_MODE_FLAG; then
	echo "[hillstar] Governance check passed."
	exit 0
else
	echo ""
	echo "[hillstar] Commit blocked: no recent Hillstar workflow execution found."
	echo "[hillstar] Run: hillstar execute <workflow.json>"
	echo "[hillstar] Or use development mode: HILLSTAR_DEV_MODE=1 git commit ..."
	exit 1
fi
"""


class HookManager:
	"""Manage git hooks for Hillstar governance enforcement."""

	def __init__(self, project_dir: str = "."):
		self.project_dir = os.path.abspath(project_dir)
		self._hooks_dir = os.path.join(self.project_dir, ".git", "hooks")
		self._hook_path = os.path.join(self._hooks_dir, "pre-commit")

	def is_git_repo(self) -> bool:
		"""Check if project_dir is a git repository."""
		return os.path.isdir(os.path.join(self.project_dir, ".git"))

	def is_installed(self) -> bool:
		"""Check if the Hillstar pre-commit hook is installed."""
		if not os.path.exists(self._hook_path):
			return False
		with open(self._hook_path, encoding="utf-8") as f:
			return "Hillstar governance" in f.read()

	def install(self, force: bool = False) -> tuple[bool, str]:
		"""
		Install the pre-commit hook.

		Args:
			force: Overwrite existing hook without prompting.

		Returns:
			(success, message)
		"""
		if not self.is_git_repo():
			return False, f"Not a git repository: {self.project_dir}"

		if not os.path.isdir(self._hooks_dir):
			os.makedirs(self._hooks_dir, exist_ok=True)

		if os.path.exists(self._hook_path) and not force:
			with open(self._hook_path, encoding="utf-8") as f:
				existing = f.read()
			if "Hillstar governance" in existing:
				return True, "Hook already installed"
			return False, (
				f"A pre-commit hook already exists at {self._hook_path}. "
				"Use --force to overwrite."
			)

		with open(self._hook_path, "w", encoding="utf-8") as f:
			f.write(PRE_COMMIT_TEMPLATE)

		# Make executable
		current = os.stat(self._hook_path).st_mode
		os.chmod(self._hook_path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

		return True, f"Pre-commit hook installed at {self._hook_path}"

	def uninstall(self) -> tuple[bool, str]:
		"""Remove the Hillstar pre-commit hook."""
		if not os.path.exists(self._hook_path):
			return True, "No hook to remove"

		with open(self._hook_path, encoding="utf-8") as f:
			content = f.read()

		if "Hillstar governance" not in content:
			return False, "Existing hook was not installed by Hillstar — not removing"

		os.remove(self._hook_path)
		return True, f"Pre-commit hook removed from {self._hook_path}"

	def status(self) -> dict:
		"""Return hook installation status."""
		return {
			"is_git_repo": self.is_git_repo(),
			"hook_path": self._hook_path,
			"is_installed": self.is_installed(),
		}
