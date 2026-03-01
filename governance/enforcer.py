"""
Script
------
enforcer.py

Path
----
python/hillstar/governance/enforcer.py

Purpose
-------
Core governance enforcement: validate that a Hillstar workflow was executed
before allowing a git commit to proceed.

Reads .hillstar/commit_ready.json written by runner.py on successful execution.
Checks age, workflow ID, and policy compliance.

Inputs
------
- hillstar_dir: path to .hillstar directory (default: .hillstar in cwd)
- policy: GovernancePolicy instance

Outputs
-------
- (compliant: bool, reason: str)

Assumptions
-----------
- runner.py writes commit_ready.json on successful workflow completion
- .hillstar/ directory exists in the project root

Parameters
----------
See GovernancePolicy

Failure Modes
-------------
- commit_ready.json missing: non-compliant
- commit_ready.json stale (age > max_age_seconds): non-compliant
- HILLSTAR_FORCE_COMMIT=1 env var: override allowed if policy permits

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
from datetime import datetime, timezone

from .policy import GovernancePolicy


COMMIT_READY_FILE = "commit_ready.json"


class GovernanceEnforcer:
	"""Enforce workflow-driven development before git commits."""

	def __init__(self, hillstar_dir: str = ".hillstar", policy: GovernancePolicy | None = None):
		self.hillstar_dir = hillstar_dir
		self.policy = policy or GovernancePolicy.load(hillstar_dir)
		self._marker_path = os.path.join(hillstar_dir, COMMIT_READY_FILE)

	def check(self, dev_mode: bool = False) -> tuple[bool, str]:
		"""
		Check whether the current state is compliant for a git commit.

		Args:
			dev_mode: If True (or HILLSTAR_DEV_MODE=1 in env), skip governance check.

		Returns:
			(compliant, reason): compliant=True means commit is allowed.
		"""
		# Check development mode first
		if dev_mode or os.environ.get("HILLSTAR_DEV_MODE") == "1":
			return True, "Development mode active (--dev flag)"

		# Check force override
		if self.policy.allow_force_override and os.environ.get("HILLSTAR_FORCE_COMMIT") == "1":
			return True, "Force override active (HILLSTAR_FORCE_COMMIT=1)"

		# Check marker exists
		if not os.path.exists(self._marker_path):
			return False, (
				"No workflow execution found. Run a Hillstar workflow first:\n"
				" hillstar execute <workflow.json>\n"
				"Or bypass with: HILLSTAR_FORCE_COMMIT=1 git commit ..."
			)

		# Load marker
		try:
			with open(self._marker_path, encoding="utf-8") as f:
				marker = json.load(f)
		except Exception as e:
			return False, f"Could not read commit_ready marker: {e}"

		# Check age
		executed_at = marker.get("executed_at")
		if not executed_at:
			return False, "Commit ready marker missing 'executed_at' timestamp"

		try:
			ts = datetime.fromisoformat(executed_at)
			if ts.tzinfo is None:
				ts = ts.replace(tzinfo=timezone.utc)
			age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
		except Exception as e:
			return False, f"Could not parse executed_at timestamp: {e}"

		if age_seconds > self.policy.max_age_seconds:
			return False, (
				f"Workflow execution is stale ({age_seconds:.0f}s ago, "
				f"max {self.policy.max_age_seconds}s). Re-run the workflow."
			)

		# Check workflow ID if required
		if self.policy.require_workflow_id and not marker.get("workflow_id"):
			return False, "Commit ready marker missing workflow_id"

		workflow_id = marker.get("workflow_id", "unknown")
		workflow_file = marker.get("workflow_file", "unknown")
		return True, (
			f"Compliant: workflow '{workflow_id}' ({workflow_file}) "
			f"executed {age_seconds:.0f}s ago"
		)

	def write_marker(self, workflow_id: str, workflow_file: str, summary: str = "") -> None:
		"""Write commit_ready marker after successful workflow execution."""
		os.makedirs(self.hillstar_dir, exist_ok=True)
		marker = {
			"workflow_id": workflow_id,
			"workflow_file": workflow_file,
			"executed_at": datetime.now(timezone.utc).isoformat(),
			"summary": summary,
		}
		with open(self._marker_path, "w", encoding="utf-8") as f:
			json.dump(marker, f, indent=2)

	def clear_marker(self) -> None:
		"""Clear the commit_ready marker (e.g. after commit completes)."""
		if os.path.exists(self._marker_path):
			os.remove(self._marker_path)

	def status(self) -> dict:
		"""Return full status dictionary for display."""
		compliant, reason = self.check()
		marker = {}
		if os.path.exists(self._marker_path):
			try:
				with open(self._marker_path, encoding="utf-8") as f:
					marker = json.load(f)
			except Exception:
				pass
		return {
			"compliant": compliant,
			"reason": reason,
			"marker": marker,
			"policy": {
				"max_age_seconds": self.policy.max_age_seconds,
				"allow_force_override": self.policy.allow_force_override,
			},
		}
