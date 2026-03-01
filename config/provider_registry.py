"""
Script
------
provider_registry.py

Path
----
python/hillstar/config/provider_registry.py

Purpose
-------
Provider Registry: Central registry for LLM providers, models, and compliance rules.

Provides a ProviderRegistry class that loads provider configurations from JSON
and provides lookup methods for model selection, cost estimation, and compliance
verification. Supports package defaults with user overrides for customization.

Inputs
------
Provider registry JSON files (default + optional user override)

Outputs
-------
Registry instance with lookup methods for providers, models, and compliance

Assumptions
-----------
- Default registry file exists at package location
- User override follows same schema as default

Parameters
----------
None (per-query)

Failure Modes
-------------
- Missing default registry FileNotFoundError
- Malformed JSON JSONDecodeError
- Invalid provider/model Returns None

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-14

Last Edited
-----------
2026-02-14 (initial implementation)
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ProviderRegistry:
	"""
	Load and query the provider registry with fallback to user overrides.

	The registry is loaded from:
	1. Package default: python/hillstar/config/provider_registry.default.json
	2. User override: ~/.hillstar/provider_registry.json (optional)
	"""

	DEFAULT_REGISTRY_PATH = Path(__file__).parent / "provider_registry.default.json"
	USER_OVERRIDE_PATH = Path(os.path.expanduser("~/.hillstar/provider_registry.json"))

	def __init__(self, custom_registry_path: Optional[str] = None):
		"""
		Initialize the provider registry.

		Args:
			custom_registry_path: Optional path to a custom registry file.
			If provided, this takes precedence over both default and user override.
		"""
		self._registry: Dict[str, Any] = {}
		self._providers: Dict[str, Dict[str, Any]] = {}
		self._models_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

		self._load_registry(custom_registry_path)

	def _load_registry(self, custom_registry_path: Optional[str] = None) -> None:
		"""Load registry from JSON files."""
		registry_data = {}

		# 1. Load package default
		default_path = self.DEFAULT_REGISTRY_PATH
		if default_path.exists():
			with open(default_path) as f:
				registry_data = json.load(f)
		else:
			raise FileNotFoundError(
				f"Default provider registry not found at {default_path}. "
				"Please reinstall the hillstar package."
			)

		# 2. Merge user override if exists (takes precedence)
		user_path = self.USER_OVERRIDE_PATH
		if custom_registry_path:
			custom_path = Path(custom_registry_path)
			if custom_path.exists():
				with open(custom_path) as f:
					custom_data = json.load(f)
				registry_data = self._merge_registry(registry_data, custom_data)
		elif user_path.exists():
			with open(user_path) as f:
				user_data = json.load(f)
			registry_data = self._merge_registry(registry_data, user_data)

		self._registry = registry_data
		self._providers = registry_data.get("providers", {})
		self._build_models_cache()

	def _merge_registry(
		self, base: Dict[str, Any], override: Dict[str, Any]
	) -> Dict[str, Any]:
		"""Deep merge override into base, with override taking precedence."""
		result = base.copy()

		for key, value in override.items():
			if key == "providers" and key in result:
				# Deep merge providers
				result["providers"] = {**result.get("providers", {}), **value}
			else:
				result[key] = value

		return result

	def _build_models_cache(self) -> None:
		"""Build a flat cache of all models for fast lookup."""
		for provider_name, provider_data in self._providers.items():
			models = provider_data.get("models", {})
			for model_id, model_data in models.items():
				self._models_cache[(provider_name, model_id)] = model_data

	@property
	def version(self) -> str:
		"""Get registry version."""
		return self._registry.get("version", "unknown")

	@property
	def last_updated(self) -> str:
		"""Get last update timestamp."""
		return self._registry.get("last_updated", "unknown")

	def list_providers(self, provider_type: Optional[str] = None) -> List[str]:
		"""
		List available providers, optionally filtered by type.

		Args:
			provider_type: Optional filter: "cloud_api", "local", "local_proxy"

		Returns:
			List of provider names
		"""
		providers = self._providers.keys()
		if provider_type:
			providers = [
				p for p in providers if self._providers[p].get("type") == provider_type
			]
		return list(providers)

	def get_provider(self, provider_name: str) -> Optional[Dict[str, Any]]:
		"""Get full provider configuration."""
		return self._providers.get(provider_name)

	def get_provider_compliance(self, provider_name: str) -> Optional[Dict[str, Any]]:
		"""Get compliance rules for a provider."""
		provider = self.get_provider(provider_name)
		if provider:
			return provider.get("compliance")
		return None

	def get_model(self, provider_name: str, model_id: str) -> Optional[Dict[str, Any]]:
		"""
		Get model configuration.

		Args:
			provider_name: Provider identifier (e.g., "anthropic")
			model_id: Model identifier (e.g., "claude-opus-4-6")

		Returns:
			Model configuration dict or None
		"""
		provider = self._providers.get(provider_name)
		if provider:
			return provider.get("models", {}).get(model_id)
		return None

	def find_models(
		self,
		capabilities: Optional[List[str]] = None,
		max_tier: Optional[str] = None,
		provider_type: Optional[str] = None,
		require_ollama: Optional[bool] = None,
	) -> List[Dict[str, Any]]:
		"""
		Find models matching criteria.

		Args:
			capabilities: List of required capabilities (e.g., ["coding", "reasoning"])
			max_tier: Maximum cost tier (e.g., "cheap", "standard")
			provider_type: Filter by provider type (e.g., "cloud_api", "local")
			require_ollama: If True, only return models requiring Ollama

		Returns:
			List of matching model configs with provider context
		"""
		matching = []
		tier_order = ["free", "affordable", "standard", "expensive", "premium"]
		max_tier_idx = tier_order.index(max_tier) if max_tier else len(tier_order) - 1

		for provider_name, provider_data in self._providers.items():
			# Filter by provider type
			if provider_type and provider_data.get("type") != provider_type:
				continue

			models = provider_data.get("models", {})
			for model_id, model_data in models.items():
				# Filter by capabilities
				if capabilities:
					model_caps = model_data.get("capabilities", [])
					if not all(cap in model_caps for cap in capabilities):
						continue

				# Filter by tier
				model_tier = model_data.get("tier", "premium")
				if tier_order.index(model_tier) > max_tier_idx:
					continue

				# Filter by Ollama requirement
				if require_ollama is not None:
					if require_ollama != model_data.get("requires_ollama", False):
						continue

				matching.append(
					{
						"provider": provider_name,
						"model_id": model_id,
						"display_name": model_data.get("display_name", model_id),
						"tier": model_tier,
						**model_data,
					}
				)

		return matching

	def get_cheapest_model(
		self,
		capabilities: Optional[List[str]] = None,
		provider_preference: Optional[List[str]] = None,
	) -> Optional[Tuple[str, str, Dict[str, Any]]]:
		"""
		Get the cheapest model matching criteria, respecting provider preference.

		Args:
			capabilities: Required capabilities
			provider_preference: Preferred provider order (e.g., ["anthropic", "openai"])

		Returns:
			Tuple of (provider, model_id, model_config) or None
		"""
		candidates = self.find_models(capabilities=capabilities, max_tier="premium")

		if not candidates:
			return None

		# Sort by: 1) provider preference, 2) tier order
		tier_order = ["free", "affordable", "standard", "expensive", "premium"]

		def sort_key(item):
			provider = item["provider"]
			tier_idx = tier_order.index(item.get("tier", "standard"))

			# Provider preference penalty
			pref_penalty = 0
			if provider_preference:
				try:
					pref_penalty = provider_preference.index(provider) * 10
				except ValueError:
					pref_penalty = 100 # Unpreferred providers last

			return (pref_penalty, tier_idx)

		candidates.sort(key=sort_key)
		best = candidates[0]

		return (best["provider"], best["model_id"], best)

	def estimate_cost(
		self,
		provider_name: str,
		model_id: str,
		input_tokens: int,
		output_tokens: int,
	) -> float:
		"""
		Estimate cost for a model call.

		Args:
			provider_name: Provider identifier
			model_id: Model identifier
			input_tokens: Number of input tokens
			output_tokens: Number of output tokens

		Returns:
			Estimated cost in USD
		"""
		model = self.get_model(provider_name, model_id)
		if not model:
			return 0.0

		pricing = model.get("pricing", {})
		input_cost = (input_tokens / 1_000_000) * pricing.get("input_per_1m_usd", 0)
		output_cost = (output_tokens / 1_000_000) * pricing.get("output_per_1m_usd", 0)

		return input_cost + output_cost

	def get_fallback_chain(
		self,
		complexity: str,
		provider_preference: Optional[List[str]] = None,
	) -> List[str]:
		"""
		Get provider fallback chain for a complexity level.

		Args:
			complexity: Task complexity ("simple", "moderate", "complex", "critical")
			provider_preference: Preferred providers (highest priority first)

		Returns:
			List of providers in fallback order
		"""
		default_chain = self._registry.get("default_fallback_chain", {})
		chain = default_chain.get(
			complexity, default_chain.get("moderate", ["anthropic", "openai"])
		)

		if provider_preference:
			# Insert preferred providers at the beginning
			result = []
			for pref in provider_preference:
				if pref in self._providers:
					result.append(pref)
			for provider in chain:
				if provider not in result:
					result.append(provider)
			return result

		return chain

	def is_usage_compliant(
		self,
		provider_name: str,
		use_case: str,
	) -> Tuple[bool, str]:
		"""
		Check if a use case is compliant for a provider.

		Args:
			provider_name: Provider identifier
			use_case: Intended use case (e.g., "research", "commercial")

		Returns:
			Tuple of (is_compliant, reason)
		"""
		compliance = self.get_provider_compliance(provider_name)
		if not compliance:
			return (True, "No compliance rules defined")

		allowed = compliance.get("allowed_use_cases", [])
		restricted = compliance.get("restricted_use_cases", [])

		if use_case in restricted:
			return (False, f"Use case '{use_case}' is restricted by provider")

		if allowed and use_case not in allowed:
			return (False, f"Use case '{use_case}' not in allowed list: {allowed}")

		return (True, "Use case is allowed")

	def get_model_sampling_params(
		self,
		provider_name: str,
		model_id: str,
	) -> Dict[str, Any]:
		"""Get default sampling parameters for a model."""
		model = self.get_model(provider_name, model_id)
		if model:
			return model.get("default_sampling_params", {})
		return {}

	def get_all_models_flat(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
		"""Get a flat dictionary of all (provider, model_id) -> model_config."""
		return self._models_cache.copy()

	def describe(self) -> str:
		"""Get a human-readable description of the registry."""
		lines = [
			f"Provider Registry v{self.version}",
			f"Last updated: {self.last_updated}",
			"",
			"Providers:",
		]

		for provider_name, provider_data in sorted(self._providers.items()):
			model_count = len(provider_data.get("models", {}))
			provider_type = provider_data.get("type", "unknown")
			display = provider_data.get("display_name", provider_name)
			lines.append(
				f" - {provider_name}: {display} ({model_count} models, {provider_type})"
			)

		return "\n".join(lines)


# Global registry instance (lazy loaded)
_registry_instance: Optional["ProviderRegistry"] = None


def get_registry() -> "ProviderRegistry":
	"""Get the global registry instance."""
	global _registry_instance
	if _registry_instance is None:
		_registry_instance = ProviderRegistry()
	return _registry_instance


def reset_registry() -> None:
	"""Reset the global registry instance (useful for testing)."""
	global _registry_instance
	_registry_instance = None
