#!/usr/bin/env python3
"""
MCP Server: OpenAI GPT Models with Dual Authentication

PURPOSE:
--------
Provides access to OpenAI GPT models via official SDK (API key mode) or
Codex CLI wrapper (subscription token mode). Enables agents to run tasks
via GPT with support for reasoning models, temperature control, and advanced
sampling parameters.

ARCHITECTURE:
-------------
- Dual authentication: API key mode (direct SDK) or subscription mode (via codex CLI)
- Uses official OpenAI SDK (openai package) for API key mode
- Uses codex exec CLI wrapper for ChatGPT subscription token mode
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Model-specific parameter handling (e.g., reasoning models skip temperature)
- Automatic mode selection and fallback to API key if subscription unavailable

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

AUTHENTICATION (Dual Mode):
---------------------------
1. SUBSCRIPTION MODE (preferred if available):
 - Requires OPENAI_CHATGPT_LOGIN_MODE=true environment variable
 - Uses ChatGPT subscription token from ~/.config/openai/codex-home/auth.json
 - Executes via: codex exec --model <model> "<prompt>"
 - Requires: codex CLI installed and `codex login` completed

2. API KEY MODE (fallback):
 - Uses OPENAI_API_KEY environment variable (sk-proj-*)
 - Direct calls to OpenAI API via official SDK
 - Fallback if subscription mode unavailable or codex exec fails

CODEX_HOME CONFIGURATION:
------------------------
Set up canonical directory:
 mkdir -p ~/.config/openai/codex-home
 chmod 700 ~/.config/openai/codex-home

For subscription mode, run:
 codex login
 (Select ChatGPT sign-in to create auth.json with tokens)

Environment variables:
 CODEX_HOME=/home/jgamboa/.config/openai/codex-home (optional, auto-detected)
 OPENAI_CHATGPT_LOGIN_MODE=true (enables subscription mode)
 OPENAI_API_KEY=sk-proj-... (API key fallback)

PARAMETERS:
-----------
- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0 for gpt-5/gpt-4 (skipped for o3/o1)
- top_p (optional): 0.0-1.0 nucleus sampling
- max_tokens (optional): Limit response length

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
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional
from openai import OpenAI
from base_mcp_server import BaseMCPServer, logger


class OpenAIMCPServer(BaseMCPServer):
	"""OpenAI GPT models via official SDK or Codex CLI wrapper."""

	def __init__(self):
		super().__init__("openai")

		# Check if ChatGPT subscription mode is enabled
		use_subscription = os.getenv("OPENAI_CHATGPT_LOGIN_MODE", "false").lower() == "true"
		self.subscription_token = None
		self.client = None
		self.auth_mode = None

		if use_subscription:
			# Try to get ChatGPT subscription token for codex CLI mode
			self.subscription_token = self._get_subscription_token()
			if self.subscription_token:
				logger.info("Using ChatGPT subscription token (codex CLI) authentication")
				self.auth_mode = "subscription"
				# Don't initialize OpenAI client in subscription mode
				logger.info("OpenAI MCP server initialized in subscription token mode")
				return

		# Fall back to API key mode
		api_key = os.getenv("OPENAI_API_KEY")
		if not api_key:
			logger.error(
				"OPENAI_API_KEY not set and ChatGPT subscription token unavailable. "
				"Set OPENAI_API_KEY or enable OPENAI_CHATGPT_LOGIN_MODE=true with codex login."
			)
			sys.exit(1)

		self.client = OpenAI(api_key=api_key)
		self.auth_mode = "api_key"
		logger.info("OpenAI MCP server initialized in API key mode")

	@staticmethod
	def _get_subscription_token() -> Optional[str]:
		"""Extract ChatGPT subscription token from CODEX_HOME/auth.json.

		Tokens are stored in auth.json under tokens.access_token (JWT format).
		Checks canonical location first (~/.config/openai/codex-home), then falls back
		to CODEX_HOME env var or ~/.codex.
		"""
		# Priority 1: Canonical CODEX_HOME location
		canonical_codex_home = Path.home() / ".config" / "openai" / "codex-home"
		if canonical_codex_home.exists():
			auth_file = canonical_codex_home / "auth.json"
			if auth_file.exists():
				try:
					with open(auth_file) as f:
						auth_data = json.load(f)
					token = auth_data.get("tokens", {}).get("access_token")
					if token:
						logger.debug(f"Loaded subscription token from {auth_file}")
						return token
				except Exception as e:
					logger.warning(f"Failed to load token from {auth_file}: {e}")

		# Priority 2: CODEX_HOME environment variable
		codex_home = os.getenv("CODEX_HOME")
		if codex_home:
			auth_file = Path(codex_home) / "auth.json"
			if auth_file.exists():
				try:
					with open(auth_file) as f:
						auth_data = json.load(f)
					token = auth_data.get("tokens", {}).get("access_token")
					if token:
						logger.debug(f"Loaded subscription token from {auth_file}")
						return token
				except Exception as e:
					logger.warning(f"Failed to load token from {auth_file}: {e}")

		# Priority 3: Legacy ~/.codex location
		legacy_codex_home = Path.home() / ".codex"
		if legacy_codex_home.exists():
			auth_file = legacy_codex_home / "auth.json"
			if auth_file.exists():
				try:
					with open(auth_file) as f:
						auth_data = json.load(f)
					token = auth_data.get("tokens", {}).get("access_token")
					if token:
						logger.debug(f"Loaded subscription token from {auth_file}")
						return token
				except Exception as e:
					logger.warning(f"Failed to load token from {auth_file}: {e}")

		logger.debug("Subscription token not found in any location")
		return None

	def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute task via OpenAI API (api_key mode) or codex CLI (subscription mode)."""

		if tool_name != "execute_task":
			return {
				"isError": True,
				"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
			}

		prompt = arguments.get("prompt", "")
		default_model = os.getenv("MODEL_DEFAULT", "gpt-5.2")
		model = arguments.get("model", default_model)
		temperature = arguments.get("temperature") # Optional parameter

		if not prompt:
			return {
				"isError": True,
				"content": [{"type": "text", "text": "prompt is required"}]
			}

		# Execute based on authentication mode
		if self.auth_mode == "subscription":
			return self._execute_via_codex_cli(model, prompt)
		else:
			return self._execute_via_api_key(model, prompt, temperature)

	def _execute_via_codex_cli(self, model: str, prompt: str) -> Dict[str, Any]:
		"""Execute task via codex CLI wrapper (subscription token mode)."""
		try:
			# Build codex exec command: codex exec --model <model> "<prompt>"
			cmd = ["codex", "exec", "--model", model, prompt]

			logger.info(f"Executing via codex CLI with model {model}")
			start_time = time.time()

			result = subprocess.run(
				cmd,
				capture_output=True,
				text=True,
				timeout=60 # 60 second timeout for codex CLI
			)

			elapsed = time.time() - start_time
			logger.info(f"Codex CLI completed in {elapsed:.2f}s")

			if result.returncode == 0:
				output = result.stdout.strip()
				if not output and result.stderr:
					# Sometimes output is on stderr
					output = result.stderr.strip()
				return {
					"isError": False,
					"content": [{"type": "text", "text": output}]
				}
			else:
				error_msg = result.stderr or f"codex exec returned {result.returncode}"
				logger.error(f"Codex CLI error: {error_msg}")
				return {
					"isError": True,
					"content": [{"type": "text", "text": f"Codex CLI failed: {error_msg}"}]
				}

		except subprocess.TimeoutExpired:
			logger.error("Codex CLI timeout (60s)")
			return {
				"isError": True,
				"content": [{"type": "text", "text": "Codex CLI timeout. Request took longer than 60 seconds."}]
			}
		except FileNotFoundError:
			logger.error("codex CLI not found. Install with: pip install codex-cli")
			return {
				"isError": True,
				"content": [{"type": "text", "text": "codex CLI not installed. Run: pip install codex-cli"}]
			}
		except Exception as e:
			logger.error(f"Codex CLI execution failed: {e}")
			return {
				"isError": True,
				"content": [{"type": "text", "text": f"Codex CLI error: {str(e)}"}]
			}

	def _execute_via_api_key(
		self, model: str, prompt: str, temperature: Optional[float] = None
	) -> Dict[str, Any]:
		"""Execute task via OpenAI API (API key mode)."""
		# Type assertion: client must be initialized when in api_key mode
		assert self.client is not None, "OpenAI client not initialized (expected in api_key mode)"

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

			logger.info(f"Executing via OpenAI API with model {model}")
			response = self.client.chat.completions.create(**request_args)

			output = response.choices[0].message.content
			logger.info("Task completed successfully")

			return {
				"isError": False,
				"content": [{"type": "text", "text": output}]
			}

		except Exception as e:
			logger.error(f"API call failed: {e}")
			return {
				"isError": True,
				"content": [{"type": "text", "text": f"API call failed: {str(e)}"}]
			}


def main():
	server = OpenAIMCPServer()
	server.run()


if __name__ == "__main__":
	main()
