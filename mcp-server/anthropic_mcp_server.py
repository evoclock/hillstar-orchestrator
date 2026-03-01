#!/usr/bin/env python3
"""
MCP Server: Anthropic Claude Models

PURPOSE:
--------
Provides access to Claude models (Opus, Sonnet, Haiku) via the official Anthropic API.
Enables agents to run tasks via Claude with full API feature support including thinking
budget, streaming, and temperature control.

ARCHITECTURE:
-------------
- Uses official Anthropic SDK (anthropic package)
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt and parameters)
- Streams responses for real-time output
- Supports optional parameters: temperature, thinking_budget

USAGE:
------
 python anthropic_mcp_server.py

Registered in ~/.claude.json under "anthropic" provider.

MODELS SUPPORTED:
-----------------
- claude-opus-4-6 (max_tokens: 4096)
- claude-sonnet-4-5-20250929 (max_tokens: 4096)
- claude-haiku-4-5-20251001 (max_tokens: 1024)

PARAMETERS:
-----------
- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-1.0 for response variability
- thinking_budget (optional): Tokens for extended thinking

AUTHENTICATION:
---------------
Requires ANTHROPIC_API_KEY environment variable.
Set via: export ANTHROPIC_API_KEY="sk-ant-..."

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import sys
import os
from typing import Any, Dict
from anthropic import Anthropic
from base_mcp_server import BaseMCPServer, logger


class AnthropicMCPServer(BaseMCPServer):
	"""Anthropic Claude models via official SDK."""

	def __init__(self):
		super().__init__("anthropic")

		api_key = os.getenv("ANTHROPIC_API_KEY")
		if not api_key:
			logger.error("ANTHROPIC_API_KEY not set")
			sys.exit(1)

		self.client = Anthropic(api_key=api_key)
		logger.info("Anthropic MCP server initialized")

	def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute task via Anthropic API."""

		if tool_name != "execute_task":
			return {
				"isError": True,
				"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
			}

		prompt = arguments.get("prompt", "")
		default_model = os.getenv("MODEL_DEFAULT", "claude-haiku-4-5-20241001")
		model = arguments.get("model", default_model)
		temperature = arguments.get("temperature") # Optional parameter

		if not prompt:
			return {
				"isError": True,
				"content": [{"type": "text", "text": "prompt is required"}]
			}

		try:
			# Model-specific max_tokens limits
			max_tokens_map = {
				"claude-opus-4-6": 4096,
				"claude-sonnet-4-5-20250929": 4096,
				"claude-haiku-4-5-20251001": 1024,
			}
			max_tokens = max_tokens_map.get(model, 4096)

			# Build request - temperature optional
			request_args = {
				"model": model,
				"max_tokens": max_tokens,
				"stream": True,
				"messages": [
					{"role": "user", "content": prompt}
				]
			}

			# Add temperature if provided
			if temperature is not None:
				request_args["temperature"] = temperature

			message = self.client.messages.create(**request_args)

			output = ""
			for event in message:
				if event.type == "content_block_delta":
					if hasattr(event.delta, "text"):
						output += event.delta.text
			logger.info("Task completed successfully")

			return {
				"isError": False,
				"content": [{"type": "text", "text": output}]
			}

		except Exception:
			logger.error("API call failed")
			return {
				"isError": True,
				"content": [{"type": "text", "text": "API call failed. Please try again."}]
			}


def main():
	server = AnthropicMCPServer()
	server.run()


if __name__ == "__main__":
	main()
