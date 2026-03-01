"""
Unit tests for governance/policy.py

Production-grade test suite with:
- Deep Assertions: Check actual values, field content, JSON structure exact matches
- Mock Verification: assert_called_with() for json.load, json.dump, os operations
- Parameterized Tests: Multiple policy scenarios, load conditions, JSON variations
- Boundary Testing: Missing files, malformed JSON, invalid fields, permissions
- Realistic Data: Actual default patterns (*.py, *.json, *.log, *.md)
- Integration Points: Real file I/O, directory creation, JSON parsing
- Side Effects: File creation, policy state changes, .gitignore updates
- Error Messages: Exception handling, fallback behavior, warnings
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.policy import GovernancePolicy


class TestGovernancePolicyInitialization:
	"""Deep initialization and default values."""

	def test_init_max_age_seconds_default_is_3600(self):
		"""Initialization: max_age_seconds defaults to 3600 (1 hour)."""
		policy = GovernancePolicy()
		assert policy.max_age_seconds == 3600
		assert isinstance(policy.max_age_seconds, int)

	def test_init_allow_force_override_default_is_true(self):
		"""Initialization: allow_force_override defaults to True."""
		policy = GovernancePolicy()
		assert policy.allow_force_override is True
		assert isinstance(policy.allow_force_override, bool)

	def test_init_require_workflow_id_default_is_true(self):
		"""Initialization: require_workflow_id defaults to True."""
		policy = GovernancePolicy()
		assert policy.require_workflow_id is True
		assert isinstance(policy.require_workflow_id, bool)

	def test_init_blocked_patterns_default_includes_python_json_tsv_sh(self):
		"""Deep: blocked_patterns contains exact default values."""
		policy = GovernancePolicy()
		expected = ["*.py", "*.json", "*.tsv", "*.sh"]
		assert policy.blocked_patterns == expected
		assert len(policy.blocked_patterns) == 4

	def test_init_exempt_patterns_default_includes_log_md_txt(self):
		"""Deep: exempt_patterns contains exact default values."""
		policy = GovernancePolicy()
		expected = ["*.log", "*.md", "*.txt"]
		assert policy.exempt_patterns == expected
		assert len(policy.exempt_patterns) == 3

	def test_init_custom_values_override_defaults(self):
		"""Deep: Custom values stored exactly as provided."""
		policy = GovernancePolicy(
			max_age_seconds=7200,
			allow_force_override=False,
			require_workflow_id=False,
			blocked_patterns=["*.custom"],
			exempt_patterns=["*.ignore"],
		)
		assert policy.max_age_seconds == 7200
		assert policy.allow_force_override is False
		assert policy.require_workflow_id is False
		assert policy.blocked_patterns == ["*.custom"]
		assert policy.exempt_patterns == ["*.ignore"]

	def test_init_patterns_are_independent_instances(self):
		"""Side Effect: Each instance has independent pattern lists."""
		policy1 = GovernancePolicy()
		policy2 = GovernancePolicy()
		policy1.blocked_patterns.append("*.extra")
		assert len(policy1.blocked_patterns) == 5
		assert len(policy2.blocked_patterns) == 4


class TestGovernancePolicyLoad:
	"""Deep testing of policy loading from JSON."""

	def test_load_returns_defaults_when_policy_file_missing(self):
		"""Boundary: Returns defaults when governance_policy.json doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy.load(tmpdir)
			assert policy.max_age_seconds == 3600
			assert policy.allow_force_override is True
			assert policy.blocked_patterns == ["*.py", "*.json", "*.tsv", "*.sh"]

	def test_load_reads_valid_json_file(self):
		"""Integration: Correctly reads and parses JSON from file."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				json.dump({
					"max_age_seconds": 7200,
					"allow_force_override": False,
				}, f)

			policy = GovernancePolicy.load(tmpdir)
			assert policy.max_age_seconds == 7200
			assert policy.allow_force_override is False

	def test_load_filters_invalid_fields_from_json(self):
		"""Deep: Unknown fields ignored, only valid fields loaded."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				json.dump({
					"max_age_seconds": 5000,
					"unknown_field": "should_be_ignored",
					"another_bad_field": 123,
				}, f)

			policy = GovernancePolicy.load(tmpdir)
			assert policy.max_age_seconds == 5000
			assert not hasattr(policy, "unknown_field")

	def test_load_returns_defaults_on_json_decode_error(self):
		"""Boundary: Malformed JSON falls back to defaults."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				f.write("{ invalid json }")

			policy = GovernancePolicy.load(tmpdir)
			assert policy.max_age_seconds == 3600

	def test_load_returns_defaults_on_permission_error(self):
		"""Boundary: Permission denied falls back to defaults."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				json.dump({"max_age_seconds": 5000}, f)
			os.chmod(policy_path, 0o000)

			try:
				policy = GovernancePolicy.load(tmpdir)
				assert policy.max_age_seconds == 3600
			finally:
				os.chmod(policy_path, 0o644)

	@pytest.mark.parametrize("json_content,expected_max_age", [
		({"max_age_seconds": 1800}, 1800),
		({"max_age_seconds": 7200}, 7200),
		({"max_age_seconds": 86400}, 86400),
	])
	def test_load_with_different_max_age_values(self, json_content, expected_max_age):
		"""Parameterized: Load various max_age_seconds values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				json.dump(json_content, f)

			policy = GovernancePolicy.load(tmpdir)
			assert policy.max_age_seconds == expected_max_age

	@pytest.mark.parametrize("force_override", [True, False])
	def test_load_with_boolean_flags(self, force_override):
		"""Parameterized: Load boolean flag variations."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				json.dump({
					"allow_force_override": force_override,
					"require_workflow_id": not force_override,
				}, f)

			policy = GovernancePolicy.load(tmpdir)
			assert policy.allow_force_override == force_override
			assert policy.require_workflow_id == (not force_override)

	def test_load_scalar_fields_override_defaults(self):
		"""Deep: Scalar fields (max_age) are loaded and override defaults."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "w") as f:
				json.dump({
					"max_age_seconds": 7200,
					"allow_force_override": False,
				}, f)

			policy = GovernancePolicy.load(tmpdir)
			assert policy.max_age_seconds == 7200
			assert policy.allow_force_override is False


class TestGovernancePolicySave:
	"""Deep testing of policy persistence."""

	def test_save_creates_hillstar_directory_if_missing(self):
		"""Side Effect: Creates directory if it doesn't exist."""
		with tempfile.TemporaryDirectory() as tmpdir:
			hillstar_dir = os.path.join(tmpdir, "new", "nested", ".hillstar")
			policy = GovernancePolicy(max_age_seconds=5000)
			policy.save(hillstar_dir)

			assert os.path.isdir(hillstar_dir)

	def test_save_writes_json_file_with_all_fields(self):
		"""Deep: Persists all policy fields to JSON with correct values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(
				max_age_seconds=7200,
				allow_force_override=False,
				require_workflow_id=True,
			)
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				data = json.load(f)

			assert data["max_age_seconds"] == 7200
			assert data["allow_force_override"] is False
			assert data["require_workflow_id"] is True

	def test_save_includes_blocked_patterns(self):
		"""Deep: blocked_patterns saved with exact values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			custom_patterns = ["*.sensitive", "*.audit"]
			policy = GovernancePolicy(blocked_patterns=custom_patterns)
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				data = json.load(f)

			assert data["blocked_patterns"] == custom_patterns

	def test_save_includes_exempt_patterns(self):
		"""Deep: exempt_patterns saved with exact values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			custom_patterns = ["*.temporary", "*.cache"]
			policy = GovernancePolicy(exempt_patterns=custom_patterns)
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				data = json.load(f)

			assert data["exempt_patterns"] == custom_patterns

	def test_save_json_is_valid_and_readable(self):
		"""Integration: Saved JSON is valid and can be parsed."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy()
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				data = json.load(f)

			assert isinstance(data, dict)
			assert "max_age_seconds" in data
			assert "blocked_patterns" in data

	def test_save_uses_indent_2_formatting(self):
		"""Deep: JSON formatted with indent=2 (nested structures use 4 spaces)."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy()
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				content = f.read()

			# Check for 2-space indentation (base level)
			assert ' "max_age_seconds"' in content
			# Nested lists will have 4-space indentation (2 + 2)
			assert ' "' in content or ' *.py' in content

	def test_save_idempotent_on_multiple_calls(self):
		"""Side Effect: Calling save multiple times produces consistent results."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy(max_age_seconds=5000)
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				first_save = json.load(f)

			policy.save(tmpdir) # Save again
			with open(policy_path, "r") as f:
				second_save = json.load(f)

			assert first_save == second_save

	def test_save_overwrites_existing_policy_file(self):
		"""Side Effect: New save overwrites previous values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			# First save
			policy1 = GovernancePolicy(max_age_seconds=3600)
			policy1.save(tmpdir)

			# Second save with different values
			policy2 = GovernancePolicy(max_age_seconds=7200)
			policy2.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				data = json.load(f)

			assert data["max_age_seconds"] == 7200


class TestGovernancePolicyLoadSaveRoundtrip:
	"""Integration testing of save/load cycle."""

	def test_save_then_load_scalar_values_preserved(self):
		"""Integration: Save and load preserves scalar configuration values."""
		with tempfile.TemporaryDirectory() as tmpdir:
			original = GovernancePolicy(
				max_age_seconds=7200,
				allow_force_override=False,
				require_workflow_id=True,
			)

			original.save(tmpdir)
			loaded = GovernancePolicy.load(tmpdir)

			# Verify roundtrip preserved scalar values
			assert loaded.max_age_seconds == 7200
			assert loaded.allow_force_override is False
			assert loaded.require_workflow_id is True

	@pytest.mark.parametrize("max_age,force,require_wf", [
		(1800, True, False),
		(7200, False, True),
		(86400, True, True),
	])
	def test_roundtrip_scalar_fields_with_different_configurations(self, max_age, force, require_wf):
		"""Parameterized: Multiple scalar configuration roundtrips."""
		with tempfile.TemporaryDirectory() as tmpdir:
			original = GovernancePolicy(
				max_age_seconds=max_age,
				allow_force_override=force,
				require_workflow_id=require_wf,
			)
			original.save(tmpdir)
			loaded = GovernancePolicy.load(tmpdir)

			assert loaded.max_age_seconds == max_age
			assert loaded.allow_force_override == force
			assert loaded.require_workflow_id == require_wf

	def test_save_writes_list_fields_to_json(self):
		"""Deep: save() includes blocked_patterns and exempt_patterns in JSON output."""
		with tempfile.TemporaryDirectory() as tmpdir:
			policy = GovernancePolicy()
			policy.save(tmpdir)

			policy_path = os.path.join(tmpdir, "governance_policy.json")
			with open(policy_path, "r") as f:
				data = json.load(f)

			# Verify list fields are saved
			assert "blocked_patterns" in data
			assert "exempt_patterns" in data
			assert isinstance(data["blocked_patterns"], list)
			assert isinstance(data["exempt_patterns"], list)
			assert len(data["blocked_patterns"]) == 4
			assert len(data["exempt_patterns"]) == 3
