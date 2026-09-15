# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-only

"""
Script
------
local_model.py

Path
----
models/local_model.py

Purpose
-------
Generic local/self-hosted model via any OpenAI-compatible HTTP server.

One configurable class replaces the former hard-coded Devstral and Jan-Code
local models. Point it at any server that exposes an OpenAI-compatible
/v1/chat/completions endpoint (llama.cpp, vLLM, LM Studio, Ollama's OpenAI
compatibility layer, text-generation-webui, ...).

LOCAL EXECUTION IS OPTIONAL AND GENERALLY NOT RECOMMENDED: it requires local
GPU/hardware and manual server management, and results are not part of any
supported reproducibility path. Most users should configure a hosted provider
(e.g. OpenAI) instead. This template exists so users who already run a local
server can plug it in with configuration alone — no code changes.

Configuration
-------------
Local models are configured, never hard-coded. Two supported patterns:

1. Remote box on the LAN (e.g. a DGX Spark or GPU workstation serving an
   OpenAI-compatible endpoint such as vLLM or llama.cpp server). Working
   example — qwen3.8-flash-next served from the DGX Spark:

	"custom_providers": {
		"local": {
			"endpoint": "http://spark:8000",
			"model_name": "qwen3.8-flash-next"
		}
	}

2. Ollama local models: use Ollama's OpenAI-compatible endpoint and follow
   the Ollama documentation for pulling and serving models
   (https://docs.ollama.com). No special support is needed:

	"custom_providers": {
		"local": {
			"endpoint": "http://127.0.0.1:11434",
			"model_name": "qwen3:8b"
		}
	}

Then reference `"provider": "local"` on the workflow node. The class is
transport-identical for both cases: only endpoint and model name change.

Inputs
------
model_name (str): Model identifier (any value the server accepts)
endpoint (str): Server base URL (default: http://127.0.0.1:8080)

Outputs
-------
Dictionary: {output, model, tokens_used, provider, error}

Failure Modes
-------------
- Server not running: "local model server not responding"
- Empty response: typed error, no successful "No output" result
- Timeout: requests.exceptions.Timeout

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-09-03
"""

from __future__ import annotations

from typing import Any

import requests


class LocalModel:
	"""Generic local/self-hosted model via an OpenAI-compatible HTTP server."""

	TEMPERATURE_DEFAULT = 0  # Deterministic by default

	def __init__(
		self,
		model_name: str = "local-model",
		endpoint: str | None = None,
	):
		"""
		Args:
		model_name: Model identifier (the server must accept this value)
		endpoint: Server base URL. Defaults to http://127.0.0.1:8080 when
		unset (e.g. local discovery left the endpoint unconfigured).
		"""
		self.model_name = model_name
		self.endpoint = endpoint or "http://127.0.0.1:8080"
		self.api_url = f"{self.endpoint}/v1/chat/completions"

	def _check_server(self) -> bool:
		"""Check if the local server is reachable."""
		try:
			response = requests.get(f"{self.endpoint}/health", timeout=2)
			return response.status_code == 200
		except requests.exceptions.RequestException:
			# Some servers do not expose /health; accept a bare root probe.
			try:
				response = requests.get(self.endpoint, timeout=2)
				return response.status_code < 500
			except requests.exceptions.RequestException:
				return False

	def call(
		self,
		prompt: str,
		max_tokens: int = 4096,
		temperature: float | None = None,
		system: str | None = None,
		**kwargs: Any,
	) -> dict[str, Any]:
		"""
		Call the local server's OpenAI-compatible chat completions endpoint.

		Args:
		prompt: User message content
		max_tokens: Maximum tokens to generate
		temperature: Sampling temperature (default: 0)
		system: System prompt

		Returns:
		Dictionary with response and metadata
		"""
		if temperature is None:
			temperature = self.TEMPERATURE_DEFAULT

		if not self._check_server():
			return {
				"output": None,
				"error": (
					f"local model server not responding at {self.endpoint}. "
					"Start your local server (llama.cpp, vLLM, LM Studio, ...) "
					"and verify the configured endpoint."
				),
				"provider": "local",
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
			for key in ("reasoning_effort", "thinking", "chat_template_kwargs"):
				if key in kwargs:
					payload[key] = kwargs[key]

			response = requests.post(self.api_url, json=payload, timeout=300)
			response.raise_for_status()

			data = response.json()
			message = (data.get("choices") or [{}])[0].get("message") or {}
			raw_content = message.get("content")
			if not isinstance(raw_content, str) or not raw_content.strip():
				return {
					"output": None,
					"error": "model response contained no text content",
					"provider": "local",
				}
			content = raw_content.strip()
			usage = data.get("usage", {})

			return {
				"output": content,
				"model": self.model_name,
				"tokens_used": usage.get("total_tokens", 0),
				"provider": "local",
			}
		except Exception as e:
			return {
				"output": None,
				"error": str(e),
				"provider": "local",
			}
