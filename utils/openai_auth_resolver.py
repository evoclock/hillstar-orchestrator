"""
Script
------
openai_auth_resolver.py

Path
----
utils/openai_auth_resolver.py

Purpose
-------
Resolve OpenAI authentication with subscription-first priority.

**OpenAI-Only:** This module implements dual authentication for OpenAI MCP provider
only. Other providers (Anthropic, Mistral, Google) use API keys only.

Supports dual authentication modes:
1. Subscription mode: tokens from $CODEX_HOME/auth.json (preferred)
   - Automatic token refresh via Codex infrastructure
   - Requires: CODEX_HOME env var + codex login
2. API key mode: OPENAI_API_KEY environment variable (fallback)
   - Manual token management
   - Requires: OPENAI_API_KEY env var

Auth resolution priority:
  1. $CODEX_HOME/auth.json (subscription tokens)
  2. OPENAI_API_KEY env var (API key)
  3. Raise error if neither available

Never logs token contents (credentials redacted).
See: docs/CLAUDE_OPENAI_AUTH_SWITCH.md

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
from pathlib import Path
from typing import Tuple, Optional


class OpenAIAuthResolver:
    """Resolve OpenAI authentication with subscription-first priority."""

    DEFAULT_CODEX_HOME = "/home/jgamboa/.config/openai/codex-home"

    @staticmethod
    def resolve() -> Tuple[str, str]:
        """
        Resolve OpenAI authentication.

        Returns:
            Tuple of (auth_type, auth_value) where:
            - auth_type: "subscription_token" or "api_key"
            - auth_value: The actual token or API key

        Raises:
            ValueError: If no authentication method is available
        """
        # Try subscription mode first
        token = OpenAIAuthResolver._try_subscription_mode()
        if token:
            return ("subscription_token", token)

        # Fall back to API key mode
        api_key = OpenAIAuthResolver._try_api_key_mode()
        if api_key:
            return ("api_key", api_key)

        # Neither available
        raise ValueError(OpenAIAuthResolver._error_message())

    @staticmethod
    def _try_subscription_mode() -> Optional[str]:
        """
        Try to load subscription token from $CODEX_HOME/auth.json.

        Returns:
            Access token if found and valid, None otherwise
        """
        codex_home = os.getenv("CODEX_HOME", OpenAIAuthResolver.DEFAULT_CODEX_HOME)
        auth_file = Path(codex_home) / "auth.json"

        if not auth_file.exists():
            return None

        try:
            with open(auth_file) as f:
                auth_data = json.load(f)

            # Extract tokens dict
            tokens = auth_data.get("tokens")
            if not isinstance(tokens, dict):
                return None

            # Get access_token
            access_token = tokens.get("access_token")
            if not access_token or not isinstance(access_token, str):
                return None

            return access_token

        except (json.JSONDecodeError, IOError):
            # File exists but is malformed/unreadable
            return None

    @staticmethod
    def _try_api_key_mode() -> Optional[str]:
        """
        Try to load API key from OPENAI_API_KEY env var.

        Returns:
            API key if set, None otherwise
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and isinstance(api_key, str) and api_key.strip():
            return api_key
        return None

    @staticmethod
    def _error_message() -> str:
        """Generate actionable error message for missing auth."""
        return (
            "OpenAI authentication failed. Neither subscription mode nor API key mode available.\n\n"
            "Subscription mode (preferred):\n"
            "  1. Set: export CODEX_HOME=/home/jgamboa/.config/openai/codex-home\n"
            "  2. Ensure: $CODEX_HOME/auth.json exists with valid tokens\n"
            "  3. Run: codex login\n\n"
            "API key mode (fallback):\n"
            "  1. Set: export OPENAI_API_KEY=sk-proj-...\n"
            "  2. Get key: https://platform.openai.com/api-keys\n\n"
            "See: docs/CLAUDE_OPENAI_AUTH_SWITCH.md"
        )
