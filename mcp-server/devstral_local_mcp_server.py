#!/usr/bin/env python3
"""
MCP Server: Devstral Local (llama.cpp HTTP Server)

PURPOSE:
--------
Provides access to Devstral Small 2 24B model running locally on GPU via llama.cpp
HTTP server. Enables on-device inference without cloud dependencies or API costs.
Ideal for deterministic code-writing tasks with tight temperature control.

ARCHITECTURE:
-------------
- HTTP client wrapper around llama.cpp server
- Connects to localhost:8080 (standard llama.cpp endpoint)
- Single tool: execute_task (send prompt to local model)
- Full parameter support: temperature, top_p, top_k, etc.

USAGE:
------
    1. Start llama.cpp server with Devstral model:
       ./llama-server -m devstral-small-2-24b.gguf -ngl 99 -t 8

    2. Run this MCP server:
       python devstral_local_mcp_server.py

Registered in ~/.claude.json under "devstral_local" provider.

MODEL:
------
- Devstral Small 2 24B (24 billion parameters)
- Quantized formats supported: q4, q5, q6, q8
- Recommended for: code generation, analysis, deterministic tasks
- Device: GPU recommended (NVIDIA/AMD), CPU fallback supported
- Context: 8K tokens default (configurable)

REQUIREMENTS:
-------------
- llama.cpp installed and built with CUDA/ROCm support
- Devstral model file (.gguf format)
- ~15GB VRAM for full quantization (q4 ~6GB)
- Local server running on http://127.0.0.1:8080

PARAMETERS:
-----------
- prompt (required): Task description
- model (required): "devstral_local" or model path
- temperature (optional): 0.0-2.0, recommend 0.3 for code
- top_p (optional): 0.0-1.0 nucleus sampling
- top_k (optional): Integer, top-k sampling

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import requests
from typing import Any, Dict
from base_mcp_server import BaseMCPServer, logger


class DevstralLocalMCPServer(BaseMCPServer):
    """Devstral Small 2 24B via llama.cpp HTTP server."""

    def __init__(self):
        super().__init__("devstral_local")
        self.endpoint = "http://127.0.0.1:8080"
        self.model = "devstral-small-2-24b"
        logger.info(f"Devstral Local MCP server initialized (endpoint: {self.endpoint})")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via devstral_server.sh HTTP API."""

        if tool_name != "execute_task":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

        prompt = arguments.get("prompt", "")

        if not prompt:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "prompt is required"}]
            }

        temperature = arguments.get("temperature")  # Optional parameter
        top_p = arguments.get("top_p")  # Optional parameter

        try:
            # Format prompt in Devstral instruction style
            formatted_prompt = f"[INST] {prompt} [/INST]"

            # Call llama.cpp /completion endpoint
            request_payload = {
                "prompt": formatted_prompt,
                "n_predict": 8192,
                "stop": ["[INST]", "</s>"]
            }

            # Add optional temperature and top_p if provided
            if temperature is not None:
                request_payload["temperature"] = temperature
            if top_p is not None:
                request_payload["top_p"] = top_p

            response = requests.post(
                f"{self.endpoint}/completion",
                json=request_payload,
                timeout=300
            )
            response.raise_for_status()

            result = response.json()
            output = result.get("content", "")

            logger.info("Task completed successfully")
            return {
                "isError": False,
                "content": [{"type": "text", "text": output}]
            }

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Devstral service")
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
    server = DevstralLocalMCPServer()
    server.run()


if __name__ == "__main__":
    main()
