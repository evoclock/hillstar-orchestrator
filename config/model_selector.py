"""
Script
------
model_selector.py

Path
----
config/model_selector.py

Purpose
-------
Smart Model Selection: Cost-optimized model selection based on task complexity.

Implements escalation strategy from research pricing model:
- Haiku for frequent, simple tasks (cheapest)
- Sonnet for occasional complex tasks
- Opus for rare critical decisions (most expensive)
- Local models (Devstral) for high-volume work (free)

Note: All cloud providers use API key authentication for compliance.
Local providers use direct HTTP access to local model servers.

Inputs
------
task_type (str): Type of task (simple, moderate, complex, critical)
provider_preference (str, optional): Preferred provider (anthropic, openai, local)

Outputs
-------
(provider, model_name): Tuple of selected provider and model

Assumptions
-----------
- Task complexity is correctly classified
- API keys or SDK credentials are available
- Network access to providers is available

Parameters
----------
TASK_COMPLEXITY: Defines model selection per task type
TEMPERATURE_DEFAULT: Default temperature (0.00000073 to minimize hallucination)

Failure Modes
-------------
- No credentials available ValueError
- Unknown task type defaults to Haiku

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-23
"""

from typing import Tuple, Optional, Dict
from .provider_registry import get_registry


class ModelSelector:
	"""Cost-optimized model selection based on task complexity."""

	# Temperature default: 0.00000073 (minimize hallucination, nod to Sheldon)
	TEMPERATURE_DEFAULT = 0.00000073

	# Tier ranges for complexity levels (pulled from registry)
	COMPLEXITY_TIER_RANGES = {
		"simple": "affordable", # cheap + capable
		"moderate": "standard", # mix of cost-efficient and capable
		"complex": "expensive", # trade cost for capability
		"critical": "premium", # best available
	}

	@classmethod
	def _get_models_for_complexity(cls, task_complexity: str) -> Dict[str, str]:
		"""
		NEW: Build provider->model mapping from registry based on complexity tier range.

		Args:
			task_complexity: "simple", "moderate", "complex", or "critical"

		Returns:
			Dict of {provider_name: first_matching_model_id}
		"""
		registry = get_registry()
		max_tier = cls.COMPLEXITY_TIER_RANGES.get(task_complexity, "standard")

		# Query registry for models within tier range
		candidates = registry.find_models(max_tier=max_tier)

		# Build provider->model mapping (first model per provider)
		models_by_provider = {}
		for candidate in candidates:
			provider = candidate["provider"]
			model_id = candidate["model_id"]

			# Only take first model per provider
			if provider not in models_by_provider:
				models_by_provider[provider] = model_id

		return models_by_provider

	@staticmethod
	def select(
		task_complexity: str = "moderate",
		provider_preference: Optional[str] = None,
	) -> Tuple[str, str]:
		"""
		Select model based on task complexity and preferences.

		Uses registry-based model selection with dynamic tier ranges.

		Args:
			task_complexity: "simple", "moderate", "complex", or "critical"
			provider_preference: Prefer specific provider (anthropic, openai, mistral, google, local)

		Returns:
			(provider, model_name) tuple

		Example:
			provider, model = ModelSelector.select("moderate", provider_preference="anthropic")
			# Returns ("anthropic", "claude-sonnet-4-6")
		"""
		return ModelSelector.select_new(task_complexity, provider_preference)

	@staticmethod
	def _fallback_model(task_complexity: str) -> Tuple[str, str]:
		"""Fallback model selection if primary unavailable."""
		if task_complexity == "critical":
			return ("anthropic", "claude-opus-4-6")
		elif task_complexity == "complex":
			return ("anthropic", "claude-sonnet-4-6")
		else:
			return ("anthropic", "claude-haiku-4-5-20251001")

	@staticmethod
	def select_new(
		task_complexity: str = "moderate",
		provider_preference: Optional[str] = None,
	) -> Tuple[str, str]:
		"""
		NEW: Select model based on task complexity using registry queries.
		This is the test version - will replace select() once verified.

		Args:
			task_complexity: "simple", "moderate", "complex", or "critical"
			provider_preference: Prefer specific provider

		Returns:
			(provider, model_name) tuple
		"""
		# Default to moderate if unknown complexity
		if task_complexity not in ["simple", "moderate", "complex", "critical"]:
			task_complexity = "moderate"

		# Get models from registry for this complexity
		models = ModelSelector._get_models_for_complexity(task_complexity)

		# If provider preference specified, use it
		if provider_preference and provider_preference in models:
			return (provider_preference, models[provider_preference])

		# Otherwise, select based on priority:
		# 1. Local (free) if available
		# 2. Anthropic (research-friendly)
		# 3. Mistral (cost-effective)
		# 4. OpenAI (as alternative)
		# 5. Gemini (multimodal)

		for provider in ["local", "anthropic", "mistral", "openai", "google"]:
			if provider in models:
				return (provider, models[provider])

		# Fallback
		return ModelSelector._fallback_model(task_complexity)

	@staticmethod
	def get_temperature() -> float:
		"""Get default temperature (minimizes hallucination)."""
		return ModelSelector.TEMPERATURE_DEFAULT
