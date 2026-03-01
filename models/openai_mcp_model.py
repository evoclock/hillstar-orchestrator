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

The MCP server handles dual authentication internally:
1. Subscription mode: Uses OPENAI_CHATGPT_LOGIN_MODE=true to trigger codex exec
 - Extracts tokens from ~/.config/openai/codex-home/auth.json
 - Requires: codex login completed
2. API key mode: Uses OPENAI_API_KEY environment variable
 - Direct OpenAI SDK calls
 - Requires: OPENAI_API_KEY set

Authentication is completely transparent to this model class—
the MCP server auto-detects which mode to use.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-24
"""

from .mcp_model import MCPModel


class OpenAIMCPModel(MCPModel):
	"""OpenAI GPT models via MCP server with transparent dual authentication."""

	def __init__(self, model_name: str, api_key: str | None = None):
		"""
		Initialize OpenAI MCP model.

		Args:
		model_name: OpenAI model identifier (e.g., "gpt-5.2")
		api_key: Optional API key (else reads from OPENAI_API_KEY env var)

		The MCP server handles authentication automatically:
		- If OPENAI_CHATGPT_LOGIN_MODE=true: Uses codex exec with subscription tokens
		- If OPENAI_API_KEY is set: Uses direct OpenAI API with SDK
		- Falls back in that order

		No auth resolution is performed here—the MCP server is fully self-contained.
		"""
		super().__init__(
			provider="openai_mcp",
			model_name=model_name,
			server_script="mcp-server/openai_mcp_server.py",
			api_key=api_key,
		)
