#!/usr/bin/env python3
"""
MCP Server: Jan-Code Local (llama.cpp HTTP Server)

PURPOSE:
--------
Provides access to Jan-Code 4B model running locally on GPU via llama.cpp
HTTP server. A lightweight, fast code model for agent subtasks, prereq
checks, and bounded single-document tasks. Complements cloud models by
handling the cheap-tier work entirely on-device.

ARCHITECTURE:
-------------
- HTTP client wrapper around llama.cpp server (OpenAI-compatible API)
- Connects to localhost:8081 (jan-code dedicated endpoint)
- Single tool: execute_task (send prompt to local model)
- Full parameter support: temperature, top_p, top_k, max_tokens
- Uses /v1/chat/completions (not /completion) for proper Qwen3 chat format

USAGE:
------
 1. Start llama.cpp server with jan-code model:
    jan_code_server.sh

 2. Run this MCP server:
    python jan_code_local_mcp_server.py

Registered in ~/.claude.json under "jan-code" provider.

MODEL:
------
- Jan-Code 4B (4.4 billion parameters, Qwen3 architecture)
- Quantization: Q8_0 (highest quality)
- Strengths: code generation, editing, debugging, agent subtasks
- Context: 32K tokens (tuned for 16 GB VRAM with all layers on GPU)
- Device: NVIDIA RTX 5070 Ti (pinned by UUID)

REQUIREMENTS:
-------------
- llama.cpp installed and built with CUDA support
- Jan-Code GGUF model file
- ~14 GB VRAM (4.4 GB weights + 9 GB KV cache at 32K context)
- Local server running on http://127.0.0.1:8081

PARAMETERS:
-----------
- prompt (required): Task description
- model (required): "jan_code_local" or model path
- temperature (optional): 0.0-2.0, recommend 0 for deterministic tasks
- top_p (optional): 0.0-1.0 nucleus sampling
- max_tokens (optional): Max tokens to generate (default 4096)

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import requests
from typing import Any, Dict
from base_mcp_server import BaseMCPServer, logger


class JanCodeLocalMCPServer(BaseMCPServer):
	"""Jan-Code 4B via llama.cpp HTTP server (OpenAI-compatible API)."""

	def __init__(self):
		super().__init__("jan-code")
		self.endpoint = "http://127.0.0.1:8081"
		self.model = "Jan-Code-4B-Q8_0.gguf"
		logger.info(f"Jan-Code Local MCP server initialized (endpoint: {self.endpoint})")

	def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute task via jan_code_server.sh HTTP API."""

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

		temperature = arguments.get("temperature")
		top_p = arguments.get("top_p")
		max_tokens = arguments.get("max_tokens", 4096)

		try:
			# Build OpenAI-compatible chat request
			request_payload: Dict[str, Any] = {
				"model": self.model,
				"messages": [
					{"role": "user", "content": prompt}
				],
				"max_tokens": max_tokens,
				"stop": ["<|im_end|>"]
			}

			if temperature is not None:
				request_payload["temperature"] = temperature
			if top_p is not None:
				request_payload["top_p"] = top_p

			response = requests.post(
				f"{self.endpoint}/v1/chat/completions",
				json=request_payload,
				timeout=300
			)
			response.raise_for_status()

			result = response.json()
			choices = result.get("choices", [])
			if choices:
				output = choices[0].get("message", {}).get("content", "")
			else:
				output = ""

			logger.info("Task completed successfully")
			return {
				"isError": False,
				"content": [{"type": "text", "text": output}]
			}

		except requests.exceptions.ConnectionError:
			logger.error("Cannot connect to Jan-Code service on port 8081")
			return {
				"isError": True,
				"content": [{"type": "text", "text": "Cannot connect to Jan-Code service. Is jan_code_server.sh running?"}]
			}
		except Exception:
			logger.error("API call failed")
			return {
				"isError": True,
				"content": [{"type": "text", "text": "API call failed. Please try again."}]
			}


def main():
	server = JanCodeLocalMCPServer()
	server.run()


if __name__ == "__main__":
	main()
