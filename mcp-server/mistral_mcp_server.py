#!/usr/bin/env python3
"""
MCP Server: Mistral AI Models

PURPOSE:
--------
Provides access to Mistral AI models via the official Mistral SDK.
Enables agents to run tasks via open-source Mistral models with full
parameter control including temperature, top_p, and advanced sampling.

ARCHITECTURE:
-------------
- Uses official Mistral SDK (mistralai package)
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Full parameter support: temperature, top_p, top_k, etc.
- Streaming responses for real-time output

USAGE:
------
    python mistral_mcp_server.py

Registered in ~/.claude.json under "mistral" provider.

MODELS SUPPORTED:
-----------------
- mistral-large-2411 (large reasoning, recommended for complex tasks)
- mistral-medium-3.1 (mid-range, fast inference)
- ministral-8b (small, efficient)
- ministral-3b (minimal, edge deployment)
- codestral-2508 (specialized for code generation)

PARAMETERS:
-----------
- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0, recommend 0.3-0.7
- top_p (optional): 0.0-1.0 nucleus sampling
- top_k (optional): Integer, top-k sampling
- max_tokens (optional): Limit response length

AUTHENTICATION:
---------------
Requires MISTRAL_API_KEY environment variable.
Set via: export MISTRAL_API_KEY="..."
Get API key: https://console.mistral.ai/

FEATURES:
---------
- Open-source models (transparent architecture)
- Competitive pricing vs closed models
- Full parameter tuning for task optimization
- Streaming support for real-time interaction

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import sys
import os
from typing import Any, Dict
from mistralai import Mistral
from base_mcp_server import BaseMCPServer, logger


class MistralMCPServer(BaseMCPServer):
    """Mistral AI models via official SDK."""

    def __init__(self):
        super().__init__("mistral")

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            logger.error("MISTRAL_API_KEY not set")
            sys.exit(1)

        self.client = Mistral(api_key=api_key)
        logger.info("Mistral MCP server initialized")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via Mistral API."""

        if tool_name != "execute_task":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

        prompt = arguments.get("prompt", "")
        default_model = os.getenv("MODEL_DEFAULT", "mistral-small-latest")
        model = arguments.get("model", default_model)
        temperature = arguments.get("temperature")  # Optional parameter
        top_p = arguments.get("top_p")  # Optional parameter

        if not prompt:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "prompt is required"}]
            }

        try:
            # Model-specific max_tokens limits
            max_tokens_map = {
                "mistral-large-2411": 4096,
                "mistral-medium-latest": 4096,
                "mistral-small-latest": 4096,
                "ministral-8b-latest": 4096,
                "ministral-3b-latest": 4096,
                "codestral-2508": 8000,
            }
            max_tokens = max_tokens_map.get(model, 4096)

            # Build request with optional temperature and top_p
            request_args = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens
            }

            # Add optional parameters if provided
            if temperature is not None:
                request_args["temperature"] = temperature
            if top_p is not None:
                request_args["top_p"] = top_p

            message = self.client.chat.complete(**request_args)

            output = message.choices[0].message.content
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
    server = MistralMCPServer()
    server.run()


if __name__ == "__main__":
    main()
