"""
Script
------
mistral_mcp_model.py

Path
----
models/mistral_mcp_model.py

Purpose
-------
Mistral AI models via MCP (Model Context Protocol) server.

Uses the mistral_mcp_server.py MCP server to dispatch tasks via JSON-RPC.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
"""

from .mcp_model import MCPModel


class MistralMCPModel(MCPModel):
    """Mistral AI models via MCP server."""

    def __init__(self, model_name: str, api_key: str | None = None):
        """
        Initialize Mistral MCP model.

        Args:
            model_name: Mistral model identifier
            api_key: Optional API key (else uses MISTRAL_API_KEY env var)
        """
        super().__init__(
            provider="mistral_mcp",
            model_name=model_name,
            server_script="mcp-server/mistral_mcp_server.py",
            api_key=api_key,
        )
