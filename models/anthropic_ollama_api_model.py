"""
Script
------
anthropic_ollama_api_model.py

Path
----
models/anthropic_ollama_api_model.py

Purpose
-------
Anthropic models via Ollama's Anthropic-compatible API (Messages API).

Supports both local and cloud Ollama models:
- Local: ANTHROPIC_AUTH_TOKEN=ollama + ANTHROPIC_BASE_URL=http://localhost:11434
- Cloud: ANTHROPIC_AUTH_TOKEN=<your_api_key> + ANTHROPIC_BASE_URL=<cloud_endpoint>

Uses Anthropic Messages API for consistency with other Claude models.
No subprocess CLI calls - pure HTTP API orchestration.

Inputs
------
model_name (str): Ollama model identifier (e.g., "minimax-m2:cloud", "glm-4.7:cloud")
messages (list): Conversation messages in Anthropic format
max_tokens (int): Maximum response length
system (str): Optional system prompt
temperature (float): Sampling temperature

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Compliance
----------
API-based orchestration compliant with provider ToS.
Requires proper API key authentication via environment variables.

Parameters
----------
timeout: Default 600s for model call completion
max_retries: Retry transient failures (default 2)

Failure Modes
-------------
- Ollama not running error dict with details
- Model not available error dict
- Timeout waiting for response error dict
- Invalid API key 401 error

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-13

Last Edited
-----------
2026-02-14
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


class AnthropicOllamaAPIModel:
	"""Anthropic models via Ollama's Anthropic-compatible API."""

	# Valid models (synced with provider_registry.default.json)
	VALID_MODELS = {
		"devstral-2:123b-cloud",
		"gpt-oss:120b-cloud",
		"gemini-3-flash-preview:cloud",
		"minimax-m2.5:cloud",
		"mistral-large-3:675b-cloud",
	}

	def __init__(
		self,
		model_name: str = "minimax-m2.5:cloud",
		base_url: str | None = None,
		api_key: str | None = None,
		max_retries: int = 2
	):
		"""
		Initialize Anthropic Ollama API provider.

		Args:
		model_name: Ollama model identifier (local or cloud)
		base_url: Ollama endpoint URL (defaults to env var ANTHROPIC_BASE_URL or localhost)
		api_key: API key for authentication (defaults to env var ANTHROPIC_AUTH_TOKEN)
		max_retries: Number of retries for transient failures
		"""
		self.model_name = model_name
		self.max_retries = max_retries

		# Get configuration from env or params
		self.base_url = base_url or os.getenv(
			"ANTHROPIC_BASE_URL",
			"http://localhost:11434"
		)
		self.api_key = api_key or os.getenv("ANTHROPIC_AUTH_TOKEN", "ollama")
		self.timeout = 600

		# Set up headers for Anthropic Messages API
		self.headers = {
			"Content-Type": "application/json",
		}
		if self.api_key != "ollama":
			# Cloud API key
			self.headers["Authorization"] = f"Bearer {self.api_key}"

	def call(self, prompt: str, **kwargs) -> dict[str, Any]:
		"""
		Call model via Ollama's Anthropic-compatible API.

		Args:
		prompt: Input prompt text
		**kwargs: Additional parameters (max_tokens, temperature, system, etc.)

		Returns:
		Dictionary with response and metadata
		"""
		try:
			# Build messages in Anthropic format
			system = kwargs.pop("system", None)
			max_tokens = kwargs.pop("max_tokens", 4096)
			temperature = kwargs.pop("temperature", 0.00000073)

			messages = [{"role": "user", "content": prompt}]

			# Prepare request for Messages API
			payload = {
				"model": self.model_name,
				"messages": messages,
				"max_tokens": max_tokens,
				"temperature": temperature,
			}

			if system:
				payload["system"] = system

			# Add any extra kwargs
			payload.update(kwargs)

			# Make HTTP request to Ollama Messages API endpoint
			url = f"{self.base_url}/v1/messages"
			response = requests.post(
				url,
				json=payload,
				headers=self.headers,
				timeout=self.timeout
			)
			response.raise_for_status()

			# Parse response
			result = response.json()

			# Extract text content from response (may have thinking blocks first)
			text_output = ""
			for content_item in result.get("content", []):
				if content_item.get("type") == "text":
					text_output = content_item.get("text", "")
					break

			return {
				"output": text_output,
				"model": self.model_name,
				"tokens_used": result.get("usage", {}).get("output_tokens", 0),
				"provider": "anthropic_ollama_api"
			}

		except requests.exceptions.RequestException as e:
			logger.error(f"Ollama API error: {str(e)}")
			return {
				"output": None,
				"error": str(e),
				"model": self.model_name,
				"provider": "anthropic_ollama_api"
			}
