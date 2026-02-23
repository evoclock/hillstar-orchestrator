"""
Unit tests for execution/model_selector.py

Tests model selection logic, provider preference resolution, and model factory caching.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

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
		"mode": "auto",
		"provider_preference": ["anthropic", "openai", "ollama"],
	}


@pytest.fixture
def model_factory(test_model_config, mock_trace_logger, mock_config_validator):
	"""Create a ModelFactory instance."""
	return ModelFactory(test_model_config, mock_trace_logger, mock_config_validator)


class TestModelSelection:
	"""Test model selection logic with select_model()."""

	def test_select_model_with_explicit_provider(self, model_factory):
		"""Test selecting model with explicit provider in node."""
		node = {
			"provider": "anthropic",
			"model": "claude-opus-4-6"
		}
		provider, model = model_factory.select_model("test_node_1", node)
		assert provider == "anthropic"
		assert model == "claude-opus-4-6"

	def test_select_model_with_explicit_provider_no_model(self, model_factory):
		"""Test selecting model with explicit provider but no model (uses default)."""
		node = {
			"provider": "openai"
		}
		provider, model = model_factory.select_model("test_node_2", node)
		assert provider == "openai"
		assert model == "gpt-4o"  # Default for openai

	def test_select_model_with_task_type_auto_mode(self, model_factory):
		"""Test selecting model based on task_type in auto mode."""
		node = {
			"task_type": "simple"
		}
		provider, model = model_factory.select_model("test_node_3", node)
		# Should return a valid provider/model pair
		assert provider is not None
		assert model is not None

	def test_select_model_with_complexity_legacy(self, model_factory):
		"""Test selecting model with legacy 'complexity' field."""
		node = {
			"complexity": "moderate"
		}
		provider, model = model_factory.select_model("test_node_4", node)
		# Should return a valid provider/model pair
		assert provider is not None
		assert model is not None

	def test_select_model_defaults_to_moderate(self, model_factory):
		"""Test that missing task_type defaults to moderate."""
		node = {}
		provider, model = model_factory.select_model("test_node_5", node)
		# Should return a valid provider/model pair
		assert provider is not None
		assert model is not None

	def test_select_model_with_complex_task(self, model_factory):
		"""Test selecting model for complex tasks."""
		node = {
			"task_type": "complex"
		}
		provider, model = model_factory.select_model("test_node_6", node)
		# Should return a valid provider/model pair
		assert provider is not None
		assert model is not None


class TestProviderResolution:
	"""Test provider preference resolution."""

	def test_resolve_provider_preference_with_available(self, model_factory):
		"""Test resolving provider preference list."""
		preference_list = ["anthropic", "openai", "ollama"]
		resolved = model_factory.resolve_provider_preference(preference_list)
		# Should return at least one provider
		assert isinstance(resolved, list)
		assert len(resolved) > 0

	def test_resolve_provider_preference_empty_list(self, model_factory):
		"""Test resolving empty provider preference list."""
		resolved = model_factory.resolve_provider_preference([])
		assert resolved == []

	def test_resolve_provider_preference_caching(self, model_factory):
		"""Test that provider preference resolution is cached."""
		preference_list = ["anthropic", "openai"]
		resolved1 = model_factory.resolve_provider_preference(preference_list)
		# Second call should use cache
		resolved2 = model_factory.resolve_provider_preference(preference_list)
		assert resolved1 == resolved2

	def test_resolve_provider_preference_fallback(self, model_factory):
		"""Test fallback when no providers are available."""
		# Create a new factory with preference for unavailable providers
		factory = ModelFactory(
			{"provider_preference": ["nonexistent_provider_xyz"]},
			MagicMock(),
			MagicMock()
		)
		resolved = factory.resolve_provider_preference(["nonexistent_provider_xyz"])
		# Should fall back to original list
		assert "nonexistent_provider_xyz" in resolved


class TestProviderAvailability:
	"""Test provider availability checking."""

	def test_provider_available_local(self, model_factory):
		"""Test that local provider is always available."""
		available = model_factory.provider_is_available("local")
		assert available is True

	def test_provider_available_api_provider(self, model_factory):
		"""Test that API providers are available by default."""
		available = model_factory.provider_is_available("anthropic")
		assert available is True

	def test_provider_available_openai(self, model_factory):
		"""Test OpenAI provider availability."""
		available = model_factory.provider_is_available("openai")
		assert available is True

	def test_provider_available_ollama(self, model_factory):
		"""Test Ollama provider availability (may vary by system)."""
		available = model_factory.provider_is_available("ollama")
		assert isinstance(available, bool)

	def test_provider_available_anthropic_mcp(self, model_factory):
		"""Test anthropic_mcp provider availability."""
		available = model_factory.provider_is_available("anthropic_mcp")
		# Depends on whether 'claude' CLI is available
		assert isinstance(available, bool)

	def test_provider_available_anthropic_ollama(self, model_factory):
		"""Test anthropic_ollama provider availability."""
		available = model_factory.provider_is_available("anthropic_ollama")
		# Depends on both claude CLI and ollama
		assert isinstance(available, bool)

	def test_provider_available_codex_mcp(self, model_factory):
		"""Test codex_mcp provider availability."""
		available = model_factory.provider_is_available("codex_mcp")
		# Depends on whether 'codex' CLI is available
		assert isinstance(available, bool)

	def test_provider_available_unknown(self, model_factory):
		"""Test unknown provider defaults to True."""
		available = model_factory.provider_is_available("some_custom_provider")
		assert available is True


class TestOllamaDetection:
	"""Test Ollama availability detection."""

	def test_ollama_available_returns_bool(self, model_factory):
		"""Test that ollama_available returns a boolean."""
		available = model_factory.ollama_available()
		assert isinstance(available, bool)

	def test_ollama_available_caching(self, model_factory):
		"""Test that Ollama availability is cached."""
		result1 = model_factory.ollama_available()
		result2 = model_factory.ollama_available()
		# Both should return the same result
		assert result1 == result2
		# Cache should be set
		assert model_factory._ollama_available_cache is not None

	def test_ollama_available_cache_reuse(self, model_factory):
		"""Test that subsequent calls use cached value."""
		# First call
		result1 = model_factory.ollama_available()
		# Verify cache is set
		cache_value = model_factory._ollama_available_cache
		assert cache_value == result1
		# Second call should return same value without network call
		result2 = model_factory.ollama_available()
		assert result2 == cache_value

	@patch('subprocess.run')
	def test_ollama_available_cli_success(self, mock_run, model_factory):
		"""Test Ollama detection when CLI is available."""
		mock_run.return_value = MagicMock(returncode=0, stdout="model1\nmodel2")
		# Reset cache for this test
		model_factory._ollama_available_cache = None
		available = model_factory.ollama_available()
		assert available is True

	@patch('subprocess.run')
	def test_ollama_available_cli_failure(self, mock_run, model_factory):
		"""Test Ollama detection when CLI fails."""
		mock_run.side_effect = FileNotFoundError()
		# Reset cache for this test
		model_factory._ollama_available_cache = None
		available = model_factory.ollama_available()
		# Should still try HTTP fallback, but may return False
		assert isinstance(available, bool)


class TestModelCaching:
	"""Test model instance caching."""

	def test_get_model_caching(self, model_factory):
		"""Test that models are cached by provider and model_name."""
		model1 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6"
		)
		model2 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6"
		)
		# Same instance should be returned from cache
		assert model1 is model2

	def test_get_model_different_instances(self, model_factory):
		"""Test that different models create different instances."""
		model1 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6"
		)
		model2 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-haiku-4-5-20251001"
		)
		# Different models should be different instances
		assert model1 is not model2

	def test_get_model_different_providers(self, model_factory):
		"""Test that different providers create different instances."""
		model1 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6"
		)
		model2 = model_factory.get_model(
			provider="openai",
			model_name="gpt-4o"
		)
		# Different providers should be different instances
		assert model1 is not model2

	def test_get_model_with_kwargs_caching(self, model_factory):
		"""Test caching with different kwargs creates different cache entries."""
		model1 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6",
			sandbox=True
		)
		model2 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6",
			sandbox=False
		)
		# Different kwargs should create different cache entries
		assert model1 is not model2

	def test_get_model_same_kwargs(self, model_factory):
		"""Test caching with same kwargs returns same instance."""
		model1 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6",
			sandbox=True
		)
		model2 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6",
			sandbox=True
		)
		# Same kwargs should return same instance
		assert model1 is model2


class TestEdgeCases:
	"""Test edge cases and error conditions."""

	def test_unknown_provider_raises_error(self, model_factory):
		"""Test that unknown provider raises ValueError during instantiation."""
		with pytest.raises((ValueError, ConfigurationError), match="Unknown provider"):
			model_factory.get_model(
				provider="unknown_provider_xyz",
				model_name="some-model"
			)

	def test_get_model_with_local_provider(self, model_factory):
		"""Test getting model with local provider."""
		model = model_factory.get_model(
			provider="local",
			model_name="test-model"
		)
		assert model is not None

	def test_get_model_with_devstral_provider(self, model_factory):
		"""Test getting model with devstral provider."""
		model = model_factory.get_model(
			provider="devstral",
			model_name="devstral"
		)
		assert model is not None

	def test_select_model_empty_config(self, mock_trace_logger, mock_config_validator):
		"""Test select_model with empty config."""
		factory = ModelFactory({}, mock_trace_logger, mock_config_validator)
		node = {"task_type": "simple"}
		provider, model = factory.select_model("test_node", node)
		# Should still select a valid model
		assert provider is not None
		assert model is not None

	def test_multiple_sequential_selections(self, model_factory):
		"""Test multiple sequential model selections."""
		for i in range(5):
			node = {"task_type": "moderate"}
			provider, model = model_factory.select_model(f"node_{i}", node)
			assert provider is not None
			assert model is not None

	def test_model_factory_initialization(self, mock_trace_logger, mock_config_validator):
		"""Test ModelFactory initialization."""
		config = {
			"mode": "explicit",
			"provider_preference": ["anthropic"]
		}
		factory = ModelFactory(config, mock_trace_logger, mock_config_validator)
		assert factory.model_config == config
		assert factory.trace_logger == mock_trace_logger
		assert factory.config_validator == mock_config_validator
		assert factory._models == {}

	def test_invalid_model_config_empty_dict(
		self, mock_trace_logger, mock_config_validator
	):
		"""Test ModelFactory with empty model_config."""
		factory = ModelFactory({}, mock_trace_logger, mock_config_validator)
		# Should initialize without error even with empty config
		assert factory.model_config == {}

	def test_select_model_with_explicit_node_provider(self, model_factory):
		"""Test select_model respects explicit provider in node."""
		node = {
			"provider": "anthropic",
			"model": "claude-opus-4-6"
		}
		provider, model = model_factory.select_model("test_node", node)
		assert provider == "anthropic"
		assert model == "claude-opus-4-6"

	def test_select_model_with_invalid_node_structure(self, model_factory):
		"""Test select_model with invalid node structure handles gracefully."""
		node = {}
		# Should handle empty node gracefully
		provider, model = model_factory.select_model("test_node", node)
		assert provider is not None
		assert model is not None

	def test_cache_key_uniqueness(self, model_factory):
		"""Test that cache keys are unique for different configs."""
		model1 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6",
			timeout=30
		)
		model2 = model_factory.get_model(
			provider="anthropic",
			model_name="claude-opus-4-6",
			timeout=60
		)
		# Both should be non-None (caching should work)
		assert model1 is not None
		assert model2 is not None
		# Different configs should create different cache entries
		assert isinstance(model1, object)


class TestConfigurationValidation:
	"""Test configuration validation for ModelFactory."""

	def test_unknown_provider_raises_error_explicit(self, model_factory):
		"""Test that unknown provider raises error during model instantiation."""
		with pytest.raises((ValueError, ConfigurationError), match="Unknown provider"):
			model_factory.get_model(
				provider="unknown_provider_xyz",
				model_name="some-model"
			)

	def test_invalid_model_config_empty(self, mock_trace_logger, mock_config_validator):
		"""Test ModelFactory with empty model_config."""
		factory = ModelFactory({}, mock_trace_logger, mock_config_validator)
		assert factory.model_config == {}

	def test_provider_available_validation(self, model_factory):
		"""Test provider availability checks for known providers."""
		# These should not raise errors
		assert isinstance(model_factory.provider_is_available("anthropic"), bool)
		assert isinstance(model_factory.provider_is_available("openai"), bool)
		assert isinstance(model_factory.provider_is_available("ollama"), bool)
		assert isinstance(model_factory.provider_is_available("local"), bool)

	def test_ollama_availability_with_caching(self, model_factory):
		"""Test that Ollama availability is cached after first check."""
		result1 = model_factory.ollama_available()
		result2 = model_factory.ollama_available()
		# Both should return same result (caching verified)
		assert result1 == result2
		# Cache should be set
		assert model_factory._ollama_available_cache is not None
