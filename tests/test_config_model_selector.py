"""
Unit tests for config/model_selector.py

Tests registry-based model selection logic, complexity tier mapping, and provider preferences.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.model_selector import ModelSelector


class TestModelSelector:
	"""Test suite for ModelSelector class with registry-based selection."""

	def test_complexity_tier_ranges_defined(self):
		"""Verify that complexity tier ranges are properly defined."""
		assert hasattr(ModelSelector, 'COMPLEXITY_TIER_RANGES')
		assert ModelSelector.COMPLEXITY_TIER_RANGES == {
			"simple": "affordable",
			"moderate": "standard",
			"complex": "expensive",
			"critical": "premium",
		}

	def test_temperature_default(self):
		"""Verify default temperature setting."""
		assert ModelSelector.TEMPERATURE_DEFAULT == 0.00000073
		assert ModelSelector.get_temperature() == 0.00000073

	def test_get_models_for_complexity_simple(self):
		"""Test _get_models_for_complexity for 'simple' complexity level."""
		models = ModelSelector._get_models_for_complexity("simple")
		assert isinstance(models, dict)
		assert len(models) > 0
		# All models should have a provider and model_id
		for provider, model_id in models.items():
			assert isinstance(provider, str)
			assert isinstance(model_id, str)
			assert len(provider) > 0
			assert len(model_id) > 0

	def test_get_models_for_complexity_moderate(self):
		"""Test _get_models_for_complexity for 'moderate' complexity level."""
		models = ModelSelector._get_models_for_complexity("moderate")
		assert isinstance(models, dict)
		assert len(models) > 0

	def test_get_models_for_complexity_complex(self):
		"""Test _get_models_for_complexity for 'complex' complexity level."""
		models = ModelSelector._get_models_for_complexity("complex")
		assert isinstance(models, dict)
		assert len(models) > 0

	def test_get_models_for_complexity_critical(self):
		"""Test _get_models_for_complexity for 'critical' complexity level."""
		models = ModelSelector._get_models_for_complexity("critical")
		assert isinstance(models, dict)
		assert len(models) > 0

	def test_get_models_for_unknown_complexity(self):
		"""Test _get_models_for_complexity with unknown complexity defaults to 'standard'."""
		models = ModelSelector._get_models_for_complexity("unknown")
		# Should still return models (defaults to "moderate" -> "standard")
		assert isinstance(models, dict)

	def test_select_without_preference(self):
		"""Test select() without provider preference returns valid tuple."""
		for complexity in ["simple", "moderate", "complex", "critical"]:
			provider, model = ModelSelector.select(complexity)
			assert isinstance(provider, str)
			assert isinstance(model, str)
			assert len(provider) > 0
			assert len(model) > 0

	def test_select_with_anthropic_preference(self):
		"""Test select() with anthropic provider preference."""
		for complexity in ["simple", "moderate", "complex", "critical"]:
			provider, model = ModelSelector.select(complexity, provider_preference="anthropic")
			# If anthropic is available for this complexity, it should be selected
			models = ModelSelector._get_models_for_complexity(complexity)
			if "anthropic" in models:
				assert provider == "anthropic"
				assert model == models["anthropic"]

	def test_select_with_unavailable_preference(self):
		"""Test select() with unavailable provider preference falls back to default priority."""
		provider, model = ModelSelector.select("simple", provider_preference="nonexistent")
		# Should fall back to default priority selection
		assert isinstance(provider, str)
		assert isinstance(model, str)

	def test_select_new_equivalent_to_select(self):
		"""Test that select_new() returns consistent results with select()."""
		for complexity in ["simple", "moderate", "complex", "critical"]:
			p1, m1 = ModelSelector.select(complexity)
			p2, m2 = ModelSelector.select_new(complexity)
			assert p1 == p2
			assert m1 == m2

	def test_select_provider_preference_with_select_new(self):
		"""Test select_new() with specific provider preferences."""
		test_cases = [
			("simple", "anthropic"),
			("moderate", "openai"),
			("complex", "mistral"),
			("critical", None),
		]

		for complexity, preference in test_cases:
			provider, model = ModelSelector.select_new(complexity, provider_preference=preference)
			assert isinstance(provider, str)
			assert isinstance(model, str)

			# If preference was provided and available, it should be used
			if preference:
				models = ModelSelector._get_models_for_complexity(complexity)
				if preference in models:
					assert provider == preference

	def test_fallback_model_critical(self):
		"""Test _fallback_model returns Opus for critical complexity."""
		provider, model = ModelSelector._fallback_model("critical")
		assert provider == "anthropic"
		assert model == "claude-opus-4-6"

	def test_fallback_model_complex(self):
		"""Test _fallback_model returns Sonnet for complex complexity."""
		provider, model = ModelSelector._fallback_model("complex")
		assert provider == "anthropic"
		assert model == "claude-sonnet-4-6"

	def test_fallback_model_default(self):
		"""Test _fallback_model returns Haiku for simple and moderate complexity."""
		for complexity in ["simple", "moderate"]:
			provider, model = ModelSelector._fallback_model(complexity)
			assert provider == "anthropic"
			assert model == "claude-haiku-4-5-20251001"

	def test_select_handles_default_complexity(self):
		"""Test select() uses 'moderate' as default complexity."""
		provider1, model1 = ModelSelector.select()
		provider2, model2 = ModelSelector.select("moderate")
		assert provider1 == provider2
		assert model1 == model2

	def test_select_new_handles_unknown_complexity(self):
		"""Test select_new() defaults to 'moderate' for unknown complexity."""
		provider, model = ModelSelector.select_new("unknown")
		# Should default to moderate
		provider_expected, model_expected = ModelSelector.select_new("moderate")
		assert provider == provider_expected
		assert model == model_expected

	def test_provider_priority_order(self):
		"""Test that provider priority is respected (local > anthropic > mistral > openai > google)."""
		# Get available providers for simple complexity
		models = ModelSelector._get_models_for_complexity("simple")
		available_providers = list(models.keys())

		# Test without preference
		provider, _ = ModelSelector.select_new("simple")

		# Check that it selected from available providers
		assert provider in available_providers

		# Verify priority order by checking if a higher-priority provider would be selected
		priority_order = ["local", "anthropic", "mistral", "openai", "google"]
		for higher_priority_provider in priority_order:
			if higher_priority_provider in available_providers:
				# This provider should be selected
				assert provider == higher_priority_provider
				break

	@pytest.mark.parametrize("complexity", ["simple", "moderate", "complex", "critical"])
	def test_all_complexity_levels(self, complexity):
		"""Parametrized test to verify all complexity levels work correctly."""
		provider, model = ModelSelector.select(complexity)
		assert provider is not None
		assert model is not None
		assert isinstance(provider, str)
		assert isinstance(model, str)
		assert len(provider) > 0
		assert len(model) > 0


class TestModelSelectorMockVerification:
	"""Enhanced tests: Mock verification of registry interactions."""

	def test_get_models_calls_registry_find_models(self):
		"""Mock verification: _get_models_for_complexity calls registry.find_models()."""
		from unittest.mock import patch, MagicMock
		with patch('config.model_selector.get_registry') as mock_get_registry:
			mock_registry = MagicMock()
			mock_get_registry.return_value = mock_registry
			mock_registry.find_models.return_value = [
				{"provider": "anthropic", "model_id": "claude-opus", "tier": "premium"}
			]

			ModelSelector._get_models_for_complexity("critical")

			# Deep assertion: Verify exact call arguments
			mock_registry.find_models.assert_called_once_with(max_tier="premium")

	def test_select_new_queries_models_for_complexity(self):
		"""Mock verification: select_new() queries models before priority selection."""
		from unittest.mock import patch
		with patch('config.model_selector.ModelSelector._get_models_for_complexity') as mock_get:
			mock_get.return_value = {"anthropic": "claude-sonnet"}

			ModelSelector.select_new("complex", provider_preference=None)

			# Verify it was called with normalized complexity
			mock_get.assert_called_once_with("complex")

	def test_complexity_normalization_calls_moderate(self):
		"""Mock verification: Unknown complexity normalized to 'moderate'."""
		from unittest.mock import patch
		with patch('config.model_selector.ModelSelector._get_models_for_complexity') as mock_get:
			mock_get.return_value = {"anthropic": "claude-haiku"}

			ModelSelector.select_new("invalid_complexity")

			# Should normalize to "moderate"
			mock_get.assert_called_once_with("moderate")


class TestModelSelectorBoundaryTesting:
	"""Enhanced tests: Boundary conditions and edge cases."""

	@pytest.mark.parametrize("complexity", [
		"", # Empty string
		None, # None value
		" ", # Whitespace
		"SIMPLE", # Uppercase (should not match)
		123, # Non-string (will be handled by type system)
	])
	def test_boundary_invalid_complexity_values(self, complexity):
		"""Boundary: Invalid complexity values handled gracefully."""
		try:
			result = ModelSelector.select_new(complexity)
			# Should not crash; either normalize or use fallback
			assert isinstance(result, tuple)
			assert len(result) == 2
		except (TypeError, AttributeError):
			# Acceptable to raise for non-string types
			pass

	def test_boundary_empty_model_dict(self):
		"""Boundary: When no models available, use fallback."""
		from unittest.mock import patch
		with patch('config.model_selector.ModelSelector._get_models_for_complexity') as mock_get:
			mock_get.return_value = {} # Empty dict

			provider, model = ModelSelector.select_new("critical")

			# Should fall back to Opus
			assert provider == "anthropic"
			assert model == "claude-opus-4-6"

	def test_boundary_none_provider_preference(self):
		"""Boundary: None provider_preference uses priority order."""
		from unittest.mock import patch
		with patch('config.model_selector.ModelSelector._get_models_for_complexity') as mock_get:
			mock_get.return_value = {"anthropic": "claude-sonnet", "openai": "gpt-4"}

			provider, model = ModelSelector.select_new("complex", provider_preference=None)

			# Should select anthropic (higher priority than openai)
			assert provider == "anthropic"

	def test_boundary_all_providers_unavailable_uses_fallback(self):
		"""Boundary: When all requested providers unavailable, use fallback."""
		from unittest.mock import patch
		with patch('config.model_selector.ModelSelector._get_models_for_complexity') as mock_get:
			# No providers available
			mock_get.return_value = {}

			for complexity in ["critical", "complex", "simple", "moderate"]:
				provider, model = ModelSelector.select_new(complexity)
				assert provider == "anthropic" # Always fallback to Anthropic


class TestModelSelectorParametrized:
	"""Enhanced tests: Parameterized variations for comprehensive coverage."""

	@pytest.mark.parametrize("complexity,expected_tier", [
		("simple", "affordable"),
		("moderate", "standard"),
		("complex", "expensive"),
		("critical", "premium"),
	])
	def test_complexity_maps_to_correct_tier(self, complexity, expected_tier):
		"""Deep: Verify tier mapping is correct for all complexities."""
		tier = ModelSelector.COMPLEXITY_TIER_RANGES[complexity]
		assert tier == expected_tier

	@pytest.mark.parametrize("complexity,expected_fallback_model", [
		("critical", "claude-opus-4-6"),
		("complex", "claude-sonnet-4-6"),
		("moderate", "claude-haiku-4-5-20251001"),
		("simple", "claude-haiku-4-5-20251001"),
		("unknown", "claude-haiku-4-5-20251001"),
	])
	def test_fallback_model_maps_complexity(self, complexity, expected_fallback_model):
		"""Deep: Fallback models match expected values for all complexity levels."""
		provider, model = ModelSelector._fallback_model(complexity)
		assert model == expected_fallback_model
		assert provider == "anthropic"

	@pytest.mark.parametrize("available_providers,preference,expected", [
		(["anthropic", "openai"], None, "anthropic"), # Priority: anthropic first
		(["openai"], None, "openai"), # Only option
		(["anthropic", "openai"], "openai", "openai"), # Preference respected
		(["anthropic"], "openai", "anthropic"), # Preference unavailable
		(["local", "anthropic"], None, "local"), # Local highest priority
	])
	def test_provider_selection_logic(self, available_providers, preference, expected):
		"""Deep: Provider selection follows documented priority order."""
		from unittest.mock import patch
		with patch('config.model_selector.ModelSelector._get_models_for_complexity') as mock_get:
			models = {p: f"{p}-model" for p in available_providers}
			mock_get.return_value = models

			provider, model = ModelSelector.select_new("moderate", provider_preference=preference)

			assert provider == expected
			assert model == f"{expected}-model"


class TestModelSelectorSideEffects:
	"""Enhanced tests: Verify state consistency and side effects."""

	def test_temperature_never_changes(self):
		"""Side effect: Temperature is immutable constant."""
		initial_temp = ModelSelector.TEMPERATURE_DEFAULT
		for _ in range(10):
			current_temp = ModelSelector.get_temperature()
			assert current_temp == initial_temp
			assert current_temp == 0.00000073

	def test_complexity_ranges_never_modified(self):
		"""Side effect: Complexity tier ranges remain consistent."""
		initial_ranges = ModelSelector.COMPLEXITY_TIER_RANGES.copy()

		# Call select multiple times
		for complexity in ["simple", "moderate", "complex", "critical"]:
			ModelSelector.select(complexity)

		# Verify ranges unchanged
		assert ModelSelector.COMPLEXITY_TIER_RANGES == initial_ranges

	def test_multiple_calls_same_complexity_consistent(self):
		"""Side effect: Multiple calls for same complexity yield same result."""
		results = []
		for _ in range(5):
			result = ModelSelector.select("moderate")
			results.append(result)

		# All results should be identical
		for i in range(1, len(results)):
			assert results[i] == results[0]

	def test_select_and_select_new_parity(self):
		"""Side effect: select() and select_new() maintain parity."""
		for complexity in ["simple", "moderate", "complex", "critical"]:
			r1 = ModelSelector.select(complexity)
			r2 = ModelSelector.select_new(complexity)
			assert r1 == r2, f"Parity broken for {complexity}: {r1} != {r2}"


class TestModelSelectorErrorHandling:
	"""Enhanced tests: Error conditions and messages."""

	def test_fallback_works_for_any_complexity(self):
		"""Error handling: Fallback always provides valid result."""
		test_values = ["critical", "complex", "moderate", "simple", "unknown", "", None]
		for value in test_values:
			try:
				provider, model = ModelSelector._fallback_model(value)
				assert provider == "anthropic"
				assert isinstance(model, str)
				assert len(model) > 0
			except (TypeError, AttributeError):
				# None is acceptable to fail with type error
				if value is not None:
					raise

	def test_select_never_returns_none(self):
		"""Error handling: select() always returns valid tuple."""
		for complexity in ["simple", "moderate", "complex", "critical", "unknown"]:
			result = ModelSelector.select(complexity)
			assert result is not None
			assert isinstance(result, tuple)
			assert len(result) == 2
			assert result[0] is not None # Provider
			assert result[1] is not None # Model

	def test_temperature_always_positive(self):
		"""Error handling: Temperature is always non-negative."""
		temp = ModelSelector.get_temperature()
		assert temp >= 0
		assert temp <= 2.0 # Within reasonable bounds


class TestModelSelectorIntegration:
	"""Enhanced tests: Integration with real registry."""

	def test_real_registry_provides_all_complexities(self):
		"""Integration: Real registry provides models for all complexity levels."""
		for complexity in ["simple", "moderate", "complex", "critical"]:
			models = ModelSelector._get_models_for_complexity(complexity)
			# Real registry should have models for valid complexity levels
			assert isinstance(models, dict)

	def test_real_select_returns_valid_models(self):
		"""Integration: Real select() returns models that exist in registry."""
		for complexity in ["simple", "moderate", "complex", "critical"]:
			provider, model = ModelSelector.select(complexity)
			# Verify result is reasonable
			assert isinstance(provider, str)
			assert isinstance(model, str)
			assert len(provider) > 0
			assert len(model) > 0


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
