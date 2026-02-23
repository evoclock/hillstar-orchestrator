"""
Test credential redactor tool.

Validates that:
1. API keys are detected and redacted
2. Tokens are detected and redacted
3. Common credential patterns are recognized
4. Redaction preserves string structure
5. Convenience functions work correctly
"""

from utils.credential_redactor import (
    CredentialRedactor,
    redact,
    contains_credentials,
)


class TestCredentialDetection:
    """Test credential detection patterns."""

    def test_detects_anthropic_keys(self):
        """Test detection of Anthropic API keys."""
        text = "My key is sk-ant-abc123def456"
        assert contains_credentials(text)
        assert CredentialRedactor.contains_credentials(text)

    def test_detects_openai_keys(self):
        """Test detection of OpenAI API keys."""
        text = "api_key = sk-proj-abcdef1234567890"
        assert contains_credentials(text)

    def test_detects_bearer_tokens(self):
        """Test detection of Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        assert contains_credentials(text)

    def test_detects_generic_api_keys(self):
        """Test detection of generic api_key patterns."""
        text = 'api_key = "secret-value-123"'
        assert contains_credentials(text)

    def test_detects_env_var_values(self):
        """Test detection of environment variable patterns."""
        text = "ANTHROPIC_API_KEY=sk-ant-super-secret-key"
        assert contains_credentials(text)

    def test_no_false_positives_on_normal_text(self):
        """Test that normal text doesn't trigger false positives."""
        texts = [
            "This is a normal sentence",
            "my-project-name is valid",
            "version 1.0.0 released",
        ]
        for text in texts:
            assert not contains_credentials(text)

    def test_empty_string(self):
        """Test that empty string is handled gracefully."""
        assert not contains_credentials("")


class TestCredentialRedaction:
    """Test credential redaction behavior."""

    def test_redacts_anthropic_keys(self):
        """Test redaction of Anthropic keys."""
        text = "My key is sk-ant-abc123def456"
        result = redact(text)
        assert "[REDACTED:anthropic_key]" in result
        assert "sk-ant" not in result

    def test_redacts_openai_keys(self):
        """Test redaction of OpenAI keys."""
        text = "key=sk-proj-abcdef1234567890"
        result = redact(text)
        assert "[REDACTED:openai_key]" in result
        assert "sk-proj" not in result

    def test_redacts_bearer_tokens(self):
        """Test redaction of Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact(text)
        assert "[REDACTED:bearer_token]" in result
        assert "Bearer eyJ" not in result

    def test_redacts_multiple_credentials(self):
        """Test redaction when multiple credentials present."""
        text = 'Config: api_key="secret1" and OPENAI_API_KEY=sk-proj-abc123'
        result = redact(text)
        # Should have multiple redactions
        assert result.count("[REDACTED:") >= 2
        assert "secret1" not in result
        assert "sk-proj" not in result

    def test_preserves_non_credential_text(self):
        """Test that non-credential parts are preserved."""
        text = "Error: Failed to authenticate with API key sk-ant-secret123"
        result = redact(text)
        assert "Error: Failed to authenticate with API key" in result
        assert "sk-ant-secret123" not in result
        assert "[REDACTED" in result

    def test_redaction_preserves_structure(self):
        """Test that redaction maintains string structure."""
        text = "URL: https://api.example.com/v1?key=sk-ant-secret"
        result = redact(text)
        # Structure should be preserved, just credential replaced
        assert "https://api.example.com/v1?key=" in result
        assert "[REDACTED" in result

    def test_error_message_with_credentials(self):
        """Test realistic error message redaction."""
        error = "Failed to authenticate: Invalid API key 'sk-ant-super-secret-key'. Check ANTHROPIC_API_KEY=sk-ant-super-secret-key"
        result = redact(error)
        assert "sk-ant-super-secret-key" not in result
        assert "[REDACTED" in result

    def test_json_with_credentials(self):
        """Test redaction in JSON-like strings."""
        json_str = '{"api_key": "sk-proj-secret123", "model": "gpt-4"}'
        result = redact(json_str)
        assert "sk-proj-secret123" not in result
        assert "[REDACTED" in result
        assert "gpt-4" in result  # Non-sensitive parts preserved


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
        assert len(result) > 10000  # Still long after redaction

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
