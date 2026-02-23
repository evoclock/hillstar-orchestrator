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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
