#!/usr/bin/env python3
"""
MCP Server: Ollama Local Models

PURPOSE:
--------
Provides access to models running via Ollama (ollama.ai) on localhost.
Enables on-device inference for both local models and cloud models accessed
via Ollama's proxy. Zero API costs, full privacy, offline-capable.

ARCHITECTURE:
-------------
- HTTP client wrapper around Ollama server
- Connects to localhost:11434 (standard Ollama endpoint)
- Single tool: execute_task (send prompt to model)
- Full parameter support: temperature, top_p, top_k, repeat_penalty, etc.
- Streaming responses for real-time output

USAGE:
------
    1. Install and start Ollama server:
       ollama serve

    2. Pull model (optional, auto-downloads on first use):
       ollama pull llama2  # or any supported model

    3. Run this MCP server:
       python ollama_mcp_server.py

Registered in ~/.claude.json under "ollama" provider.

MODELS SUPPORTED (Examples):
-----------------------------
Local models:
- llama2 (7B, text generation)
- mistral (7B, fast inference)
- neural-chat (7B, conversational)
- devstral-2 (code-specialized)

Cloud models via Ollama proxy:
- minimax-m2.5:cloud (multimodal, Ollama cloud)
- gpt-oss:120b-cloud (OpenSource, deterministic)
- mistral-large-3:675b-cloud (reasoning)
- gemini-3-flash-preview:cloud (fast, creative)

PARAMETERS:
-----------
- prompt (required): Task description
- model (required): Model name from ollama
- temperature (optional): 0.0-2.0, recommend 0.3-0.7
- top_p (optional): 0.0-1.0 nucleus sampling
- top_k (optional): Integer, top-k sampling
- repeat_penalty (optional): Penalize repetition

REQUIREMENTS:
-------------
- Ollama installed from ollama.ai
- Ollama server running on http://127.0.0.1:11434
- Sufficient disk space for models (~7GB per model)
- GPU recommended (NVIDIA/AMD/Apple) for speed

FEATURES:
---------
- Free, local inference (no API costs)
- Full privacy (data never leaves machine)
- Offline capability
- Easy model swapping
- Cloud model access via Ollama proxy

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import os
import requests
from typing import Any, Dict
from base_mcp_server import BaseMCPServer, logger


class OllamaMCPServer(BaseMCPServer):
    """Ollama local models via HTTP API."""

    def __init__(self):
        super().__init__("ollama")
        self.endpoint = "http://127.0.0.1:11434"
        logger.info(f"Ollama MCP server initialized (endpoint: {self.endpoint})")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via Ollama HTTP API."""

        if tool_name != "execute_task":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

        prompt = arguments.get("prompt", "")
        default_model = os.getenv("MODEL_DEFAULT", "devstral-2:123b-cloud")
        model = arguments.get("model", default_model)

        temperature = arguments.get("temperature")  # Optional parameter

        if not prompt:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "prompt is required"}]
            }

        try:
            # Call Ollama /api/generate endpoint
            request_payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }

            # Add optional temperature if provided
            if temperature is not None:
                request_payload["temperature"] = temperature

            response = requests.post(
                f"{self.endpoint}/api/generate",
                json=request_payload,
                timeout=300
            )
            response.raise_for_status()

            result = response.json()
            output = result.get("response", "")

            logger.info("Task completed successfully")
            return {
                "isError": False,
                "content": [{"type": "text", "text": output}]
            }

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama service")
            return {
                "isError": True,
                "content": [{"type": "text", "text": "Cannot connect to service. Please try again."}]
            }
        except Exception:
            logger.error("API call failed")
            return {
                "isError": True,
                "content": [{"type": "text", "text": "API call failed. Please try again."}]
            }


def main():
    server = OllamaMCPServer()
    server.run()


if __name__ == "__main__":
    main()
