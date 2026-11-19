# SPDX-FileCopyrightText: 2026 Julen Gamboa
# SPDX-License-Identifier: AGPL-3.0-only
"""Timeout cleanup must include descendants of script_run shells."""

import os
import signal
import time

import pytest

from unittest.mock import MagicMock

from execution.node_executor import NodeExecutor


def make_executor():
	return NodeExecutor(MagicMock(), MagicMock(), {})


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
@pytest.mark.parametrize("ignore_term", [False, True])
def test_timeout_kills_grandchild(tmp_path, ignore_term):
	pid_file = tmp_path / "child.pid"
	child = "sh -c 'trap \"\" TERM; exec sleep 300'" if ignore_term else "sleep 300"
	script = f"{child} & echo $! > child.pid; wait"
	pid = None
	try:
		result = make_executor()._execute_script_run(
			"node", {"tool": "script_run", "parameters": {"script": script},
			"cwd": str(tmp_path), "timeout": 1, "timeout_grace": 1}, {}
		)
		assert result == {
			"output": "", "error": "script timed out after 1 seconds",
			"error_type": "script_timeout", "return_code": None,
		}
		pid = int(pid_file.read_text())
		deadline = time.monotonic() + 3
		while time.monotonic() < deadline:
			try:
				os.kill(pid, 0)
			except ProcessLookupError:
				break
			time.sleep(0.05)
		else:
			pytest.fail("script grandchild survived timeout")
	finally:
		if pid is None and pid_file.exists():
			pid = int(pid_file.read_text())
		if pid is not None:
			try:
				os.kill(pid, signal.SIGKILL)
			except ProcessLookupError:
				pass
