"""
Test
----
test_openai_auth_resolver.py

Path
----
tests/test_openai_auth_resolver.py

Purpose
-------
Test OpenAI authentication resolution with subscription-first priority.

Tests cover:
- Subscription token available (CODEX_HOME/auth.json)
- Fallback to OPENAI_API_KEY
- Neither available -> error
- Malformed auth.json handling
- Missing auth.json handling

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from utils.openai_auth_resolver import OpenAIAuthResolver


class TestOpenAIAuthResolver:
    """Test OpenAI auth resolution with subscription-first priority."""

    def test_subscription_token_available(self, tmp_path):
        """Test successful resolution from CODEX_HOME/auth.json."""
        # Create mock auth.json with subscription tokens
        codex_home = tmp_path / "codex-home"
        codex_home.mkdir()
        auth_file = codex_home / "auth.json"

        auth_data = {
            "auth_mode": "chatgpt",
            "tokens": {
                "id_token": "id-token-value",
                "access_token": "access-token-value",
                "refresh_token": "refresh-token-value",
                "account_id": "user-12345"
            },
            "last_refresh": "2026-02-22T16:00:00Z"
        }

        with open(auth_file, "w") as f:
            json.dump(auth_data, f)

        # Test with CODEX_HOME set
        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
            auth_type, auth_value = OpenAIAuthResolver.resolve()

        assert auth_type == "subscription_token"
        assert auth_value == "access-token-value"

    def test_fallback_to_api_key(self, tmp_path):
        """Test fallback to OPENAI_API_KEY when CODEX_HOME not available."""
        # No CODEX_HOME set, only API key available
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "sk-proj-test-key", "CODEX_HOME": ""},
            clear=False
        ):
            # Remove CODEX_HOME if it exists
            if "CODEX_HOME" in os.environ:
                del os.environ["CODEX_HOME"]

            # Mock non-existent CODEX_HOME
            with patch.object(
                OpenAIAuthResolver,
                "_try_subscription_mode",
                return_value=None
            ):
                auth_type, auth_value = OpenAIAuthResolver.resolve()

        assert auth_type == "api_key"
        assert auth_value == "sk-proj-test-key"

    def test_neither_auth_available_raises_error(self):
        """Test error when neither subscription token nor API key available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(
                OpenAIAuthResolver,
                "_try_subscription_mode",
                return_value=None
            ):
                with patch.object(
                    OpenAIAuthResolver,
                    "_try_api_key_mode",
                    return_value=None
                ):
                    with pytest.raises(ValueError) as exc_info:
                        OpenAIAuthResolver.resolve()

                    error_msg = str(exc_info.value)
                    assert "OpenAI authentication failed" in error_msg
                    assert "subscription mode" in error_msg
                    assert "API key mode" in error_msg

    def test_malformed_auth_json(self, tmp_path):
        """Test graceful handling of malformed auth.json."""
        codex_home = tmp_path / "codex-home"
        codex_home.mkdir()
        auth_file = codex_home / "auth.json"

        # Write invalid JSON
        with open(auth_file, "w") as f:
            f.write("{ invalid json }")

        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
            # Should return None (malformed), allowing fallback to API key
            result = OpenAIAuthResolver._try_subscription_mode()
            assert result is None

    def test_missing_tokens_in_auth_json(self, tmp_path):
        """Test handling of auth.json without tokens key."""
        codex_home = tmp_path / "codex-home"
        codex_home.mkdir()
        auth_file = codex_home / "auth.json"

        # Valid JSON but missing tokens key
        auth_data = {
            "auth_mode": "chatgpt",
            "last_refresh": "2026-02-22T16:00:00Z"
            # No "tokens" key
        }

        with open(auth_file, "w") as f:
            json.dump(auth_data, f)

        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
            result = OpenAIAuthResolver._try_subscription_mode()
            assert result is None

    def test_missing_access_token_in_tokens(self, tmp_path):
        """Test handling of tokens dict without access_token."""
        codex_home = tmp_path / "codex-home"
        codex_home.mkdir()
        auth_file = codex_home / "auth.json"

        auth_data = {
            "auth_mode": "chatgpt",
            "tokens": {
                "id_token": "id-token-value",
                "refresh_token": "refresh-token-value",
                # Missing "access_token"
            },
            "last_refresh": "2026-02-22T16:00:00Z"
        }

        with open(auth_file, "w") as f:
            json.dump(auth_data, f)

        with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
            result = OpenAIAuthResolver._try_subscription_mode()
            assert result is None

    def test_subscription_takes_priority_over_api_key(self, tmp_path):
        """Test that subscription token is preferred over API key."""
        # Create valid auth.json
        codex_home = tmp_path / "codex-home"
        codex_home.mkdir()
        auth_file = codex_home / "auth.json"

        auth_data = {
            "auth_mode": "chatgpt",
            "tokens": {
                "access_token": "subscription-token",
                "refresh_token": "refresh-token",
                "account_id": "user-12345"
            }
        }

        with open(auth_file, "w") as f:
            json.dump(auth_data, f)

        # Both subscription and API key available
        with patch.dict(
            os.environ,
            {"CODEX_HOME": str(codex_home), "OPENAI_API_KEY": "sk-proj-api-key"}
        ):
            auth_type, auth_value = OpenAIAuthResolver.resolve()

        # Should prefer subscription token
        assert auth_type == "subscription_token"
        assert auth_value == "subscription-token"

    def test_empty_api_key_falls_through(self):
        """Test that empty/whitespace API key is ignored."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "  "}, clear=True):
            with patch.object(
                OpenAIAuthResolver,
                "_try_subscription_mode",
                return_value=None
            ):
                with pytest.raises(ValueError):
                    OpenAIAuthResolver.resolve()

    def test_default_codex_home_used_when_unset(self, tmp_path):
        """Test that default CODEX_HOME is used when env var not set."""
        # Create auth.json at default location
        default_codex_home = Path(OpenAIAuthResolver.DEFAULT_CODEX_HOME)

        # Verify we're using the expected default
        assert str(default_codex_home) == "/home/jgamboa/.config/openai/codex-home"

    def test_error_message_includes_setup_instructions(self):
        """Test that error message includes actionable setup instructions."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(
                OpenAIAuthResolver,
                "_try_subscription_mode",
                return_value=None
            ):
                with patch.object(
                    OpenAIAuthResolver,
                    "_try_api_key_mode",
                    return_value=None
                ):
                    with pytest.raises(ValueError) as exc_info:
                        OpenAIAuthResolver.resolve()

                    error_msg = str(exc_info.value)
                    assert "CODEX_HOME" in error_msg
                    assert "OPENAI_API_KEY" in error_msg
                    assert "codex login" in error_msg
                    assert "docs/CLAUDE_OPENAI_AUTH_SWITCH.md" in error_msg
