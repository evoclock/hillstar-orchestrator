"""
Script
------
anthropic_mcp_model.py

Path
----
models/anthropic_mcp_model.py

Purpose
-------
Anthropic Claude models via MCP (Model Context Protocol) server.

Uses the anthropic_mcp_server.py MCP server to dispatch tasks via JSON-RPC.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
"""

from .mcp_model import MCPModel


class AnthropicMCPModel(MCPModel):
	"""Anthropic Claude models via MCP server."""

	def __init__(self, model_name: str, api_key: str | None = None):
		"""
		Initialize Anthropic MCP model.

		Args:
		model_name: Claude model identifier
		api_key: Optional API key (else uses ANTHROPIC_API_KEY env var)
		"""
		super().__init__(
			provider="anthropic_mcp",
			model_name=model_name,
			server_script="mcp-server/anthropic_mcp_server.py",
			api_key=api_key,
		)
