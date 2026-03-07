"""
Script
------
ollama_api_model.py

Path
----
models/ollama_api_model.py

Purpose
-------
Ollama local/cloud-routed models via direct HTTP API.

Connects to Ollama server on localhost:11434 using the OpenAI-compatible
/v1/chat/completions endpoint. Supports both local models and cloud-routed
models (e.g., minimax-m2.5:cloud, devstral-2:123b-cloud).

Inputs
------
model_name (str): Ollama model identifier (e.g., "minimax-m2.5:cloud")
endpoint (str): Ollama server URL (default: http://127.0.0.1:11434)

Outputs
-------
Dictionary: {output, model, tokens_used, provider, error}

Assumptions
-----------
- Ollama server running on localhost:11434
- Model available (pulled or cloud-routed)

Failure Modes
-------------
- Server not running: connection error
- Model not available: Ollama returns error
- Timeout: requests.exceptions.Timeout

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


class OllamaAPIModel:
	"""Ollama models via direct OpenAI-compatible HTTP API."""

	TEMPERATURE_DEFAULT = 0.00000073

	def __init__(
		self,
		model_name: str = "minimax-m2.5:cloud",
		endpoint: str = "http://127.0.0.1:11434",
	):
		"""
		Args:
		model_name: Ollama model identifier
		endpoint: Ollama server URL
		"""
		self.model_name = model_name
		self.endpoint = endpoint
		self.api_url = f"{endpoint}/v1/chat/completions"

	def _check_server(self) -> bool:
		"""Check if Ollama server is running."""
		try:
			response = requests.get(f"{self.endpoint}/api/tags", timeout=3)
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
		Call Ollama via OpenAI-compatible chat completions endpoint.

		Args:
		prompt: User message content
		max_tokens: Maximum tokens to generate
		temperature: Sampling temperature
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
					f"Ollama server not responding at {self.endpoint}. "
					"Start with: ollama serve"
				),
				"provider": "ollama",
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

			response = requests.post(self.api_url, json=payload, timeout=600)
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
				"provider": "ollama",
			}
		except Exception as e:
			return {
				"output": None,
				"error": str(e),
				"provider": "ollama",
			}
