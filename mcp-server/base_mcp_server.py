#!/usr/bin/env python3
"""
MCP Server: Base Class for All Providers

PURPOSE:
--------
Provides common JSON-RPC 2.0 protocol handling for all MCP servers.
Implements initialization, tool listing, and request routing.
All provider-specific servers inherit from this base class.

ARCHITECTURE:
-------------
- JSON-RPC 2.0 protocol over stdin/stdout
- Tool registry system (subclasses add tools)
- Request dispatching to appropriate handlers
- Logging to ~/.hillstar/mcp-logs/mcp.log

PROTOCOL METHODS:
-----------------
- initialize: Handshake with client, returns server info
- tools/list: Return available tools and schemas
- tools/call: Execute a tool with arguments

USAGE:
------
This is a base class. Individual provider servers extend it:
 class AnthropicMCPServer(BaseMCPServer):
 def call_tool(self, tool_name, arguments):
 # Provider-specific implementation

LOGGING:
--------
- Location: ~/.hillstar/mcp-logs/mcp.log
- Level: INFO
- Format: timestamp - name - level - message

SUBCLASSES:
-----------
- AnthropicMCPServer: Claude models via Anthropic SDK
- OpenAIMCPServer: GPT models via OpenAI SDK
- MistralMCPServer: Mistral models via Mistral SDK
- GoogleAIStudioMCPServer: Gemini via Google SDK
- OllamaMCPServer: Local Ollama models
- DevstralLocalMCPServer: Devstral via llama.cpp
- FileOperationsMCPServer: File read/write operations

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import json
import sys
import logging
from typing import Any, Dict, Optional
from pathlib import Path

# Logging setup
LOG_DIR = Path.home() / ".hillstar" / "mcp-logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[logging.FileHandler(LOG_DIR / "mcp.log")]
)
logger = logging.getLogger(__name__)


class BaseMCPServer:
	"""Base MCP server - all providers inherit from this."""

	def __init__(self, provider_name: str):
		self.version = "1.0.0"
		self.provider_name = provider_name
		self.tools = {
			"execute_task": {
				"description": f"Execute a task with {provider_name}",
				"inputSchema": {
					"type": "object",
					"properties": {
						"prompt": {
							"type": "string",
							"description": "The prompt/task to execute"
						},
						"model": {
							"type": "string",
							"description": f"Which {provider_name} model to use"
						}
					},
					"required": ["prompt", "model"]
				}
			}
		}

	def initialize(self) -> Dict[str, Any]:
		"""MCP initialization."""
		logger.info(f"Initializing {self.provider_name} MCP server")
		return {
			"protocolVersion": "2025-11-25",
			"capabilities": {"tools": {}},
			"serverInfo": {
				"name": f"{self.provider_name}-mcp",
				"version": self.version
			}
		}

	def list_tools(self) -> Dict[str, Any]:
		"""List available tools."""
		return {
			"tools": [
				{
					"name": tool_name,
					"description": tool_info["description"],
					"inputSchema": tool_info["inputSchema"]
				}
				for tool_name, tool_info in self.tools.items()
			]
		}

	def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute a tool. Subclasses override this."""
		raise NotImplementedError("Subclasses must implement call_tool()")

	def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		"""Route MCP requests. Returns None for notifications (no response)."""
		method = request.get("method")
		params = request.get("params", {})
		request_id = request.get("id")

		# Notifications (no id, method starts with "notifications/") get no response.
		# Per JSON-RPC 2.0 + MCP spec: client sends notifications/initialized after
		# handshake; any response to a notification violates protocol and clients
		# disconnect.
		if request_id is None or (method or "").startswith("notifications/"):
			return None

		result = None
		if method == "initialize":
			result = self.initialize()
		elif method == "tools/list":
			result = self.list_tools()
		elif method == "tools/call":
			result = self.call_tool(params.get("name"), params.get("arguments", {}))
		else:
			return {
				"jsonrpc": "2.0",
				"id": request_id,
				"error": {
					"code": -32601,
					"message": f"Method not found: {method}"
				}
			}

		return {
			"jsonrpc": "2.0",
			"id": request_id,
			"result": result
		}

	def run(self):
		"""Main MCP event loop."""
		logger.info(f"{self.provider_name} MCP server starting")
		try:
			while True:
				line = sys.stdin.readline()
				if not line:
					break
				line = line.strip()
				if not line:
					continue

				try:
					request = json.loads(line)
				except json.JSONDecodeError as e:
					logger.warning(f"Skipping malformed JSON line: {e}")
					continue

				response = self.handle_request(request)

				# Notifications return None; do not write to stdout.
				if response is not None:
					sys.stdout.write(json.dumps(response) + "\n")
					sys.stdout.flush()

		except KeyboardInterrupt:
			logger.info("Received interrupt, shutting down")
		except Exception as e:
			logger.error(f"Error: {e}", exc_info=True)
			sys.exit(1)
		finally:
			logger.info(f"{self.provider_name} MCP server stopped")
