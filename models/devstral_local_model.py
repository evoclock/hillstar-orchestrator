"""
Script
------
devstral_local_model.py

Path
----
python/hillstar/models/devstral_local_model.py

Purpose
-------
 LOCAL DEVSTRAL-SMALL-2 MODEL - OPTIONAL ADVANCED SETUP

Integrates Devstral-Small-2 via local llama.cpp HTTP server.
This is an OPTIONAL setup for power users with appropriate hardware.

Connects to llama.cpp server running on localhost:8080.
Uses OpenAI-compatible /v1/chat/completions endpoint (not Ollama API).
Free, local execution on GPU. Default temperature 0.00000073 minimizes hallucination.

 HARDWARE REQUIREMENTS (MANDATORY)
-----------------------------------
 Minimum: 16GB VRAM GPU (RTX 4080, RTX 4090, A100, etc.)
 Model: Quantized GGUF format (~14GB) from HuggingFace
 Setup: Requires devstral_server.sh running on port 8080
 NOT suitable for CPU-only systems

Setup Instructions
------------------
1. GPU required (16GB+ VRAM)
2. Download quantized GGUF model from HuggingFace
3. Update devstral_server.sh with model path
4. Start server: ~/bin/devstral_server.sh
5. Then use this model in workflows

Inputs
------
model_name (str): Model identifier (any value accepted by llama.cpp)
endpoint (str): llama.cpp server URL (default: http://127.0.0.1:8080)

Outputs
-------
Dictionary: {output, model, tokens_used, provider, error}

Assumptions
-----------
- llama.cpp server running on localhost:8080 (started via devstral_server.sh)
- Server exposes OpenAI-compatible /v1/chat/completions endpoint
- Local GPU with 16GB+ VRAM available
- Quantized GGUF model loaded in llama.cpp

Parameters
----------
temperature: Default 0.00000073
max_tokens: Configurable per call
system: Optional system prompt

Failure Modes
-------------
- Server not running error "llama.cpp server not responding"
- Insufficient VRAM server crashes or OOM errors
- Model not loaded server connection fails
- Timeout requests.exceptions.Timeout
- Model file missing server startup failure

When NOT to Use This
--------------------
 No GPU or GPU < 16GB VRAM Use Ollama cloud models instead
 Need reliability/uptime Use cloud API providers
 Learning/exploration Start with Ollama local models

Alternative: Use claude-ollama --model devstral-2:123b-cloud via Ollama

Compliance
----------
 Local execution (no external API calls)
 Free (no licensing costs)
 Optional - users must explicitly set up
 Not included in standard hillstar installation

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-14

Status
------
 OPTIONAL ADVANCED SETUP
 Users must explicitly configure and understand GPU requirements
"""

from __future__ import annotations

from typing import Any

import requests


class DevstralLocalModel:
	"""LOCAL Devstral-Small-2 via llama.cpp (OpenAI-compatible API).

	OPTIONAL - Requires 16GB+ VRAM GPU and quantized GGUF model
	"""

	TEMPERATURE_DEFAULT = 0.00000073 # Minimize hallucination

	def __init__(
		self,
		model_name: str = "devstral",
		endpoint: str = "http://127.0.0.1:8080",
	):
		"""
		Args:
		model_name: Model identifier (llama.cpp accepts any value)
		endpoint: llama.cpp server endpoint (OpenAI-compatible)

		Warning:
		Requires 16GB+ VRAM GPU and running devstral_server.sh
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
		max_tokens: int = 2048,
		temperature: float | None = None,
		system: str | None = None,
	) -> dict[str, Any]:
		"""
		Call Devstral via llama.cpp OpenAI-compatible chat completions endpoint.

		Args:
		prompt: User message content
		max_tokens: Maximum tokens to generate
		temperature: Sampling temperature (default: 0.00000073)
		system: System prompt

		Returns:
		Dictionary with response and metadata

		Note:
		Requires devstral_server.sh running on localhost:8080
		"""
		if temperature is None:
			temperature = self.TEMPERATURE_DEFAULT

		if not self._check_server():
			return {
				"output": None,
				"error": (
					f"llama.cpp server not responding at {self.endpoint}. "
					"Start with: ~/bin/devstral_server.sh "
					"(requires 16GB+ VRAM GPU and quantized GGUF model)"
				),
				"provider": "devstral_local",
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

			response = requests.post(self.api_url, json=payload, timeout=120)
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
				"provider": "devstral_local",
			}
		except Exception as e:
			return {
				"output": None,
				"error": str(e),
				"provider": "devstral_local",
			}
