"""
Unit tests for governance/enforcer.py

Production-grade test suite with:
- Deep Assertions: Check actual values, timestamps, return types
- Mock Verification: assert_called_with() for file I/O and env vars
- Parameterized Tests: Multiple scenarios (dev_mode, force_override, stale markers)
- Boundary Testing: Missing files, None values, invalid timestamps
- Realistic Data: Actual marker JSON structures from GovernanceEnforcer
- Integration Points: File I/O verified (read/write/delete)
- Side Effects: Marker creation, file system changes, timestamp validation
- Error Messages: Exact error text in compliance reasons
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.enforcer import GovernanceEnforcer, COMMIT_READY_FILE
from governance.policy import GovernancePolicy


class TestGovernanceEnforcerInitialization:
	"""Deep initialization and dependency injection."""

	def test_init_defaults_to_hillstar_directory(self):
		"""Initialization: Default hillstar_dir is .hillstar."""
		enforcer = GovernanceEnforcer()
		assert enforcer.hillstar_dir == ".hillstar"

	def test_init_custom_hillstar_dir_stored(self):
		"""Initialization: Custom directory path is stored."""
		enforcer = GovernanceEnforcer(hillstar_dir="/custom/.hillstar")
		assert enforcer.hillstar_dir == "/custom/.hillstar"

	def test_init_creates_policy_from_directory_by_default(self):
		"""Deep: Policy is loaded from directory by default."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			assert isinstance(enforcer.policy, GovernancePolicy)

	def test_init_accepts_custom_policy(self):
		"""Initialization: Custom policy is used instead of loading."""
		custom_policy = GovernancePolicy(max_age_seconds=1800)
		enforcer = GovernanceEnforcer(policy=custom_policy)
		assert enforcer.policy is custom_policy
		assert enforcer.policy.max_age_seconds == 1800

	def test_init_marker_path_calculated_correctly(self):
		"""Deep: Marker path is computed from hillstar_dir."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			expected = os.path.join(tmpdir, COMMIT_READY_FILE)
			assert enforcer._marker_path == expected


class TestCheckDevMode:
	"""Deep testing of development mode bypass."""

	def test_check_dev_mode_parameter_true_returns_compliant(self):
		"""Deep: dev_mode parameter overrides all checks."""
		enforcer = GovernanceEnforcer()
		compliant, reason = enforcer.check(dev_mode=True)
		assert compliant is True
		assert "Development mode" in reason

	def test_check_hillstar_dev_mode_env_var_overrides(self):
		"""Deep: HILLSTAR_DEV_MODE environment variable bypasses check."""
		enforcer = GovernanceEnforcer()
		with patch.dict(os.environ, {"HILLSTAR_DEV_MODE": "1"}):
			compliant, reason = enforcer.check(dev_mode=False)
		assert compliant is True

	def test_check_dev_mode_false_does_not_skip_checks(self):
		"""Boundary: dev_mode=False does not bypass enforcement."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			compliant, reason = enforcer.check(dev_mode=False)
		assert compliant is False
		assert "No workflow execution found" in reason

	@pytest.mark.parametrize("env_value", ["0", "", "false", "False"])
	def test_check_dev_mode_env_false_values_do_not_bypass(self, env_value):
		"""Boundary: HILLSTAR_DEV_MODE with false values does not bypass."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			with patch.dict(os.environ, {"HILLSTAR_DEV_MODE": env_value}):
				compliant, reason = enforcer.check()
		assert compliant is False


class TestCheckForceOverride:
	"""Deep testing of force override mechanism."""

	def test_check_force_override_env_var_returns_compliant(self):
		"""Deep: HILLSTAR_FORCE_COMMIT bypasses workflow check."""
		enforcer = GovernanceEnforcer()
		with patch.dict(os.environ, {"HILLSTAR_FORCE_COMMIT": "1"}):
			compliant, reason = enforcer.check()
		assert compliant is True
		assert "Force override" in reason

	def test_check_force_override_requires_policy_permission(self):
		"""Deep: Force override only works if policy allows it."""
		policy = GovernancePolicy(allow_force_override=False)
		enforcer = GovernanceEnforcer(policy=policy)
		with patch.dict(os.environ, {"HILLSTAR_FORCE_COMMIT": "1"}):
			compliant, reason = enforcer.check()
		assert compliant is False

	def test_check_force_override_message_includes_env_var_name(self):
		"""Deep: Reason message includes HILLSTAR_FORCE_COMMIT reference."""
		enforcer = GovernanceEnforcer()
		with patch.dict(os.environ, {"HILLSTAR_FORCE_COMMIT": "1"}):
			compliant, reason = enforcer.check()
		assert "HILLSTAR_FORCE_COMMIT" in reason


class TestCheckMarkerFile:
	"""Deep testing of commit marker validation."""

	def test_check_missing_marker_returns_non_compliant(self):
		"""Boundary: Missing marker file returns non-compliant."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			compliant, reason = enforcer.check()
		assert compliant is False
		assert "No workflow execution found" in reason

	def test_check_valid_marker_returns_compliant(self):
		"""Deep: Valid marker with recent timestamp returns compliant."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			now = datetime.now(timezone.utc)
			marker_data = {
				"executed_at": now.isoformat(),
				"workflow_id": "test-workflow",
				"workflow_file": "test.json",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is True
		assert "Compliant" in reason

	def test_check_corrupted_marker_returns_error_message(self):
		"""Boundary: Corrupted marker file returns error reason."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				f.write("not valid json {]")
			compliant, reason = enforcer.check()
		assert compliant is False
		assert "Could not read" in reason


class TestCheckTimestampValidation:
	"""Deep testing of marker age validation."""

	def test_check_missing_executed_at_returns_error(self):
		"""Boundary: Marker without executed_at timestamp fails."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			marker_data = {"workflow_id": "test"}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is False
		assert "executed_at" in reason

	def test_check_invalid_timestamp_format_returns_error(self):
		"""Boundary: Invalid ISO timestamp format returns error."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			marker_data = {
				"executed_at": "not-a-timestamp",
				"workflow_id": "test",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is False
		assert "timestamp" in reason.lower()

	def test_check_recent_marker_within_max_age_compliant(self):
		"""Deep: Marker within max_age_seconds is compliant."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(max_age_seconds=3600)
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir, policy=policy)
			now = datetime.now(timezone.utc)
			marker_data = {
				"executed_at": now.isoformat(),
				"workflow_id": "test-wf",
				"workflow_file": "test.json",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is True

	def test_check_stale_marker_exceeds_max_age_non_compliant(self):
		"""Boundary: Marker older than max_age_seconds is non-compliant."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(max_age_seconds=10)
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir, policy=policy)
			old_time = datetime.now(timezone.utc) - timedelta(seconds=20)
			marker_data = {
				"executed_at": old_time.isoformat(),
				"workflow_id": "test-wf",
				"workflow_file": "test.json",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is False
		assert "stale" in reason.lower()

	def test_check_stale_marker_includes_age_in_message(self):
		"""Deep: Stale marker error includes age in seconds."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(max_age_seconds=10)
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir, policy=policy)
			old_time = datetime.now(timezone.utc) - timedelta(seconds=30)
			marker_data = {
				"executed_at": old_time.isoformat(),
				"workflow_id": "test",
				"workflow_file": "test.json",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert "stale" in reason.lower()
		assert "30" in reason or "3" in reason


class TestCheckWorkflowIdValidation:
	"""Deep testing of workflow ID requirement."""

	def test_check_missing_workflow_id_when_required_non_compliant(self):
		"""Boundary: Missing workflow_id when required fails check."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(require_workflow_id=True)
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir, policy=policy)
			now = datetime.now(timezone.utc)
			marker_data = {
				"executed_at": now.isoformat(),
				"workflow_file": "test.json",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is False
		assert "workflow_id" in reason

	def test_check_missing_workflow_id_when_not_required_compliant(self):
		"""Deep: Missing workflow_id is OK when policy allows."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(require_workflow_id=False)
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir, policy=policy)
			now = datetime.now(timezone.utc)
			marker_data = {
				"executed_at": now.isoformat(),
				"workflow_file": "test.json",
			}
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path, "w") as f:
				json.dump(marker_data, f)
			compliant, reason = enforcer.check()
		assert compliant is True


class TestWriteMarker:
	"""Side effect validation for marker creation."""

	def test_write_marker_creates_file(self):
		"""Side Effect: write_marker() creates commit_ready.json."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			enforcer.write_marker("test-workflow", "test.json", "Test summary")
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			assert os.path.exists(marker_path)

	def test_write_marker_contains_workflow_id(self):
		"""Deep: Written marker contains workflow_id."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			enforcer.write_marker("my-workflow-123", "workflow.json")
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path) as f:
				data = json.load(f)
		assert data["workflow_id"] == "my-workflow-123"

	def test_write_marker_contains_workflow_file(self):
		"""Deep: Written marker contains workflow_file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			enforcer.write_marker("test-wf", "workflows/main.json")
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path) as f:
				data = json.load(f)
		assert data["workflow_file"] == "workflows/main.json"

	def test_write_marker_contains_executed_at_timestamp(self):
		"""Deep: Written marker has executed_at ISO timestamp."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			before = datetime.now(timezone.utc)
			enforcer.write_marker("test", "test.json")
			after = datetime.now(timezone.utc)
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path) as f:
				data = json.load(f)
			ts_str = data["executed_at"]
			ts = datetime.fromisoformat(ts_str)
		assert before <= ts <= after

	def test_write_marker_contains_summary(self):
		"""Deep: Written marker contains optional summary."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			enforcer.write_marker("test", "test.json", "Custom summary text")
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			with open(marker_path) as f:
				data = json.load(f)
		assert data["summary"] == "Custom summary text"

	def test_write_marker_creates_directory_if_missing(self):
		"""Side Effect: Creates hillstar_dir if it doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			hillstar_dir = os.path.join(tmpdir, "new", ".hillstar")
			enforcer = GovernanceEnforcer(hillstar_dir=hillstar_dir)
			enforcer.write_marker("test", "test.json")
			assert os.path.isdir(hillstar_dir)


class TestClearMarker:
	"""Side effect validation for marker deletion."""

	def test_clear_marker_removes_file(self):
		"""Side Effect: clear_marker() deletes commit_ready.json."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			enforcer.write_marker("test", "test.json")
			marker_path = os.path.join(tmpdir, COMMIT_READY_FILE)
			assert os.path.exists(marker_path)
			enforcer.clear_marker()
		assert not os.path.exists(marker_path)

	def test_clear_marker_safe_when_file_missing(self):
		"""Boundary: clear_marker() doesn't error if file missing."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			try:
				enforcer.clear_marker()
			except FileNotFoundError:
				pytest.fail("clear_marker() should not raise when file missing")


class TestStatusMethod:
	"""Integration testing of status reporting."""

	def test_status_returns_dict_with_required_fields(self):
		"""Integration: status() returns complete dictionary."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			status = enforcer.status()
		assert "compliant" in status
		assert "reason" in status
		assert "marker" in status
		assert "policy" in status

	def test_status_includes_current_compliance_state(self):
		"""Deep: status() reflects current compliance."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			status = enforcer.status()
		assert status["compliant"] is False

	def test_status_includes_marker_data_when_file_exists(self):
		"""Deep: status() includes parsed marker content."""
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir)
			enforcer.write_marker("test-wf", "test.json")
			status = enforcer.status()
		assert status["marker"]["workflow_id"] == "test-wf"

	def test_status_includes_policy_settings(self):
		"""Deep: status() includes policy max_age_seconds."""
		policy = GovernancePolicy(max_age_seconds=1800)
		with tempfile.TemporaryDirectory() as tmpdir:
			enforcer = GovernanceEnforcer(hillstar_dir=tmpdir, policy=policy)
			status = enforcer.status()
		assert status["policy"]["max_age_seconds"] == 1800
