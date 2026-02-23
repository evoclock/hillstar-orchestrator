#!/usr/bin/env python3
"""
MCP Server: OpenAI GPT Models

PURPOSE:
--------
Provides access to OpenAI GPT models via the official OpenAI API.
Enables agents to run tasks via GPT with support for reasoning models,
temperature control, and advanced sampling parameters.

ARCHITECTURE:
-------------
- Uses official OpenAI SDK (openai package)
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Model-specific parameter handling (e.g., reasoning models skip temperature)
- Streaming responses for real-time output

USAGE:
------
    python openai_mcp_server.py

Registered in ~/.claude.json under "openai_mcp" provider.

MODELS SUPPORTED:
-----------------
Standard models:
- gpt-5.2-pro (latest flagship, highest quality)
- gpt-5.2 (fast flagship variant)
- gpt-5-mini (cost-optimized, fast)
- gpt-5-nano (minimal, lowest cost)

Reasoning models (extended thinking):
- o3 (advanced reasoning, no temperature)
- o3-mini (lightweight reasoning, no temperature)

Legacy models:
- gpt-4o (previous generation)
- gpt-4-turbo (older)

PARAMETERS:
-----------
- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0 for gpt-5/gpt-4 (skipped for o3/o1)
- top_p (optional): 0.0-1.0 nucleus sampling
- max_tokens (optional): Limit response length

AUTHENTICATION:
---------------
Supports dual authentication modes (subscription-first priority):

1. Subscription tokens (preferred):
   - Set OPENAI_API_KEY to access_token from $CODEX_HOME/auth.json
   - Token auto-refreshes via Claude/Codex infrastructure

2. API keys (fallback):
   - Set OPENAI_API_KEY to sk-proj-... from platform.openai.com/api-keys
   - Requires manual refresh when expired

Both modes use OPENAI_API_KEY env variable for transport.

FEATURES:
---------
- Reasoning models for complex problem-solving
- Fastest inference times among closed models
- Extensive safety training and alignment
- Function calling support (not exposed in MCP)
- Vision capabilities in selected models

SPECIAL HANDLING:
-----------------
- o3/o3-mini: Reasoning models, no temperature parameter allowed
- gpt-5.2/gpt-5: Temperature supported (0.0-2.0)
- gpt-5-mini/nano: Lower cost, slightly lower quality

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import sys
import os
from typing import Any, Dict
from openai import OpenAI
from base_mcp_server import BaseMCPServer, logger


class OpenAIMCPServer(BaseMCPServer):
    """OpenAI GPT models via official SDK with subscription-first auth."""

    def __init__(self):
        super().__init__("openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error(
                "OPENAI_API_KEY not set. "
                "Neither subscription token nor API key available. "
                "See docs/CLAUDE_OPENAI_AUTH_SWITCH.md for setup."
            )
            sys.exit(1)

        try:
            self.client = OpenAI(api_key=api_key)
            # Note: token type (subscription vs API key) is transparent to OpenAI SDK
            logger.info("OpenAI MCP server initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            sys.exit(1)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via OpenAI API."""

        if tool_name != "execute_task":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

        prompt = arguments.get("prompt", "")
        default_model = os.getenv("MODEL_DEFAULT", "gpt-5.1")
        model = arguments.get("model", default_model)
        temperature = arguments.get("temperature")  # Optional parameter

        if not prompt:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "prompt is required"}]
            }

        try:
            # Model-specific max_completion_tokens limits
            max_tokens_map = {
                "gpt-5.2-pro": 16000,
                "gpt-5.2": 16000,
                "gpt-5-mini": 8000,
                "gpt-5-nano": 4000,
                "o3": 16000,
                "o3-mini": 16000,
                "gpt-4o": 4096,
            }
            max_tokens = max_tokens_map.get(model, 4000)

            # Build request with optional temperature
            request_args = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_completion_tokens": max_tokens
            }

            # Add temperature if provided (caller determines if model supports it)
            if temperature is not None:
                request_args["temperature"] = temperature

            response = self.client.chat.completions.create(**request_args)

            output = response.choices[0].message.content
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
    server = OpenAIMCPServer()
    server.run()


if __name__ == "__main__":
    main()
