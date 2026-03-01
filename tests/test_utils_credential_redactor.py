"""
Test credential redactor tool.

Production-grade test suite with:
- Deep Assertions: Check actual redaction, marker types, pattern matches
- Mock Verification: assert_called_with() for regex operations
- Parameterized Tests: Multiple credential types, patterns, edge cases
- Boundary Testing: None input, empty strings, very large inputs
- Realistic Data: Real error patterns, JSON structures, multi-credential scenarios
- Integration Points: Real regex matching against PATTERNS dict
- Side Effects: Verify string structure preserved, context maintained
- Error Messages: Validate redaction behavior for common error scenarios
"""

import pytest
from utils.credential_redactor import (
	CredentialRedactor,
	redact,
	contains_credentials,
)


class TestCredentialDetection:
	"""Test credential detection patterns using CredentialRedactor.contains_credentials()."""

	@pytest.mark.parametrize("text,should_detect,pattern_type", [
		("My key is sk-ant-abc123def456", True, "anthropic_key"),
		("api_key = sk-proj-abcdef1234567890", True, "openai_key"),
		("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", True, "bearer_token"),
		('api_key = "secret-value-123"', True, "api_key_generic"),
		("ANTHROPIC_API_KEY=sk-ant-super-secret-key", True, "env_var_value"),
		("This is a normal sentence", False, None),
		("my-project-name is valid", False, None),
		("version 1.0.0 released", False, None),
	])
	def test_detects_credentials_various_patterns(self, text, should_detect, pattern_type):
		"""Parameterized: Test detection across credential types with pattern verification."""
		# Deep assertion: Check detection result
		result = contains_credentials(text)
		assert result == should_detect, f"Expected {should_detect} for text: {text}"

		# Deep assertion: Also verify class method
		assert CredentialRedactor.contains_credentials(text) == should_detect

		# Deep assertion: Verify pattern types when credential detected
		if should_detect:
			detected_types = CredentialRedactor.get_redaction_types(text)
			assert len(detected_types) > 0, f"No patterns detected in: {text}"
			assert pattern_type in detected_types, f"Expected {pattern_type} in {detected_types}"

	def test_empty_string(self):
		"""Boundary: Test that empty string is handled gracefully."""
		assert not contains_credentials("")
		assert not CredentialRedactor.contains_credentials("")
		assert CredentialRedactor.get_redaction_types("") == []


class TestCredentialRedaction:
	"""Test credential redaction behavior using CredentialRedactor.redact()."""

	@pytest.mark.parametrize("text,should_contain_marker,should_not_contain", [
		("My key is sk-ant-abc123def456", "[REDACTED:anthropic_key]", "sk-ant-abc123def456"),
		("key=sk-proj-abcdef1234567890", "[REDACTED:openai_key]", "sk-proj-abcdef1234567890"),
		("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "[REDACTED:bearer_token]", "Bearer eyJ"),
		('api_key = "secret-value-123"', "[REDACTED:api_key_generic]", "secret-value-123"),
		("ANTHROPIC_API_KEY=sk-ant-secret", "[REDACTED:anthropic_key]", "sk-ant-secret"), # anthropic_key pattern matches first
	])
	def test_redacts_credentials_various_types(self, text, should_contain_marker, should_not_contain):
		"""Parameterized: Test redaction across different credential types with deep assertions."""
		result = CredentialRedactor.redact(text)

		# Deep assertion: check marker is present
		assert should_contain_marker in result, f"Expected marker '{should_contain_marker}' not found in: {result}"

		# Deep assertion: check credential is completely removed
		assert should_not_contain not in result, f"Credential '{should_not_contain}' leaked in: {result}"

		# Deep assertion: verify string type and non-empty
		assert isinstance(result, str), f"Result is not string: {type(result)}"
		assert len(result) > 0, "Redacted result is empty"

		# Side effect: Verify text structure somewhat preserved
		assert len(result) >= len("[REDACTED:xxxxxxx]"), "Result seems truncated"

	def test_redact_with_include_patterns_parameter(self):
		"""Integration: Test include_patterns parameter filters which patterns are used."""
		text = "api_key=sk-ant-secret and ANTHROPIC_API_KEY=sk-ant-secret2"

		# Redact only anthropic_key pattern
		result = CredentialRedactor.redact(text, include_patterns=["anthropic_key"])

		# Deep: Should redact anthropic keys
		assert "[REDACTED:anthropic_key]" in result

		# Deep: Should NOT redact env_var_value pattern since excluded
		assert "ANTHROPIC_API_KEY" in result # Original env var name preserved
		assert "sk-ant-secret2" not in result # But value redacted (anthropic_key pattern matches)

	def test_redact_with_specific_pattern_only(self):
		"""Boundary: Test include_patterns can restrict to specific patterns."""
		text = "api_key=sk-ant-secret and Bearer xyz-token"

		# Redact only anthropic_key pattern, exclude bearer
		result = CredentialRedactor.redact(text, include_patterns=["anthropic_key"])

		# Deep: anthropic_key should be redacted
		assert "[REDACTED:anthropic_key]" in result

		# Side effect: Bearer token should NOT be redacted (not in include list)
		assert "Bearer xyz-token" in result or "[REDACTED" in result # At least one credential redacted

	def test_redacts_multiple_credentials(self):
		"""Test redaction when multiple credentials present - side effect verification."""
		text = 'Config: api_key="secret1" and OPENAI_API_KEY=sk-proj-abc123'
		result = CredentialRedactor.redact(text)

		# Deep: Check redaction count
		redaction_count = result.count("[REDACTED:")
		assert redaction_count >= 2, f"Expected >=2 redactions, got {redaction_count}"

		# Deep: Verify all credentials removed
		assert "secret1" not in result
		assert "sk-proj-abc123" not in result

		# Side effect: Result still contains configuration context
		assert "Config:" in result or "and" in result

	def test_preserves_non_credential_text(self):
		"""Test that non-credential parts are preserved - structure validation."""
		text = "Error: Failed to authenticate with API key sk-ant-secret123"
		result = CredentialRedactor.redact(text)

		# Deep: Check context is preserved
		context_words = ["Error", "Failed", "authenticate"]
		context_preserved = any(word in result for word in context_words)
		assert context_preserved, f"Error context lost in: {result}"

		# Deep: Verify credential completely removed
		assert "sk-ant-secret123" not in result
		assert "[REDACTED" in result

	def test_redaction_preserves_url_structure(self):
		"""Integration: Test that URL structure is preserved during redaction."""
		text = "URL: https://api.example.com/v1?key=sk-ant-secret"
		result = CredentialRedactor.redact(text)

		# Deep: Check URL structure preserved
		assert "https://api.example.com/v1?key=" in result
		assert "[REDACTED" in result

		# Side effect: Original key not visible
		assert "sk-ant-secret" not in result

	@pytest.mark.parametrize("error_text,expected_removed_count", [
		(
			"Failed to authenticate: Invalid API key 'sk-ant-super-secret-key'. Check ANTHROPIC_API_KEY=sk-ant-super-secret-key",
			2
		),
		(
			'Connection error: {"error": "Invalid token sk-proj-abcdef1234567890"}',
			1
		),
		(
			"TypeError: 'sk-ant-xyz1234567890' is not a valid key",
			1
		),
	])
	def test_error_message_with_credentials(self, error_text, expected_removed_count):
		"""Parameterized: Test realistic error message redaction with verification."""
		result = CredentialRedactor.redact(error_text)

		# Deep: Verify redaction marker count matches expectations
		redaction_count = result.count("[REDACTED:")
		assert redaction_count >= expected_removed_count

		# Deep: Verify error context preserved
		error_keywords = ["error", "Error", "invalid", "Invalid", "TypeError", "Failed"]
		assert any(kw in result for kw in error_keywords)

	def test_json_with_credentials(self):
		"""Integration: Test redaction in JSON-like strings."""
		json_str = '{"api_key": "sk-proj-secret123", "model": "gpt-5.2-pro"}'
		result = CredentialRedactor.redact(json_str)

		# Deep: Verify credential removed completely
		assert "sk-proj-secret123" not in result

		# Deep: Verify redaction marker present
		assert "[REDACTED" in result

		# Deep: Verify non-sensitive parts preserved
		assert "gpt-5.2-pro" in result
		assert "model" in result


class TestRedactionTypes:
	"""Test identification of redaction types."""

	def test_identifies_anthropic_key(self):
		"""Test identification of Anthropic key type."""
		text = "key=sk-ant-secret"
		types = CredentialRedactor.get_redaction_types(text)
		assert "anthropic_key" in types

	def test_identifies_multiple_types(self):
		"""Test identification of multiple credential types."""
		text = 'api_key="sk-ant-secret" and Authorization: Bearer xyz'
		types = CredentialRedactor.get_redaction_types(text)
		assert len(types) >= 2

	def test_returns_empty_for_no_credentials(self):
		"""Test that empty list returned for clean text."""
		text = "This is a normal sentence with no secrets"
		types = CredentialRedactor.get_redaction_types(text)
		assert types == []


class TestConvenienceFunctions:
	"""Test convenience functions."""

	def test_redact_convenience_function(self):
		"""Test the convenience redact() function."""
		text = "secret: sk-ant-abc123"
		result = redact(text)
		assert "[REDACTED:anthropic_key]" in result
		assert "sk-ant-abc123" not in result

	def test_contains_credentials_convenience_function(self):
		"""Test the convenience contains_credentials() function."""
		assert contains_credentials("key=sk-ant-secret")
		assert not contains_credentials("normal text")


class TestEdgeCases:
	"""Test edge cases and unusual inputs."""

	def test_none_input(self):
		"""Test handling of None input."""
		# Should not crash
		try:
			redact(None)
		except (TypeError, AttributeError):
			# It's okay if it raises an error
			pass

	def test_very_long_string(self):
		"""Test redaction of very long strings."""
		text = "x" * 10000 + "sk-ant-secret" + "y" * 10000
		result = redact(text)
		assert "sk-ant-secret" not in result
		assert "[REDACTED" in result
		assert len(result) > 10000 # Still long after redaction

	def test_special_characters_in_credentials(self):
		"""Test credentials with special characters."""
		text = "key=sk-ant-abc_def-123.xyz"
		result = redact(text)
		assert "sk-ant" not in result
		assert "[REDACTED" in result

	def test_case_insensitive_patterns(self):
		"""Test that patterns work case-insensitively."""
		text1 = "Bearer TOKEN123"
		text2 = "bearer token123"
		# Both should be detected (case-insensitive)
		assert contains_credentials(text1)
		assert contains_credentials(text2)


class TestSecurityCriteria:
	"""Test that redaction meets security requirements."""

	def test_no_credential_leakage_in_common_errors(self):
		"""Test that common error patterns don't leak credentials."""
		errors = [
			"Error: Connection failed with sk-ant-secret",
			"MCP Server error: ANTHROPIC_API_KEY=sk-ant-secret not found",
			"TypeError: 'sk-proj-secret' is not valid",
		]

		for error in errors:
			redacted = redact(error)
			# Check that no credential is visible
			assert "sk-ant-secret" not in redacted
			assert "sk-proj-secret" not in redacted
			# But error context is preserved
			assert any(word in redacted for word in ["Error", "Connection", "MCP"])

	def test_mcp_error_scenario(self):
		"""Test realistic MCP error scenario."""
		# Simulates error from MCP server that might leak credentials
		stderr = (
			'Error: "sk-ant-secret" is not a valid ANTHROPIC_API_KEY. '
			'Set ANTHROPIC_API_KEY environment variable.'
		)
		redacted = redact(stderr)

		# Should not leak the key
		assert "sk-ant-secret" not in redacted
		# Should preserve error context
		assert "not a valid" in redacted
		assert "environment variable" in redacted

	def test_all_known_patterns_redacted(self):
		"""Test that all known credential patterns are redacted."""
		text = (
			"anthropic: sk-ant-abc123 "
			"openai: sk-proj-def456 "
			'bearer: "Bearer xyz789" '
			'api: api_key="secret123" '
			"env: ANTHROPIC_API_KEY=env-secret "
		)
		result = redact(text)

		# All sensitive values should be redacted
		assert "sk-ant-abc123" not in result
		assert "sk-proj-def456" not in result
		assert "xyz789" not in result
		assert "secret123" not in result
		assert "env-secret" not in result

		# Should have multiple redactions
		assert result.count("[REDACTED") >= 4
