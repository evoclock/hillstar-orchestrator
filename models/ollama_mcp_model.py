"""
Script
------
ollama_mcp_model.py

Path
----
models/ollama_mcp_model.py

Purpose
-------
Ollama (local models) via MCP (Model Context Protocol) server.

Uses the ollama_mcp_server.py MCP server to dispatch tasks to local Ollama models via JSON-RPC.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
"""

from .mcp_model import MCPModel


class OllamaMCPModel(MCPModel):
	"""Ollama local models via MCP server."""

	def __init__(self, model_name: str):
		"""
		Initialize Ollama MCP model.

		Args:
		model_name: Ollama model identifier (e.g., "devstral-small-2:24b")
		"""
		super().__init__(
			provider="ollama_mcp",
			model_name=model_name,
			server_script="mcp-server/ollama_mcp_server.py",
			api_key=None, # Ollama doesn't require API key
		)
