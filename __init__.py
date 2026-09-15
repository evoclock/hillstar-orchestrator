# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-only

"""Hillstar Orchestrator."""

from execution.runner import WorkflowRunner
from execution.graph import WorkflowGraph
from execution.trace import TraceLogger
from execution.checkpoint import CheckpointManager
from governance.enforcer import GovernanceEnforcer
from governance.hooks import HookManager
from governance.policy import GovernancePolicy

import tomllib
from pathlib import Path

try:
	__version__ = tomllib.loads(
		(Path(__file__).resolve().parent / "pyproject.toml").read_text()
	)["project"]["version"]
except Exception:
	try:
		from importlib.metadata import version as _v
		__version__ = _v("hillstar-orchestrator")
	except Exception:
		__version__ = "0.0.0"
__author__ = "Julen Gamboa"

__all__ = [
	"WorkflowRunner",
	"WorkflowGraph",
	"TraceLogger",
	"CheckpointManager",
	"GovernanceEnforcer",
	"HookManager",
	"GovernancePolicy",
]
