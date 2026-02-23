"""
Script
------
openai_mcp_model.py

Path
----
models/openai_mcp_model.py

Purpose
-------
OpenAI GPT models via MCP (Model Context Protocol) server.

Uses the openai_mcp_server.py MCP server to dispatch tasks via JSON-RPC.

Supports dual authentication with subscription-first priority:
1. Subscription tokens from $CODEX_HOME/auth.json (preferred)
2. API key from OPENAI_API_KEY env var (fallback)

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-22
"""

from .mcp_model import MCPModel
from utils.openai_auth_resolver import OpenAIAuthResolver


class OpenAIMCPModel(MCPModel):
    """OpenAI GPT models via MCP server with subscription-first auth."""

    def __init__(self, model_name: str, api_key: str | None = None):
        """
        Initialize OpenAI MCP model with auth resolution.

        Args:
            model_name: OpenAI model identifier
            api_key: Optional API key (else resolves via CODEX_HOME or env var)

        Auth resolution (subscription-first):
          1. $CODEX_HOME/auth.json (subscription tokens)
          2. OPENAI_API_KEY env var (API key)
          3. Raises error if neither available
        """
        # If api_key not provided, resolve it (try subscription first, then API key)
        if not api_key:
            try:
                auth_type, auth_value = OpenAIAuthResolver.resolve()
                api_key = auth_value
            except ValueError as e:
                # Pass error message to parent for later error handling
                api_key = None
                self._auth_error = str(e)
        else:
            self._auth_error = None

        super().__init__(
            provider="openai_mcp",
            model_name=model_name,
            server_script="mcp-server/openai_mcp_server.py",
            api_key=api_key,
        )

        # Override the generic error message with subscription-aware one
        if not api_key and not self._auth_error:
            self._api_key_missing_error = OpenAIAuthResolver._error_message()
        elif self._auth_error:
            self._api_key_missing_error = self._auth_error
