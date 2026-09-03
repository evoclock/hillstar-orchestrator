# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""script_run failure-propagation integration tests.

Verifies that a nonzero script_run exit (or a timeout) produces a typed,
non-empty error and that the runner commit path raises on such results,
preventing downstream node scheduling.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from execution.node_executor import NodeExecutor


def make_executor():
	return NodeExecutor(
		MagicMock(),
		MagicMock(),
		MagicMock(),
		{"anthropic": {"models": ["claude-opus-4-6"]}},
	)


class TestScriptRunPropagation:
	def test_success_returns_all_streams(self):
		executor = make_executor()
		with patch("subprocess.run") as mock_run:
			mock_run.return_value = MagicMock(returncode=0, stdout="out", stderr="err")
			result = executor._execute_script_run(
				"n1", {"tool": "script_run", "parameters": {"script": "true"}}, {}
			)

		assert result == {"output": "out", "error": None, "return_code": 0}

	def test_nonzero_exit_sets_error_even_without_stderr(self):
		executor = make_executor()
		with patch("subprocess.run") as mock_run:
			mock_run.return_value = MagicMock(returncode=3, stdout="", stderr="")
			result = executor._execute_script_run(
				"n1", {"tool": "script_run", "parameters": {"script": "false"}}, {}
			)

		assert result["return_code"] == 3
		assert result["error"] == "script exited with return code 3"

	def test_timeout_is_typed_and_nonempty(self):
		executor = make_executor()
		exc = subprocess.TimeoutExpired(cmd="sleep", timeout=5)
		with patch("subprocess.run", side_effect=exc):
			result = executor._execute_script_run(
				"n1",
				{"tool": "script_run", "parameters": {"script": "sleep 100", "timeout": 5}},
				{},
			)

		assert result["error"] == "script timed out after 5 seconds"
		assert result["error_type"] == "script_timeout"
		assert result["return_code"] is None
		# Non-empty error is essential: the runner commits failure on truthy error.
		assert result["error"]

	def test_runner_commit_raises_on_script_error(self):
		"""A truthy script_run error must raise through the commit path."""
		from execution.runner import WorkflowRunner

		class _Graph:
			node_outputs = {}
			trace = []

		class _Runner:
			graph = _Graph()

		runner = _Runner()
		result = {"output": "", "error": "script exited with return code 1", "return_code": 1}

		with pytest.raises(Exception, match="script exited with return code 1"):
			WorkflowRunner._commit_concurrent_node(
				runner, "n1", {"tool": "script_run"}, result, skipped=False
			)

	def test_runner_commit_succeeds_on_clean_result(self):
		from execution.runner import WorkflowRunner

		class _Graph:
			node_outputs = {}
			trace = []

		class _Runner:
			graph = _Graph()

		runner = _Runner()
		WorkflowRunner._commit_concurrent_node(
			runner, "n1", {"tool": "script_run"}, {"output": "ok"}, skipped=False
		)
		assert _Graph.trace[-1]["status"] == "success"
