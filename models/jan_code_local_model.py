"""
Script
------
jan_code_local_model.py

Path
----
python/hillstar/models/jan_code_local_model.py

Purpose
-------
 LOCAL JAN-CODE 4B MODEL - OPTIONAL ADVANCED SETUP

Integrates Jan-Code 4B via local llama.cpp HTTP server.
This is an OPTIONAL setup for power users with appropriate hardware.

Connects to llama.cpp server running on localhost:8081.
Uses OpenAI-compatible /v1/chat/completions endpoint (not Ollama API).
Free, local execution on GPU. Default temperature 0 for deterministic output.

 HARDWARE REQUIREMENTS (MANDATORY)
-----------------------------------
 Minimum: 16GB VRAM GPU (RTX 5070 Ti, RTX 4080, RTX 4090, A100, etc.)
 Model: Q8_0 GGUF format (~4.4GB) from Jan AI / HuggingFace
 Setup: Requires jan_code_server.sh running on port 8081
 Context: 32K tokens (tuned for 16GB VRAM with all layers on GPU)
 NOT suitable for CPU-only systems (Q8_0 quant is GPU-optimized)

Setup Instructions
------------------
1. GPU required (16GB+ VRAM)
2. Download Q8_0 GGUF model from Jan AI or HuggingFace
3. Symlink or place model at ~/models/jan-code/Jan-Code-4B-Q8_0.gguf
4. Start server: ~/bin/jan_code_server.sh
5. Verify: ~/bin/jan_code_ping.sh
6. Then use this model in workflows

Inputs
------
model_name (str): Model identifier (any value accepted by llama.cpp)
endpoint (str): llama.cpp server URL (default: http://127.0.0.1:8081)

Outputs
-------
Dictionary: {output, model, tokens_used, provider, error}

Assumptions
-----------
- llama.cpp server running on localhost:8081 (started via jan_code_server.sh)
- Server exposes OpenAI-compatible /v1/chat/completions endpoint
- Local GPU with 16GB+ VRAM available
- Q8_0 GGUF model loaded in llama.cpp

Parameters
----------
temperature: Default 0 (deterministic)
max_tokens: Configurable per call (default 4096)
system: Optional system prompt

Failure Modes
-------------
- Server not running error "llama.cpp server not responding on port 8081"
- Insufficient VRAM server crashes or OOM errors
- Model not loaded server connection fails
- Timeout requests.exceptions.Timeout
- Model file missing server startup failure

When NOT to Use This
--------------------
 No GPU or GPU < 16GB VRAM Use Ollama cloud models instead
 Need large context > 32K Use cloud API providers
 Complex multi-document review Use devstral-2:123b-cloud or Anthropic

Alternative: Use ollama cloud model minimax-m2.5:cloud or devstral-2:123b-cloud

Compliance
----------
 Local execution (no external API calls)
 Free (no licensing costs)
 Apache 2.0 licensed model
 Optional - users must explicitly set up
 Not included in standard hillstar installation

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-03-07

Last Edited
-----------
2026-03-07
"""

from __future__ import annotations

from typing import Any

import requests


class JanCodeLocalModel:
	"""LOCAL Jan-Code 4B via llama.cpp (OpenAI-compatible API).

	OPTIONAL - Requires 16GB+ VRAM GPU and Q8_0 GGUF model
	"""

	TEMPERATURE_DEFAULT = 0  # Deterministic by default

	def __init__(
		self,
		model_name: str = "jan-code",
		endpoint: str = "http://127.0.0.1:8081",
	):
		"""
		Args:
		model_name: Model identifier (llama.cpp accepts any value)
		endpoint: llama.cpp server endpoint (OpenAI-compatible)

		Warning:
		Requires 16GB+ VRAM GPU and running jan_code_server.sh
		"""
		self.model_name = model_name
		self.endpoint = endpoint
		self.api_url = f"{endpoint}/v1/chat/completions"

	def _check_server(self) -> bool:
		"""Check if llama.cpp server is running via /health endpoint."""
		try:
			response = requests.get(f"{self.endpoint}/health", timeout=2)
			return response.status_code == 200
		except requests.exceptions.RequestException:
			return False

	def call(
		self,
		prompt: str,
		max_tokens: int = 4096,
		temperature: float | None = None,
		system: str | None = None,
	) -> dict[str, Any]:
		"""
		Call Jan-Code via llama.cpp OpenAI-compatible chat completions endpoint.

		Args:
		prompt: User message content
		max_tokens: Maximum tokens to generate
		temperature: Sampling temperature (default: 0)
		system: System prompt

		Returns:
		Dictionary with response and metadata

		Note:
		Requires jan_code_server.sh running on localhost:8081
		"""
		if temperature is None:
			temperature = self.TEMPERATURE_DEFAULT

		if not self._check_server():
			return {
				"output": None,
				"error": (
					f"llama.cpp server not responding at {self.endpoint}. "
					"Start with: ~/bin/jan_code_server.sh "
					"(requires 16GB+ VRAM GPU and Q8_0 GGUF model)"
				),
				"provider": "jan_code_local",
			}

		messages: list[dict[str, str]] = []
		if system:
			messages.append({"role": "system", "content": system})
		messages.append({"role": "user", "content": prompt})

		try:
			payload = {
				"model": self.model_name,
				"messages": messages,
				"temperature": temperature,
				"max_tokens": max_tokens,
			}

			response = requests.post(self.api_url, json=payload, timeout=300)
			response.raise_for_status()

			data = response.json()
			content = (
				data.get("choices", [{}])[0]
				.get("message", {})
				.get("content", "")
				.strip()
			)
			usage = data.get("usage", {})

			return {
				"output": content,
				"model": self.model_name,
				"tokens_used": usage.get("total_tokens", 0),
				"provider": "jan_code_local",
			}
		except Exception as e:
			return {
				"output": None,
				"error": str(e),
				"provider": "jan_code_local",
			}
