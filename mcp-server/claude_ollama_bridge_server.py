#!/usr/bin/env python3
"""
MCP Server: Fallback to Ollama Cloud Models via claude-ollama CLI

PURPOSE:
--------
When Claude API (claude.anthropic.com) hits usage limits, this server allows
Claude Code to dispatch tasks to Ollama cloud models as a fallback mechanism.

Instead of being blocked by API limits, users can seamlessly switch to models
hosted on Ollama's cloud infrastructure (devstral-2, minimax, gemini, gpt-oss, etc.)
via the claude-ollama CLI wrapper.

ARCHITECTURE:
-------------
- Wraps the claude-ollama --model <model> CLI command
- Dispatches MCP tool calls to claude-ollama binary
- claude-ollama maps model aliases (e.g., "minimax") to actual Ollama cloud models
- Unsets CLAUDECODE env var to allow nested Claude Code sessions

USAGE:
------
    python claude_ollama_bridge_server.py

This server is registered in ~/.claude.json and invoked by Claude Code when
the user selects an Ollama cloud model as the execution provider.

MODEL ALIASES (from tools/ollama/models.config):
------------------------------------------------
- minimax → minimax-m2.5:cloud (recommended for code)
- devstral-2 → devstral-2:123b-cloud (recommended for code)
- gpt-oss → gpt-oss:120b-cloud (deterministic, low temp)
- mistral-large-3 → mistral-large-3:675b-cloud (deterministic, low temp)
- gemini → gemini-3-flash-preview:cloud (creative, high temp)

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import json
import sys
import os
import subprocess
import logging
from typing import Any, Dict
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent / "mcp-server-logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "minimax_mcp.log"

# Configure logging (file only - stderr interferes with MCP protocol)
# MCP is a stdio protocol; sending logs to stderr confuses the protocol layer
# All logging goes to file for debugging without interfering with stdin/stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE)  # File logging only
    ]
)
logger = logging.getLogger("minimax-mcp")
logger.info(f"Minimax MCP server logs: {LOG_FILE}")


class MinimaxMCPServer:
    """
    MCP Server wrapper for Ollama cloud models via claude-ollama CLI.

    This server bridges Claude Code with Ollama cloud models when Claude API
    is rate-limited or unavailable. It wraps the claude-ollama CLI which:
    1. Resolves model aliases (minimax → minimax-m2.5:cloud)
    2. Launches a nested Claude Code session with that model
    3. Executes the task and returns results

    Implements core MCP methods:
    - initialize: Server startup, advertise capabilities
    - call_tool: Dispatch tasks via `claude-ollama --model <model>` CLI
    - list_tools: Advertise execute_task tool

    Process Flow:
    1. Claude Code invokes MCP tool via JSON-RPC
    2. Server receives task + optional context
    3. Server invokes: bash -c "echo <prompt> | ~/bin/claude-ollama --model minimax"
    4. claude-ollama launches nested Claude Code with specified model
    5. Returns stdout/stderr to MCP caller
    """

    def __init__(self):
        self.version = "0.1.0"
        self.tools = {
            "execute_task": {
                "description": "Execute a task with Ollama Minimax model",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Task description or code to execute"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context/environment information"
                        }
                    },
                    "required": ["task"]
                }
            }
        }

    def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP server."""
        logger.info("Minimax MCP server initializing")
        return {
            "protocolVersion": "2025-11-25",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "minimax-mcp",
                "version": self.version
            }
        }

    def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        logger.info("Listing available tools")
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
        """Execute a tool (task dispatch to minimax)."""
        logger.info(f"Tool call: {tool_name}")

        if tool_name != "execute_task":
            logger.error(f"Unknown tool requested: {tool_name}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ]
            }

        task = arguments.get("task", "")
        context = arguments.get("context", "")

        logger.debug(f"Task arguments: task_length={len(task)}, context_length={len(context)}")

        if not task:
            logger.error("Task argument is empty")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": "Task is required"
                    }
                ]
            }

        # Prepare the prompt for minimax
        prompt = task
        if context:
            prompt = f"{context}\n\n{task}"

        logger.info("Executing task with minimax")

        try:
            # Invoke claude-ollama --model minimax
            # Unset CLAUDECODE to allow subprocess to launch Claude Code safely
            env = {**os.environ}
            env.pop('CLAUDECODE', None)

            logger.debug("Starting subprocess: minimax execution")

            result = subprocess.run(
                ["bash", "-c", f"echo '{prompt}' | ~/bin/claude-ollama --model minimax"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=env
            )

            logger.info("Minimax execution completed")

            # Return the output
            output = result.stdout if result.returncode == 0 else result.stderr

            return {
                "isError": result.returncode != 0,
                "content": [
                    {
                        "type": "text",
                        "text": output or "(no output)"
                    }
                ]
            }

        except subprocess.TimeoutExpired:
            logger.error("Minimax execution timed out")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": "Minimax execution timed out after 300 seconds"
                    }
                ]
            }
        except Exception:
            logger.error("Minimax execution failed")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": "Execution failed. Please try again."
                    }
                ]
            }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.info(f"Request: {method}")

        result = None
        if method == "initialize":
            result = self.initialize()
        elif method == "tools/list":
            result = self.list_tools()
        elif method == "tools/call":
            result = self.call_tool(
                params.get("name"),
                params.get("arguments", {})
            )
        else:
            result = {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown method: {method}"
                    }
                ]
            }

        # Wrap response in JSON-RPC 2.0 format if id is present
        if request_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        return result


def main():
    """Main MCP server loop (stdio protocol)."""
    logger.info("="*70)
    logger.info("Minimax MCP server starting")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("="*70)

    server = MinimaxMCPServer()

    try:
        request_count = 0
        while True:
            # Read JSON-RPC request from stdin
            try:
                line = sys.stdin.readline()
                if not line:
                    logger.info("EOF received, shutting down gracefully")
                    break

                request_count += 1
                logger.debug(f"Request #{request_count}: {line[:100]}...")

                request = json.loads(line)
                response = server.handle_request(request)

                # Send JSON response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                logger.debug(f"Response sent for request #{request_count}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                sys.stdout.write(json.dumps({
                    "isError": True,
                    "content": [{"type": "text", "text": f"Invalid JSON: {e}"}]
                }) + "\n")
                sys.stdout.flush()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C), shutting down")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info(f"Minimax MCP server stopped after {request_count} requests")
        logger.info("="*70)


if __name__ == "__main__":
    main()
