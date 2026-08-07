# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Script
------
model_selector.py

Path
----
execution/model_selector.py

Purpose
-------
Model Factory: Manage model instantiation, caching, and provider selection logic for execution.

Extracted from WorkflowRunner to separate model creation and provider resolution from execution.
Handles provider availability checks, provider preference resolution, and model instance caching.

Inputs
------
model_config (dict): Model configuration with provider preferences
trace_logger (TraceLogger): Logger for provider resolution events
config_validator (ConfigValidator): For API key retrieval
node_id (str): Node identifier for selection logging
node (dict): Node definition with optional provider/model
provider (str): Provider name for availability check
provider_preference (list): List of preferred providers in order

Outputs
-------
model (BaseModel): Cached or newly created model instance
provider_chain (list): Ordered list of providers to try
is_available (bool): Whether provider is available

Assumptions
-----------
- Model classes are importable from models module
- Local tools (claude, ollama, codex) are accessible if available
- API keys are managed by ConfigValidator

Parameters
----------
None (per-workflow via model_config)

Failure Modes
-------------
- Unknown provider ValueError
- Missing API key Model handles error
- Ollama unavailable Check fails, other providers tried
- Local tool missing Marked unavailable

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
"""

import subprocess
import shutil
import threading
import urllib.request
from datetime import datetime
from .trace import TraceLogger
from .config_validator import ConfigValidator
from models import (
	AnthropicOllamaAPIModel,
	AnthropicModel,
	AnthropicMCPModel,
	DevstralLocalModel,
	JanCodeLocalModel,
	MistralAPIModel,
	OpenAIMCPModel,
	MistralMCPModel,
	OllamaMCPModel,
)
from models.ollama_api_model import OllamaAPIModel
from execution.seat_resolver import is_seat, resolve_seat
from config.model_selector import ModelSelector


class ModelFactory:
	"""Factory for creating and caching model instances with provider resolution."""

	def __init__(
		self,
		model_config: dict,
		trace_logger: TraceLogger,
		config_validator: ConfigValidator,
	):
		"""
		Args:
			model_config: Model configuration with provider preferences
			trace_logger: Logger for provider resolution and events
			config_validator: ConfigValidator for API key retrieval
		"""
		self.model_config = model_config
		self.trace_logger = trace_logger
		self.config_validator = config_validator
		self._models: dict = {}
		self._provider_resolution_logged = False
		self._resolved_provider_preference = None
		self._ollama_available_cache = None
		self._resolution_lock = threading.RLock()
		self._model_lock = threading.RLock()

	def select_model(
		self,
		node_id: str,
		node: dict,
	) -> tuple:
		"""
		Select model for a node using three-layer priority.

		Layer 1: Explicit node settings (provider/model)
		Layer 2: Config-based selection (task_type/complexity + provider_preference)
		Layer 3: Fallback defaults

		Returns:
			(provider, model_name) tuple
		"""
		# Layer 1: Check for explicit provider in node (model is optional — defaults apply)
		if node.get("provider"):
			provider = node["provider"]
			# Use explicit model if given, else fall back to provider default
			_defaults = {
				"devstral": "devstral",
				"jan_code": "jan-code",
				"jan_code_local": "jan-code",
				"local": "local",
				"anthropic": "claude-haiku-4-5-20251001",
				"openai": "gpt-5-mini-2025-08-07",
				"ollama": "minimax-m2.5:cloud",
				"anthropic_mcp": "claude-sonnet-4-6",
			}
			model = node.get("model") or _defaults.get(provider, "")
			return (provider, model)

		# Layer 2: Use config-based selection
		# Support both 'task_type' (new) and 'complexity' (legacy) field names
		task_complexity = node.get("task_type") or node.get("complexity", "moderate")

		# In auto mode, respect provider_preference order
		mode = self.model_config.get("mode", "explicit")
		provider_preference = self.model_config.get("provider_preference", [])

		if mode == "auto" and provider_preference:
			resolved_preference = self.resolve_provider_preference(provider_preference)
			# Use provider preference order (e.g., ["anthropic_mcp", "ollama", "local"])
			# Try each provider in order using registry-based selection
			for pref_provider in resolved_preference:
				# Use select_new with provider preference
				provider, model = ModelSelector.select_new(
					task_complexity,
					provider_preference=pref_provider,
				)
				if provider == pref_provider:
					return (provider, model)

		# Fallback to registry-based selection without provider preference
		provider, model = ModelSelector.select_new(task_complexity)

		return (provider, model)

	def resolve_provider_preference(self, provider_preference: list[str]) -> list[str]:
		"""Resolve provider preferences once, safely across worker threads."""
		with self._resolution_lock:
			return self._resolve_provider_preference(provider_preference)

	def _resolve_provider_preference(self, provider_preference: list[str]) -> list[str]:
		"""Resolve provider preference list based on availability checks."""
		if self._resolved_provider_preference is not None:
			return self._resolved_provider_preference

		availability = {}
		resolved = []
		for provider in provider_preference:
			available = self.provider_is_available(provider)
			availability[provider] = available
			if available:
				resolved.append(provider)

		resolution_status = "resolved"
		if not resolved:
			resolved = provider_preference
			resolution_status = "fallback_to_original"

		self._resolved_provider_preference = resolved

		if not self._provider_resolution_logged:
			self.trace_logger.log(
				{
					"timestamp": datetime.now().isoformat(),
					"event": "provider_preference_resolved",
					"resolution_status": resolution_status,
					"original_preference": provider_preference,
					"resolved_preference": resolved,
					"availability": availability,
				}
			)
			self._provider_resolution_logged = True

		return resolved

	# Local llama.cpp providers and their default endpoints
	LOCAL_LLAMA_PROVIDERS = {
		"devstral": "http://127.0.0.1:8080",
		"devstral_local": "http://127.0.0.1:8080",
		"jan_code": "http://127.0.0.1:8081",
		"jan_code_local": "http://127.0.0.1:8081",
	}

	def provider_is_available(self, provider: str) -> bool:
		"""Check if a provider appears available based on local tools/endpoints."""
		if provider in ["local"]:
			return True

		if provider in self.LOCAL_LLAMA_PROVIDERS:
			return self._check_http_health(self.LOCAL_LLAMA_PROVIDERS[provider])

		if provider in ["anthropic_mcp"]:
			return shutil.which("claude") is not None

		if provider in ["anthropic_ollama"]:
			return shutil.which("claude") is not None and self.ollama_available()

		if provider in ["codex_mcp", "codex_messages"]:
			return shutil.which("codex") is not None

		if provider in ["ollama"]:
			return self.ollama_available()

		# Default to True for API-based providers or custom providers
		return True

	def _check_http_health(self, endpoint: str) -> bool:
		"""Check if an HTTP server is healthy via /health endpoint."""
		try:
			with urllib.request.urlopen(f"{endpoint}/health", timeout=10) as resp:
				return resp.status == 200
		except Exception:
			return False

	def ollama_available(self) -> bool:
		"""Check if Ollama is available via CLI or HTTP."""
		if self._ollama_available_cache is not None:
			return self._ollama_available_cache

		available = False
		try:
			proc = subprocess.run(
				["ollama", "list"],
				capture_output=True,
				text=True,
				timeout=5,
			)
			if proc.returncode == 0 and proc.stdout.strip():
				available = True
		except (FileNotFoundError, subprocess.SubprocessError):
			available = False

		if not available:
			try:
				with urllib.request.urlopen(
					"http://127.0.0.1:11434/api/tags", timeout=5
				):
					available = True
			except Exception:
				available = False

		self._ollama_available_cache = available
		return available

	def _custom_provider(self, provider: str) -> dict | None:
		"""Return the workflow's `custom_providers` entry for `provider`, if any.

		`model_config.custom_providers` has been in the workflow schema since
		the beginning (endpoint / model_name / type), but nothing read it during
		execution — only `WorkflowDiscovery` looked at it, for a metadata
		boolean. Reading it here is what lets a workflow target an arbitrary
		OpenAI-compatible endpoint (notably the Vogelkop router) without adding
		a provider to the hardcoded enum below.

		Returns None when the entry is missing or malformed, so a typo falls
		through to normal provider resolution rather than silently producing a
		client pointed at nothing.
		"""
		custom = self.model_config.get("custom_providers")
		if not isinstance(custom, dict):
			return None
		entry = custom.get(provider)
		if not isinstance(entry, dict):
			return None
		endpoint = entry.get("endpoint")
		if not isinstance(endpoint, str) or not endpoint.strip():
			return None
		return entry

	def _model_for_seat(self, seat_name: str):
		"""Build the model a seat resolves to on THIS machine.

		Resolution is deliberately not cached across calls beyond the existing
		model cache: the answer depends on what the machine currently has, and
		a router that comes up mid-session should be usable without a restart.

		The chosen model is recorded in the trace. Portability makes the model
		vary by machine, so an execution receipt is the only place that record
		survives -- see agents-process/execution-architecture.md.
		"""
		resolution = resolve_seat(
			seat_name,
			custom_providers=self.model_config.get("custom_providers"),
		)

		self.trace_logger.log(
			{
				"timestamp": datetime.now().isoformat(),
				"event": "seat_resolved",
				"seat": seat_name,
				"source": resolution.source,
				"provider": resolution.provider,
				"model": resolution.model_name,
				"endpoint": resolution.endpoint,
			}
		)

		if resolution.provider == "ollama":
			# Local discovery leaves the endpoint unset, so the client's own
			# default (127.0.0.1:11434) applies.
			if resolution.endpoint:
				return OllamaAPIModel(resolution.model_name, endpoint=resolution.endpoint)
			return OllamaAPIModel(resolution.model_name)

		# llamacpp and custom both speak OpenAI-compatible
		# /v1/chat/completions, which is what the router serves.
		return JanCodeLocalModel(resolution.model_name, endpoint=resolution.endpoint)

	def get_model(self, provider: str, model_name: str, **kwargs):
		"""Get or create a cached model safely across worker threads."""
		with self._model_lock:
			return self._get_model(provider, model_name, **kwargs)

	def _get_model(self, provider: str, model_name: str, **kwargs):
		"""Get or create model instance with smart selection.

		Args:
			provider: Provider name.
			model_name: Model identifier.
			**kwargs: Provider-specific options (e.g., sandbox, approval_policy
			for codex_mcp).
		"""
		import importlib

		# Include provider-specific config in cache key to allow different
		# sandbox/approval configs for different nodes.
		extra_key = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
		key = (
			f"{provider}:{model_name}:{extra_key}"
			if extra_key
			else f"{provider}:{model_name}"
		)

		if key not in self._models:
			# Reload anthropic_ollama module to ensure latest fixes
			if provider == "anthropic_ollama":
				import sys

				if "hillstar.models.anthropic_ollama_api_model" in sys.modules:
					importlib.reload(
						sys.modules["hillstar.models.anthropic_ollama_api_model"]
					)
			# Get API key from config or environment (for providers that need it)
			api_key = self.config_validator.get_api_key_for_provider(provider)

			# A SEAT names a role, not a model. Resolve it through the chain
			# (workflow pin -> host router -> local discovery -> typed failure)
			# so the same workflow runs under Vogelkop, standalone, or on
			# another machine without carrying a host address.
			if is_seat(model_name):
				self._models[key] = self._model_for_seat(model_name)
				return self._models[key]

			custom = self._custom_provider(provider)
			if custom is not None:
				# A declared endpoint wins over the built-in provider table, so
				# a workflow can point `ollama` (or any name) at a different
				# host without editing source. `model_name` from the entry
				# overrides the node's, letting the workflow name a seat while
				# the entry supplies what the backend actually serves.
				endpoint = custom["endpoint"].rstrip("/")
				effective_model = custom.get("model_name") or model_name
				kind = custom.get("type", "custom")
				if kind == "ollama":
					self._models[key] = OllamaAPIModel(effective_model, endpoint=endpoint)
				else:
					# llamacpp and custom both speak OpenAI-compatible
					# /v1/chat/completions, which is also what the router serves.
					self._models[key] = JanCodeLocalModel(effective_model, endpoint=endpoint)
				return self._models[key]

			if provider == "anthropic":
				self._models[key] = AnthropicModel(model_name, api_key=api_key)
			elif provider == "anthropic_ollama":
				self._models[key] = AnthropicOllamaAPIModel(model_name=model_name)
			elif provider == "anthropic_mcp":
				self._models[key] = AnthropicMCPModel(model_name, api_key=api_key)
			elif provider in ("openai", "openai_mcp"):
				self._models[key] = OpenAIMCPModel(model_name, api_key=api_key)
			elif provider == "mistral":
				self._models[key] = MistralAPIModel(model_name, api_key=api_key)
			elif provider == "mistral_mcp":
				self._models[key] = MistralMCPModel(model_name, api_key=api_key)
			elif provider == "ollama":
				self._models[key] = OllamaAPIModel(model_name)
			elif provider == "ollama_mcp":
				self._models[key] = OllamaMCPModel(model_name)
			elif provider in ["devstral", "devstral_local", "local"]:
				self._models[key] = DevstralLocalModel(model_name)
			elif provider in ["jan_code", "jan_code_local"]:
				self._models[key] = JanCodeLocalModel(model_name)
			else:
				raise ValueError(f"Unknown provider: {provider}")

		return self._models[key]
