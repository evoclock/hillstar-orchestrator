"""
Script
------
policy.py

Path
----
python/hillstar/governance/policy.py

Purpose
-------
Governance policy definitions: what constitutes a valid workflow execution
for the purpose of gating git commits.

Inputs
------
None (configuration constants)

Outputs
-------
GovernancePolicy dataclass

Assumptions
-----------
- Policy is loaded from .hillstar/governance_policy.json if present,
  otherwise defaults apply.

Parameters
----------
- max_age_seconds: Maximum age of a commit_ready marker (default 3600 = 1 hour)
- allow_force_override: Whether HILLSTAR_FORCE_COMMIT env var is respected
- require_workflow_id: Whether a workflow ID must be present in the marker
- blocked_patterns: File patterns that always require a workflow (e.g. *.py, *.json)
- exempt_patterns: File patterns exempt from enforcement (e.g. *.md docs, logs)

Failure Modes
-------------
- policy.json malformed: falls back to defaults with a warning

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class GovernancePolicy:
	"""Policy configuration for workflow enforcement."""

	max_age_seconds: int = 3600
	allow_force_override: bool = True
	require_workflow_id: bool = True
	blocked_patterns: list[str] = field(default_factory=lambda: [
		"*.py",
		"*.json",
		"*.tsv",
		"*.sh",
	])
	exempt_patterns: list[str] = field(default_factory=lambda: [
		"*.log",
		"*.md",
		"*.txt",
	])

	@classmethod
	def load(cls, hillstar_dir: str) -> "GovernancePolicy":
		"""Load policy from .hillstar/governance_policy.json, or return defaults."""
		policy_path = os.path.join(hillstar_dir, "governance_policy.json")
		if not os.path.exists(policy_path):
			return cls()
		try:
			with open(policy_path, encoding="utf-8") as f:
				data = json.load(f)
			return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
		except Exception as e:
			print(f"[governance] Warning: could not load policy ({e}), using defaults")
			return cls()

	def save(self, hillstar_dir: str) -> None:
		"""Persist policy to .hillstar/governance_policy.json."""
		os.makedirs(hillstar_dir, exist_ok=True)
		policy_path = os.path.join(hillstar_dir, "governance_policy.json")
		with open(policy_path, "w", encoding="utf-8") as f:
			json.dump({
				"max_age_seconds": self.max_age_seconds,
				"allow_force_override": self.allow_force_override,
				"require_workflow_id": self.require_workflow_id,
				"blocked_patterns": self.blocked_patterns,
				"exempt_patterns": self.exempt_patterns,
			}, f, indent=2)
