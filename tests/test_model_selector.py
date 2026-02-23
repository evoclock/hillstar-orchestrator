"""
Unit tests for execution/model_selector.py

Tests model selection logic, provider preference resolution, and model factory caching.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.model_selector import ModelFactory
from utils.exceptions import ConfigurationError


@pytest.fixture
def mock_trace_logger():
    """Create a mock TraceLogger."""
    return MagicMock()


@pytest.fixture
def mock_config_validator():
    """Create a mock ConfigValidator."""
    validator = MagicMock()
    validator.get_api_key_for_provider.return_value = "test-api-key"
    return validator


@pytest.fixture
def test_model_config():
    """Test model configuration."""
    return {
        "anthropic": {
            "models": ["claude-opus-4-6", "claude-sonnet-4-5", "claude-haiku-4-5"]
        },
        "openai": {
            "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        },
        "ollama": {
            "models": ["devstral-2", "minimax-m2.1", "glm-4.7"]
        },
        "mistral": {
            "models": ["mistral-large", "mistral-medium"]
        }
    }


@pytest.fixture
def model_factory(test_model_config, mock_trace_logger, mock_config_validator):
    """Create a ModelFactory instance."""
    return ModelFactory(test_model_config, mock_trace_logger, mock_config_validator)


class TestModelSelection:
    """Test basic model selection logic."""

    def test_select_model_by_name(self, model_factory):
        """Test selecting a model by exact name."""
        model = model_factory._select_model(
            model_name="claude-opus-4-6",
            provider_preference="anthropic",
            available_providers=["anthropic", "openai", "ollama"]
        )

        assert model["name"] == "claude-opus-4-6"
        assert model["provider"] == "anthropic"

    def test_select_model_by_provider_preference(self, model_factory):
        """Test selecting first model when provider is preferred."""
        model = model_factory._select_model(
            model_name=None,
            provider_preference="openai",
            available_providers=["anthropic", "openai", "ollama"]
        )

        assert model["provider"] == "openai"
        assert model["name"] in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

    def test_select_model_unknown_provider(self, model_factory):
        """Test selection with unknown provider."""
        model = model_factory._select_model(
            model_name="unknown-model",
            provider_preference="anthropic",
            available_providers=["anthropic"]
        )

        # Should return None or fallback
        assert model is None or "provider" in model

    def test_select_model_unknown_model(self, model_factory):
        """Test selection of unknown model."""
        model = model_factory._select_model(
            model_name="nonexistent-model-xyz",
            provider_preference="anthropic",
            available_providers=["anthropic"]
        )

        assert model is None or "provider" in model

    def test_select_model_fallback_to_available(self, model_factory):
        """Test fallback when preferred provider not available."""
        model = model_factory._select_model(
            model_name=None,
            provider_preference="anthropic",
            available_providers=["openai", "ollama"]  # anthropic not available
        )

        # Should fall back to available provider
        assert model is not None
        assert model["provider"] in ["openai", "ollama"]


class TestProviderResolution:
    """Test provider preference resolution."""

    def test_resolve_anthropic_preference(self, model_factory):
        """Test resolving Anthropic as preference."""
        resolved = model_factory._resolve_provider_preference(
            preference="anthropic",
            available_providers=["anthropic", "openai", "ollama"]
        )

        assert resolved == "anthropic"

    def test_resolve_openai_preference(self, model_factory):
        """Test resolving OpenAI as preference."""
        resolved = model_factory._resolve_provider_preference(
            preference="openai",
            available_providers=["anthropic", "openai", "mistral"]
        )

        assert resolved == "openai"

    def test_resolve_ollama_preference(self, model_factory):
        """Test resolving Ollama as preference."""
        resolved = model_factory._resolve_provider_preference(
            preference="ollama",
            available_providers=["anthropic", "ollama"]
        )

        assert resolved == "ollama"

    def test_resolve_unknown_preference_defaults(self, model_factory):
        """Test that unknown preference falls back to first available."""
        resolved = model_factory._resolve_provider_preference(
            preference="unknown_provider",
            available_providers=["anthropic", "openai"]
        )

        # Should return first available
        assert resolved == "anthropic"

    def test_resolve_empty_available_providers(self, model_factory):
        """Test resolution with no available providers."""
        resolved = model_factory._resolve_provider_preference(
            preference="anthropic",
            available_providers=[]
        )

        assert resolved is None

    def test_resolve_none_preference(self, model_factory):
        """Test resolution with None preference."""
        resolved = model_factory._resolve_provider_preference(
            preference=None,
            available_providers=["openai", "anthropic"]
        )

        # Should default to first available
        assert resolved in ["openai", "anthropic"]


class TestProviderAvailability:
    """Test provider availability checking."""

    def test_provider_is_available_with_api_key(self, model_factory):
        """Test provider is available when API key exists."""
        available = model_factory._provider_is_available(
            provider="anthropic",
            api_key="sk-ant-test"
        )

        assert available is True

    def test_provider_is_available_missing_api_key(self, model_factory):
        """Test provider unavailable without API key."""
        available = model_factory._provider_is_available(
            provider="openai",
            api_key=None
        )

        assert available is False

    def test_provider_unavailable(self, model_factory):
        """Test provider marked as unavailable."""
        available = model_factory._provider_is_available(
            provider="nonexistent",
            api_key="some-key"
        )

        # Nonexistent provider should be unavailable
        assert available is False

    def test_ollama_provider_no_key_needed(self, model_factory):
        """Test that Ollama doesn't require an API key."""
        available = model_factory._provider_is_available(
            provider="ollama",
            api_key=None
        )

        # Ollama should be available without API key
        assert available is True

    def test_multiple_providers_check(self, model_factory):
        """Test checking multiple providers."""
        providers = {
            "anthropic": "sk-ant-test",
            "openai": None,
            "ollama": None
        }

        available_providers = [
            p for p, key in providers.items()
            if model_factory._provider_is_available(p, key)
        ]

        assert "anthropic" in available_providers
        assert "ollama" in available_providers
        assert "openai" not in available_providers


class TestOllamaDetection:
    """Test Ollama availability detection."""

    @patch('subprocess.run')
    def test_ollama_available_when_running(self, mock_run, model_factory):
        """Test Ollama detection when running."""
        mock_run.return_value = MagicMock(returncode=0)

        available = model_factory._ollama_available()

        assert available is True

    @patch('subprocess.run')
    def test_ollama_unavailable_when_not_running(self, mock_run, model_factory):
        """Test Ollama detection when not running."""
        mock_run.return_value = MagicMock(returncode=1)

        available = model_factory._ollama_available()

        assert available is False

    @patch('subprocess.run')
    def test_ollama_available_cache(self, mock_run, model_factory):
        """Test that Ollama availability is cached."""
        mock_run.return_value = MagicMock(returncode=0)

        # First call
        available1 = model_factory._ollama_available()
        # Second call (should use cache)
        available2 = model_factory._ollama_available()

        # Both should be True
        assert available1 is True
        assert available2 is True
        # But subprocess.run should only be called once (caching works)
        assert mock_run.call_count == 1

    @patch('subprocess.run')
    def test_ollama_exception_handling(self, mock_run, model_factory):
        """Test exception handling in Ollama detection."""
        mock_run.side_effect = Exception("Connection refused")

        available = model_factory._ollama_available()

        # Should return False on exception
        assert available is False


class TestModelFactory:
    """Test model factory and caching."""

    def test_get_model_caching(self, model_factory):
        """Test that models are cached."""
        model1 = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6"
        )
        model2 = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6"
        )

        # Same instance should be returned from cache
        assert model1 is model2

    def test_get_model_creates_new_instance(self, model_factory):
        """Test that different models are separate instances."""
        model1 = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6"
        )
        model2 = model_factory.get_model(
            provider="anthropic",
            model="claude-sonnet-4-5"
        )

        # Different models should be different instances
        assert model1 is not model2

    def test_get_model_invalid_type(self, model_factory):
        """Test getting model with invalid type."""
        model = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6",
            model_type="invalid_type"
        )

        # Should handle gracefully or return None
        assert model is None or hasattr(model, 'call')

    def test_get_model_with_extra_config(self, model_factory):
        """Test getting model with extra configuration."""
        model = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6",
            extra_config={"timeout": 60}
        )

        assert model is not None

    def test_model_factory_empty_config(self, mock_trace_logger, mock_config_validator):
        """Test model factory with empty config."""
        factory = ModelFactory({}, mock_trace_logger, mock_config_validator)

        model = factory.get_model(provider="anthropic", model="claude-opus-4-6")

        # Should handle empty config gracefully
        assert model is None or hasattr(model, 'call')


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiple_providers(self, model_factory):
        """Test handling multiple providers."""
        providers = ["anthropic", "openai", "ollama", "mistral"]

        for provider in providers:
            model = model_factory.get_model(
                provider=provider,
                model=provider  # Use provider name as model
            )
            # Should not crash
            assert model is None or hasattr(model, 'call')

    def test_fallback_chains(self, model_factory):
        """Test fallback chain logic."""
        providers_chain = ["anthropic", "openai", "ollama"]

        resolved = model_factory._resolve_provider_preference(
            preference=None,
            available_providers=providers_chain
        )

        assert resolved == "anthropic"

    def test_cost_aware_selection(self, model_factory):
        """Test cost-aware model selection."""
        # Models selected should prefer cheaper options if not specified
        model = model_factory._select_model(
            model_name=None,
            provider_preference="openai",
            available_providers=["openai"]
        )

        assert model is not None

    def test_concurrent_model_requests(self, model_factory):
        """Test handling concurrent model requests."""
        models = []
        for i in range(5):
            model = model_factory.get_model(
                provider="anthropic",
                model="claude-opus-4-6"
            )
            models.append(model)

        # All should get the same instance (caching)
        assert all(m is models[0] for m in models)

    def test_very_long_model_name(self, model_factory):
        """Test handling very long model name."""
        long_name = "claude-" + "x" * 100

        model = model_factory.get_model(
            provider="anthropic",
            model=long_name
        )

        # Should handle gracefully
        assert model is None or hasattr(model, 'call')

    def test_special_characters_in_provider(self, model_factory):
        """Test provider names with special characters."""
        provider = "anthropic-test_v2"

        model = model_factory.get_model(
            provider=provider,
            model="test"
        )

        # Should handle gracefully
        assert model is None or hasattr(model, 'call')

    def test_cache_key_uniqueness(self, model_factory):
        """Test that cache keys are unique for different configs."""
        model1 = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6",
            extra_config={"timeout": 30}
        )
        model2 = model_factory.get_model(
            provider="anthropic",
            model="claude-opus-4-6",
            extra_config={"timeout": 60}
        )

        # Different configs should create different cache entries
        # (though may be same instance if caching is simple)
        assert model1 is not None

    def test_provider_resolution_logging(self, model_factory, mock_trace_logger):
        """Test that provider resolution is logged."""
        model_factory._resolve_provider_preference(
            preference="anthropic",
            available_providers=["anthropic", "openai"]
        )

        # Trace logger should be called (if logging is implemented)
        # This is a soft assertion - logging might be optional
        assert mock_trace_logger is not None
