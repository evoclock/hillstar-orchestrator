"""
Script
------
config.py

Purpose
-------
Unified configuration management for Hillstar.

Handles:
- Loading default registry from provider_registry.default.json
- Merging user overrides from user config
- Validating provider configurations against registry schema
- Compliance checks for provider configurations
- Managing user-level API keys and settings

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-22
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from .provider_registry import ProviderRegistry


class HillstarConfig:
	"""
	Unified configuration management for Hillstar.

	Combines registry-based provider configuration with user-level
	API key management. Provides methods for:
	- Loading and merging configurations
	- Validating provider configurations
	- Managing user API keys and settings
	- Checking compliance requirements
	"""

	USER_CONFIG_DIR = Path.home() / ".hillstar"
	USER_CONFIG_FILE = USER_CONFIG_DIR / "provider_registry.json"
	USER_OVERRIDE_PATH = USER_CONFIG_FILE

	def __init__(self):
		"""Initialize HillstarConfig with user and default configurations."""
		self.registry = ProviderRegistry()
		self.user_config: dict[str, Any] = self._load_or_init_config()

	# ===== User Configuration Management =====

	def set_provider_key(self, provider: str, api_key: str) -> None:
		"""
		Store API key for a provider.

		Args:
			provider: Provider name (e.g., 'anthropic', 'openai')
			api_key: API key value

		Raises:
			ValueError: If provider name or api_key is empty
		"""
		if not provider or not api_key:
			raise ValueError("Provider name and API key cannot be empty")

		if "providers" not in self.user_config:
			self.user_config["providers"] = {}

		self.user_config["providers"][provider] = {"api_key": api_key}

	def get_provider_key(self, provider: str) -> Optional[str]:
		"""
		Retrieve API key for a provider.

		Args:
			provider: Provider name

		Returns:
			API key if configured, None otherwise
		"""
		if "providers" not in self.user_config:
			return None

		provider_config = self.user_config["providers"].get(provider, {})
		return provider_config.get("api_key")

	def list_configured_providers(self) -> list[str]:
		"""
		List providers that have API keys configured.

		Returns:
			List of provider names with keys configured
		"""
		if "providers" not in self.user_config:
			return []

		configured = []
		for provider, config in self.user_config["providers"].items():
			if isinstance(config, dict) and "api_key" in config:
				configured.append(provider)

		return sorted(configured)

	def list_missing_providers(
		self, all_providers: Optional[list[str]] = None
	) -> list[str]:
		"""
		List providers not yet configured.

		Args:
			all_providers: List of provider names to check against.
			If None, uses default provider list.

		Returns:
			List of provider names without keys configured
		"""
		if all_providers is None:
			all_providers = [
				"anthropic",
				"openai",
				"google_ai_studio",
				"mistral",
				"ollama",
				"devstral_local",
				"anthropic_ollama",
			]

		configured = self.list_configured_providers()
		missing = [p for p in all_providers if p not in configured]

		return sorted(missing)

	def validate_key(self, provider: str, api_key: str) -> bool:
		"""
		Validate that an API key is non-empty and reasonably formatted.

		This is basic validation (non-empty, reasonable length).
		Full validation (API call) deferred to runtime.

		Args:
			provider: Provider name
			api_key: API key to validate

		Returns:
			True if key passes basic validation, False otherwise
		"""
		if not api_key or not isinstance(api_key, str):
			return False

		# Basic checks: non-empty, reasonable length (>= 8 chars)
		if len(api_key.strip()) < 8:
			return False

		# No spaces in key (most API keys don't have them)
		if " " in api_key:
			return False

		return True

	def save_config(self) -> None:
		"""
		Write configuration to ~/.hillstar/provider_registry.json.

		Creates the directory if it doesn't exist.

		Raises:
			IOError: If unable to write file
		"""
		try:
			self.USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

			# Prepare config with metadata
			config_to_save = {
				"version": "1.0.0",
				"description": "User provider configuration",
				"providers": self.user_config.get("providers", {}),
			}

			with open(self.USER_CONFIG_FILE, "w") as f:
				json.dump(config_to_save, f, indent=2)

		except IOError as e:
			msg = f"Failed to save config to {self.USER_CONFIG_FILE}: {e}"
			raise IOError(msg) from e

	def load_config(self) -> None:
		"""
		Load configuration from ~/.hillstar/provider_registry.json.

		Creates empty config if file doesn't exist.
		"""
		if self.USER_CONFIG_FILE.exists():
			try:
				with open(self.USER_CONFIG_FILE) as f:
					loaded = json.load(f)
				self.user_config = loaded
			except json.JSONDecodeError as e:
				msg = f"Invalid JSON in {self.USER_CONFIG_FILE}: {e}"
				raise ValueError(msg) from e
		else:
			self.user_config = {"providers": {}}

	# ===== Registry-Based Configuration =====

	def get_merged_registry(self) -> ProviderRegistry:
		"""Get the complete registry with user overrides applied."""
		return self.registry

	def validate_provider_config(
		self,
		provider: str,
		config: dict[str, Any],
	) -> list[str]:
		"""
		Validate provider configuration against registry.

		Args:
			provider: Provider name
			config: Provider configuration dict

		Returns:
			List of validation error messages (empty if valid)
		"""
		errors = []

		# Get provider schema from registry
		provider_schema = self.registry.get_provider(provider)
		if not provider_schema:
			# Unknown provider - skip validation
			return errors

		# Check required env vars are configured
		env_vars = provider_schema.get("env_vars", [])
		for env_var in env_vars:
			if env_var not in config and not os.getenv(env_var):
				msg = (
					f"Provider '{provider}' requires '{env_var}' "
					f"env var or config key"
				)
				errors.append(msg)

		# Validate endpoint format for non-local providers
		provider_type = provider_schema.get("type", "")
		if provider_type == "cloud_api":
			endpoint = provider_schema.get("endpoint", "")
			if endpoint and not (
				endpoint.startswith("http://") or endpoint.startswith("https://")
			):
				msg = f"Provider '{provider}' has invalid endpoint: {endpoint}"
				errors.append(msg)

		# Validate model is in registry
		model_name = config.get("model")
		if model_name:
			models = provider_schema.get("models", {})
			if models and model_name not in models:
				valid = list(models.keys())
				msg = (
					f"Unknown model '{model_name}' for provider "
					f"'{provider}'. Valid: {', '.join(valid[:5])}"
					f"{'...' if len(valid) > 5 else ''}"
				)
				errors.append(msg)

		return errors

	def check_compliance(
		self,
		provider: str,
		config: dict[str, Any],
	) -> tuple[bool, list[str]]:
		"""
		Check compliance requirements for a provider.

		Args:
			provider: Provider name
			config: Provider configuration

		Returns:
			(is_compliant: bool, issues: List[str])
		"""
		issues = []

		provider_config = self.registry.get_provider(provider)
		if not provider_config:
			return True, issues

		compliance = provider_config.get("compliance", {})
		if not compliance:
			return True, issues

		# Check ToS acceptance requirement
		requires_tos = compliance.get("requires_tos_acceptance", False)
		if requires_tos:
			tos_accepted = config.get("tos_accepted", False)
			if not tos_accepted:
				tos_url = compliance.get("tos_url", "N/A")
				msg = (
					f"Provider '{provider}' requires ToS acceptance. "
					f"See: {tos_url}"
				)
				issues.append(msg)

		# Check audit requirement
		audit_required = compliance.get("audit_required", False)
		if audit_required and not config.get("audit_enabled", False):
			msg = (
				f"Provider '{provider}' requires audit logging "
				f"to be enabled"
			)
			issues.append(msg)

		# Check data residency requirements
		allowed_regions = compliance.get("data_residency", [])
		if allowed_regions and "local" not in allowed_regions:
			# For cloud providers, user should be aware
			msg = (
				f"Provider '{provider}' processes data in: "
				f"{', '.join(allowed_regions)}"
			)
			issues.append(msg)

		return len(issues) == 0, issues

	def get_provider_info(
		self, provider: str
	) -> Optional[dict[str, Any]]:
		"""Get full provider configuration from registry."""
		return self.registry.get_provider(provider)

	def list_available_providers(self) -> list[str]:
		"""List all available providers from registry."""
		return self.registry.list_providers()

	def list_available_models(self, provider: str) -> list[str]:
		"""List all available models for a provider."""
		provider_config = self.registry.get_provider(provider)
		if not provider_config:
			return []
		models = provider_config.get("models", {})
		return list(models.keys())

	def merge_configs(
		self,
		user_config: dict[str, Any],
		workflow_config: dict[str, Any],
	) -> dict[str, Any]:
		"""
		Merge user configuration with workflow configuration.

		Workflow configuration takes precedence over user config.

		Args:
			user_config: User provider configuration overrides
			workflow_config: Workflow-specific model configuration

		Returns:
			Merged configuration dictionary
		"""
		# Start with user config as base
		merged = user_config.copy()

		# Override with workflow config (workflow takes precedence)
		merged.update(workflow_config)

		return merged

	# ===== Internal Methods =====

	def _load_or_init_config(self) -> dict[str, Any]:
		"""Load existing config or initialize empty one."""
		if self.USER_CONFIG_FILE.exists():
			try:
				with open(self.USER_CONFIG_FILE) as f:
					return json.load(f)
			except (json.JSONDecodeError, IOError):
				return {"providers": {}}
		return {"providers": {}}
