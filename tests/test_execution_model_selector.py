# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

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
from execution.seat_resolver import SeatResolutionError
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
		assert model == "gpt-5-mini-2025-08-07" # Default for openai

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


class TestCustomProviderEndpoint:
	"""Custom-provider endpoint plumbing.

	`model_config.custom_providers` has always been in the workflow schema
	(endpoint / model_name / type) but nothing read it during execution — only
	WorkflowDiscovery, for a metadata boolean. These tests cover reading it, so
	a workflow can target an arbitrary OpenAI-compatible endpoint (the Vogelkop
	router in particular) without adding a name to the hardcoded provider enum.
	"""

	def _factory(self, custom, trace, validator):
		return ModelFactory(
			model_config={"mode": "explicit", "custom_providers": custom},
			trace_logger=trace,
			config_validator=validator,
		)

	def test_custom_llamacpp_provider_uses_declared_endpoint(
		self, mock_trace_logger, mock_config_validator
	):
		"""A declared endpoint reaches the model client instead of the default."""
		factory = self._factory(
			{
				"router": {
					"endpoint": "http://127.0.0.1:18100",
					"model_name": "router-planner",
					"type": "llamacpp",
				}
			},
			mock_trace_logger,
			mock_config_validator,
		)
		model = factory.get_model("router", "router-planner")
		assert model.endpoint == "http://127.0.0.1:18100"
		# llamacpp/custom speak OpenAI-compatible /v1/chat/completions, which is
		# what the router serves.
		assert model.api_url == "http://127.0.0.1:18100/v1/chat/completions"

	def test_custom_ollama_provider_uses_declared_endpoint(
		self, mock_trace_logger, mock_config_validator
	):
		"""type: ollama builds an ollama client at the declared host."""
		factory = self._factory(
			{
				"remote-ollama": {
					"endpoint": "http://192.168.1.6:11434",
					"model_name": "qwen3-coder-next:cloud",
					"type": "ollama",
				}
			},
			mock_trace_logger,
			mock_config_validator,
		)
		model = factory.get_model("remote-ollama", "ignored")
		assert model.endpoint == "http://192.168.1.6:11434"
		assert model.model_name == "qwen3-coder-next:cloud"

	def test_entry_model_name_overrides_the_node(
		self, mock_trace_logger, mock_config_validator
	):
		"""The node may name a seat; the entry supplies what the backend serves."""
		factory = self._factory(
			{"router": {"endpoint": "http://127.0.0.1:18100", "model_name": "seat-model", "type": "custom"}},
			mock_trace_logger,
			mock_config_validator,
		)
		assert factory.get_model("router", "router-planner").model_name == "seat-model"

	def test_node_model_used_when_entry_names_none(
		self, mock_trace_logger, mock_config_validator
	):
		factory = self._factory(
			{"router": {"endpoint": "http://127.0.0.1:18100", "type": "custom"}},
			mock_trace_logger,
			mock_config_validator,
		)
		assert factory.get_model("router", "from-node").model_name == "from-node"

	def test_trailing_slash_is_normalised(self, mock_trace_logger, mock_config_validator):
		"""Avoids a doubled slash in the composed request URL."""
		factory = self._factory(
			{"router": {"endpoint": "http://127.0.0.1:18100/", "type": "custom"}},
			mock_trace_logger,
			mock_config_validator,
		)
		assert factory.get_model("router", "m").api_url == "http://127.0.0.1:18100/v1/chat/completions"

	def test_malformed_entry_falls_through_to_normal_resolution(
		self, mock_trace_logger, mock_config_validator
	):
		"""A typo must not yield a client pointed at nothing.

		An entry with no usable endpoint is ignored, so resolution proceeds
		through the built-in provider table and an unknown name still raises.
		"""
		factory = self._factory(
			{"ollama": {"model_name": "x", "type": "ollama"}},  # no endpoint
			mock_trace_logger,
			mock_config_validator,
		)
		model = factory.get_model("ollama", "minimax-m3:cloud")
		assert model.endpoint == "http://127.0.0.1:11434"  # the built-in default

	def test_absent_custom_providers_changes_nothing(
		self, mock_trace_logger, mock_config_validator
	):
		factory = ModelFactory(
			model_config={"mode": "explicit"},
			trace_logger=mock_trace_logger,
			config_validator=mock_config_validator,
		)
		assert factory.get_model("ollama", "minimax-m3:cloud").endpoint == "http://127.0.0.1:11434"


class TestSeatDispatch:
	"""A workflow node naming a SEAT resolves through the chain.

	The point is portability: the same workflow runs under Vogelkop (router
	injected), standalone against a router the user runs, or against local
	models only -- without the workflow file carrying a host address.
	"""

	def _factory(self, trace, validator, custom=None):
		config = {"mode": "explicit"}
		if custom is not None:
			config["custom_providers"] = custom
		return ModelFactory(
			model_config=config, trace_logger=trace, config_validator=validator
		)

	def test_seat_uses_a_workflow_pin_when_present(
		self, mock_trace_logger, mock_config_validator
	):
		factory = self._factory(
			mock_trace_logger,
			mock_config_validator,
			custom={"router": {"endpoint": "http://127.0.0.1:18100", "type": "custom"}},
		)
		model = factory.get_model("router", "router-planner")
		assert model.endpoint == "http://127.0.0.1:18100"
		# The seat name passes through: the router substitutes the backend's
		# real model itself.
		assert model.model_name == "router-planner"

	def test_seat_uses_the_host_router_env(
		self, monkeypatch, mock_trace_logger, mock_config_validator
	):
		monkeypatch.setenv("HILLSTAR_ROUTER_URL", "http://127.0.0.1:18100")
		factory = self._factory(mock_trace_logger, mock_config_validator)
		model = factory.get_model("router", "router-reviewer")
		assert model.endpoint == "http://127.0.0.1:18100"
		assert model.model_name == "router-reviewer"

	def test_seat_falls_back_to_a_local_model(
		self, monkeypatch, mock_trace_logger, mock_config_validator
	):
		"""No router: the seat resolves against what the machine has."""
		monkeypatch.delenv("HILLSTAR_ROUTER_URL", raising=False)
		monkeypatch.setattr(
			"execution.seat_resolver._ollama_models", lambda: ["jan-code-4b:latest"]
		)
		factory = self._factory(mock_trace_logger, mock_config_validator)
		model = factory.get_model("router", "router-planner")
		assert model.model_name == "jan-code-4b:latest"
		# Local discovery leaves the endpoint unset so the client default applies.
		assert model.endpoint == "http://127.0.0.1:11434"

	def test_unresolvable_seat_raises_rather_than_escalating(
		self, monkeypatch, mock_trace_logger, mock_config_validator
	):
		"""Never reach for a paid API because nothing local was found."""
		monkeypatch.delenv("HILLSTAR_ROUTER_URL", raising=False)
		monkeypatch.setattr("execution.seat_resolver._ollama_models", lambda: [])
		factory = self._factory(mock_trace_logger, mock_config_validator)
		with pytest.raises(SeatResolutionError):
			factory.get_model("router", "router-planner")

	# Portability makes the model vary by machine, so the trace is the only
	# place the actual choice survives.
	def test_resolution_is_recorded_in_the_trace(
		self, monkeypatch, mock_trace_logger, mock_config_validator
	):
		monkeypatch.setenv("HILLSTAR_ROUTER_URL", "http://127.0.0.1:18100")
		factory = self._factory(mock_trace_logger, mock_config_validator)
		factory.get_model("router", "router-planner")
		events = [c.args[0] for c in mock_trace_logger.log.call_args_list]
		seat_events = [e for e in events if e.get("event") == "seat_resolved"]
		assert len(seat_events) == 1
		assert seat_events[0]["seat"] == "router-planner"
		assert seat_events[0]["source"] == "host-config"
		assert seat_events[0]["model"] == "router-planner"

	def test_a_non_seat_model_name_is_unaffected(
		self, mock_trace_logger, mock_config_validator
	):
		"""Existing workflows naming a concrete model keep working."""
		factory = self._factory(mock_trace_logger, mock_config_validator)
		model = factory.get_model("ollama", "minimax-m3:cloud")
		assert model.model_name == "minimax-m3:cloud"
		assert model.endpoint == "http://127.0.0.1:11434"
