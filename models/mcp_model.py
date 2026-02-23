"""
Script
------
mcp_model.py

Path
----
models/mcp_model.py

Purpose
-------
Base class for MCP-based model providers: Handle subprocess lifecycle and JSON-RPC communication.

Provides unified interface to MCP servers (stdio-based) with automatic initialization,
error handling, and response normalization to match AnthropicModel.call() interface.

Inputs
------
provider (str): Provider name (e.g., "anthropic_mcp")
model_name (str): Model identifier
server_script (str): Path to MCP server script
api_key (str, optional): API key for the provider

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Assumptions
-----------
- MCP server script exists and is executable
- Server implements standard MCP protocol (initialize, tools/call)
- run_with_env.sh wrapper is available in mcp-server/

Failure Modes
-------------
- Process spawn fails → RuntimeError
- MCP server crashes → RuntimeError (EOF on stdout)
- Invalid JSON response → json.JSONDecodeError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from utils.credential_redactor import redact


class MCPModel:
    """Base class for MCP-based model providers."""

    TEMPERATURE_DEFAULT = 0.00000073  # Minimize hallucinations (match AnthropicModel)

    def __init__(
        self,
        provider: str,
        model_name: str,
        server_script: str,
        api_key: str | None = None,
    ):
        """
        Initialize MCP model.

        Args:
            provider: Provider name (e.g., "anthropic_mcp")
            model_name: Model identifier (e.g., "claude-opus-4-6")
            server_script: Path to MCP server script (relative to repo root)
            api_key: Optional API key (else reads from environment)
        """
        self.provider = provider
        self.model_name = model_name
        self.server_script = server_script
        self.api_key = api_key
        self.process = None
        self._request_id = 0
        self._initialized = False
        self._api_key_missing_error = None

        # Check if API key is missing for providers that require it
        if not api_key and provider not in ["ollama_mcp"]:
            base_provider = provider.replace("_mcp", "")
            self._api_key_missing_error = (
                f"API key for '{base_provider}' not found. "
                f"Run: hillstar config\n"
                f"See: https://github.com/julen-gcs/agentic-orchestrator#provider-setup"
            )

    def _ensure_process(self) -> None:
        """Spawn MCP server subprocess if not running."""
        if self.process is not None and self.process.poll() is None:
            # Process still running
            return

        # Prepare environment
        env = os.environ.copy()

        # Set provider-specific API key if provided
        if self.api_key:
            env_var_map = {
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
                "mistral": "MISTRAL_API_KEY",
                "google_ai_studio": "GOOGLE_API_KEY",
            }
            base_provider = self.provider.replace("_mcp", "")
            env_var_name = env_var_map.get(base_provider)
            if env_var_name:
                env[env_var_name] = self.api_key

        # Determine repo root (mcp_model.py is in models/, so go up 2 levels)
        repo_root = Path(__file__).parent.parent

        # Spawn subprocess using run_with_env.sh wrapper
        try:
            self.process = subprocess.Popen(
                [
                    "bash",
                    str(repo_root / "mcp-server" / "run_with_env.sh"),
                    str(repo_root / self.server_script),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line-buffered mode
                cwd=str(repo_root),
                env=env,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to spawn MCP server: {e}")

        # Send initialize request
        self._send_initialize()
        self._initialized = True

    def _send_initialize(self) -> None:
        """Send JSON-RPC initialize request."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hillstar", "version": "1.0"},
            },
        }

        response = self._send_request(request)
        if not response or response.get("isError"):
            raise RuntimeError(f"MCP initialization failed: {response}")

    def _send_request(self, request: dict) -> dict:
        """Send JSON-RPC request and read response.

        Args:
            request: JSON-RPC request dict

        Returns:
            JSON-RPC response dict (with result or error)
        """
        if not self.process:
            raise RuntimeError("MCP process not initialized")

        # Type guards: streams are guaranteed non-None by PIPE configuration
        assert self.process.stdin is not None, "stdin should not be None"
        assert self.process.stdout is not None, "stdout should not be None"
        assert self.process.stderr is not None, "stderr should not be None"

        try:
            # Send request
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                # EOF - server crashed or closed
                stderr = self.process.stderr.read()
                # Redact any credentials from stderr before including in error
                stderr = redact(stderr)
                raise RuntimeError(
                    f"MCP server closed connection. Error output: {stderr}"
                )

            return json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON from MCP server: {e}")
        except Exception as e:
            raise RuntimeError(f"MCP communication error: {e}")

    def call(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float | None = None,
        system: str | None = None,
    ) -> dict[str, Any]:
        """Execute task via MCP server.

        Matches AnthropicModel.call() interface for compatibility.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (unused for MCP servers)
            system: System prompt (unused for MCP servers)

        Returns:
            Dictionary with response and metadata
        """
        if temperature is None:
            temperature = self.TEMPERATURE_DEFAULT

        # Check for missing API key before attempting to spawn process
        if self._api_key_missing_error:
            return {
                "output": None,
                "error": self._api_key_missing_error,
                "provider": self.provider,
            }

        try:
            # Ensure process is running
            self._ensure_process()

            # Increment request ID
            self._request_id += 1

            # Build task prompt
            task_prompt = prompt
            if system:
                task_prompt = f"{system}\n\n{prompt}"

            # Send tools/call request
            request = {
                "jsonrpc": "2.0",
                "id": self._request_id + 1,  # Offset from init request
                "method": "tools/call",
                "params": {
                    "name": "execute_task",
                    "arguments": {
                        "prompt": task_prompt,
                        "model": self.model_name,
                    },
                },
            }

            response = self._send_request(request)
            result = response.get("result", {})

            # Check for errors
            if result.get("isError"):
                error_text = "Unknown error"
                if result.get("content"):
                    error_text = result["content"][0].get("text", error_text)
                return {
                    "output": None,
                    "error": redact(error_text),
                    "provider": self.provider,
                }

            # Extract output
            output = "No output"
            if result.get("content"):
                output = result["content"][0].get("text", output)

            return {
                "output": output,
                "model": self.model_name,
                "tokens_used": 0,  # MCP servers don't return token counts
                "provider": self.provider,
            }

        except Exception as e:
            # Sanitize error message (don't expose internal details or API keys)
            error_msg = str(e)

            # First, redact any credentials that might be in the error
            error_msg = redact(error_msg)

            # Then, provide helpful message for common errors
            if "API key" in error_msg or "ANTHROPIC_API_KEY" in error_msg:
                error_msg = "API authentication failed. Check your credentials with: hillstar config --show"
            elif "MCP" in error_msg or "subprocess" in error_msg.lower():
                error_msg = f"Failed to connect to {self.provider} provider. Please try again."

            return {
                "output": None,
                "error": error_msg,
                "provider": self.provider,
            }

    def __del__(self):
        """Cleanup subprocess on deletion."""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.close()
                self.process.wait(timeout=2)
            except Exception:
                pass
