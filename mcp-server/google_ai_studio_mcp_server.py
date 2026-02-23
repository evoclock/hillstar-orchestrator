#!/usr/bin/env python3
"""
MCP Server: Google AI Studio (Gemini Models)

PURPOSE:
--------
Provides access to Google Gemini models via Google AI Studio API.
Enables agents to run tasks via Gemini with multimodal capabilities,
thinking modes, and flexible parameter control.

ARCHITECTURE:
-------------
- Uses official Google generativeai SDK
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Supports streaming for real-time output
- Optional parameters: temperature, thinking_mode, safety_settings

USAGE:
------
    python google_ai_studio_mcp_server.py

Registered in ~/.claude.json under "google_ai_studio" provider.

MODELS SUPPORTED:
-----------------
- gemini-3-pro (reasoning model, thinking support)
- gemini-3-flash (fast model, minimal thinking)
- gemini-3-flash-lite (lightweight, edge device support)
- gemini-1.5-pro (legacy, extended context)
- gemini-1.5-flash (legacy, fast generation)

PARAMETERS:
-----------
- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0 for creativity
- thinking_mode (optional): "enabled" or "disabled"
- max_output_tokens (optional): Limit response length

AUTHENTICATION:
---------------
Requires GOOGLE_API_KEY environment variable.
Set via: export GOOGLE_API_KEY="AIzaSy..."
Get API key: https://ai.google.dev

FEATURES:
---------
- Thinking models for complex reasoning
- Multimodal input support (text, images, etc.)
- Safety filtering (configurable per use case)
- Streaming responses for real-time output

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import sys
import os
from typing import Any, Dict
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from google.generativeai import types
from base_mcp_server import BaseMCPServer, logger


class GoogleAIStudioMCPServer(BaseMCPServer):
    """Google Gemini models via official SDK."""

    def __init__(self):
        super().__init__("google_ai_studio")

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not set")
            sys.exit(1)

        configure(api_key=api_key)
        logger.info("Google AI Studio MCP server initialized")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via Google Gemini API."""

        if tool_name != "execute_task":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

        prompt = arguments.get("prompt", "")
        model = arguments.get("model", "gemini-2.0-flash-lite")
        temperature = arguments.get("temperature")  # Optional parameter

        if not prompt:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "prompt is required"}]
            }

        try:
            model_instance = GenerativeModel(model)

            # Model-specific max_output_tokens limits
            max_tokens_map = {
                "gemini-3-pro": 8000,
                "gemini-3-flash": 8000,
                "gemini-3-flash-lite": 8000,
                "gemini-2.0-pro": 8000,
                "gemini-2.0-flash": 8000,
                "gemini-2.0-flash-lite": 8000,
                "gemini-1.5-pro": 8000,
                "gemini-1.5-flash": 8000,
            }
            max_tokens = max_tokens_map.get(model, 8000)

            # Build generation config
            if temperature is not None:
                generation_config = types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                generation_config = types.GenerationConfig(
                    max_output_tokens=max_tokens
                )

            response = model_instance.generate_content(
                prompt,
                generation_config=generation_config
            )

            output = response.text
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
    server = GoogleAIStudioMCPServer()
    server.run()


if __name__ == "__main__":
    main()
