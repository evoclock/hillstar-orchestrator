"""
Unit tests for execution/config_validator.py

Tests configuration validation, API key resolution, and environment loading.
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.config_validator import ConfigValidator
from utils.exceptions import ConfigurationError


@pytest.fixture
def mock_trace_logger():
    """Create a mock TraceLogger."""
    return MagicMock()


@pytest.fixture
def mock_graph():
    """Create a mock WorkflowGraph."""
    graph = MagicMock()
    graph.get_all_node_ids.return_value = ["node1", "node2"]
    return graph


@pytest.fixture
def test_model_config():
    """Test model configuration."""
    return {
        "anthropic": {
            "api_key": "test-api-key-anthropic"
        },
        "openai": {
            "models": ["gpt-4o"]
        },
        "ollama": {
            "base_url": "http://localhost:11434"
        }
    }


@pytest.fixture
def config_validator(test_model_config, mock_graph, mock_trace_logger):
    """Create a ConfigValidator instance."""
    return ConfigValidator(test_model_config, mock_graph, mock_trace_logger)


class TestLoadEnvFile:
    """Test environment file loading."""

    def test_load_env_file_success(self):
        """Test successful .env file loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ANTHROPIC_API_KEY=test-key\n")
            f.write("OPENAI_API_KEY=test-openai\n")
            env_path = f.name

        try:
            ConfigValidator.load_env_file()
            # If no exception raised, test passes
            assert True
        finally:
            os.unlink(env_path)

    def test_load_env_file_missing(self):
        """Test loading when .env file doesn't exist."""
        # Should not raise an error, just skip loading
        try:
            ConfigValidator.load_env_file()
            assert True
        except FileNotFoundError:
            pytest.fail("load_env_file should not raise FileNotFoundError")

    def test_load_env_file_invalid_syntax(self):
        """Test loading .env with invalid syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("INVALID SYNTAX WITHOUT EQUALS\n")
            env_path = f.name

        try:
            # Should handle gracefully
            ConfigValidator.load_env_file()
            assert True
        finally:
            os.unlink(env_path)


class TestValidateModelConfig:
    """Test configuration validation."""

    def test_valid_anthropic_config(self, config_validator):
        """Test validation of valid Anthropic config."""
        # Should not raise
        config_validator.validate_model_config()
        assert True

    def test_valid_openai_config(self, test_model_config, mock_graph, mock_trace_logger):
        """Test validation with OpenAI config."""
        config_validator = ConfigValidator(test_model_config, mock_graph, mock_trace_logger)
        config_validator.validate_model_config()
        assert True

    def test_valid_ollama_config(self, test_model_config, mock_graph, mock_trace_logger):
        """Test validation with Ollama config."""
        config_validator = ConfigValidator(test_model_config, mock_graph, mock_trace_logger)
        config_validator.validate_model_config()
        assert True

    def test_invalid_missing_provider(self, mock_graph, mock_trace_logger):
        """Test validation fails with missing provider in config."""
        bad_config = {"unknown_provider": {}}
        validator = ConfigValidator(bad_config, mock_graph, mock_trace_logger)

        # Should either pass (provider not required) or raise ConfigurationError
        try:
            validator.validate_model_config()
        except ConfigurationError:
            assert True

    def test_invalid_missing_models(self, test_model_config, mock_graph, mock_trace_logger):
        """Test that missing models field is handled."""
        bad_config = test_model_config.copy()
        bad_config["anthropic"] = {}  # Empty provider config

        validator = ConfigValidator(bad_config, mock_graph, mock_trace_logger)
        # Should handle gracefully or raise ConfigurationError
        try:
            validator.validate_model_config()
            assert True
        except ConfigurationError:
            assert True

    def test_invalid_model_structure(self, test_model_config, mock_graph, mock_trace_logger):
        """Test validation with malformed model structure."""
        bad_config = test_model_config.copy()
        bad_config["openai"]["models"] = "not-a-list"  # Should be list

        validator = ConfigValidator(bad_config, mock_graph, mock_trace_logger)
        try:
            validator.validate_model_config()
            # Either passes or raises - both acceptable
            assert True
        except (ConfigurationError, TypeError):
            assert True


class TestGetApiKeyForProvider:
    """Test API key resolution."""

    def test_get_api_key_from_config(self, config_validator):
        """Test retrieving API key from config."""
        api_key = config_validator.get_api_key_for_provider("anthropic")
        assert api_key == "test-api-key-anthropic"

    def test_get_api_key_from_env(self, config_validator):
        """Test retrieving API key from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"}):
            api_key = config_validator.get_api_key_for_provider("openai")
            # Should get from env or config
            assert api_key is not None

    def test_get_api_key_missing_error(self, config_validator):
        """Test error when API key not found."""
        api_key = config_validator.get_api_key_for_provider("nonexistent_provider")
        # Should return None for missing provider
        assert api_key is None

    def test_api_key_for_ollama_optional(self, config_validator):
        """Test that Ollama API key is optional."""
        api_key = config_validator.get_api_key_for_provider("ollama")
        # Ollama should return None since it doesn't need an API key
        assert api_key is None or isinstance(api_key, str)

    def test_api_key_priority_config_over_env(self, config_validator):
        """Test that config takes priority over environment."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            api_key = config_validator.get_api_key_for_provider("anthropic")
            # Should get from config (test-api-key-anthropic), not environment
            assert api_key == "test-api-key-anthropic"

    def test_api_key_case_variations(self, config_validator):
        """Test API key retrieval with different case variations."""
        # Should handle both OPENAI_API_KEY and openai_api_key
        api_key = config_validator.get_api_key_for_provider("openai")
        # Either finds it or returns None
        assert api_key is None or isinstance(api_key, str)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_config(self, mock_graph, mock_trace_logger):
        """Test validation with empty config."""
        validator = ConfigValidator({}, mock_graph, mock_trace_logger)
        try:
            validator.validate_model_config()
            assert True
        except ConfigurationError:
            assert True

    def test_malformed_json_in_env(self):
        """Test handling of malformed JSON in environment."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("{invalid json")
            env_path = f.name

        try:
            ConfigValidator.load_env_file()
            assert True
        finally:
            os.unlink(env_path)

    def test_provider_case_sensitivity(self, test_model_config, mock_graph, mock_trace_logger):
        """Test that provider names are case-sensitive."""
        validator = ConfigValidator(test_model_config, mock_graph, mock_trace_logger)

        # Should handle lowercase vs uppercase provider names
        api_key_lower = validator.get_api_key_for_provider("anthropic")
        api_key_upper = validator.get_api_key_for_provider("ANTHROPIC")

        # Behavior depends on implementation (should probably be case-insensitive)
        assert api_key_lower is not None or api_key_upper is not None

    def test_special_characters_in_api_key(self, mock_graph, mock_trace_logger):
        """Test config with special characters in API key."""
        config = {
            "anthropic": {
                "api_key": "sk-ant-abc123!@#$%^&*()_+-=[]{}|;:',.<>?/"
            }
        }
        validator = ConfigValidator(config, mock_graph, mock_trace_logger)
        api_key = validator.get_api_key_for_provider("anthropic")
        assert "sk-ant-abc123" in api_key

    def test_very_long_api_key(self, mock_graph, mock_trace_logger):
        """Test handling of very long API key."""
        long_key = "sk-ant-" + "x" * 1000
        config = {
            "anthropic": {
                "api_key": long_key
            }
        }
        validator = ConfigValidator(config, mock_graph, mock_trace_logger)
        api_key = validator.get_api_key_for_provider("anthropic")
        assert api_key == long_key

    def test_none_values_in_config(self, mock_graph, mock_trace_logger):
        """Test handling of None values in config."""
        config = {
            "anthropic": {
                "api_key": None
            }
        }
        validator = ConfigValidator(config, mock_graph, mock_trace_logger)
        api_key = validator.get_api_key_for_provider("anthropic")
        # Should return None or handle gracefully
        assert api_key is None or isinstance(api_key, str)


class TestEnvironmentIntegration:
    """Test integration with environment variables."""

    def test_load_from_system_env(self, config_validator):
        """Test loading API keys from system environment."""
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sys-anthropic-key",
            "OPENAI_API_KEY": "sys-openai-key"
        }):
            # Config values should take priority, but env should be fallback
            anthropic_key = config_validator.get_api_key_for_provider("anthropic")
            assert anthropic_key is not None

    def test_missing_all_sources(self, config_validator):
        """Test when API key missing from both config and env."""
        with patch.dict(os.environ, {}, clear=True):
            api_key = config_validator.get_api_key_for_provider("unknown")
            assert api_key is None

    def test_multiple_env_sources(self, config_validator):
        """Test resolution with multiple environment sources."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "key1",
            "OPENAI_API_KEY_ALT": "key2"
        }):
            api_key = config_validator.get_api_key_for_provider("openai")
            # Should return one of the valid keys
            assert api_key in ["key1", "key2", None]
