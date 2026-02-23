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
- Unknown provider → ValueError
- Missing API key → Model handles error
- Ollama unavailable → Check fails, other providers tried
- Local tool missing → Marked unavailable

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
import urllib.request
from datetime import datetime
from .trace import TraceLogger
from .config_validator import ConfigValidator
from models import (
    AnthropicOllamaAPIModel,
    AnthropicModel,
    AnthropicMCPModel,
    DevstralLocalModel,
    MistralAPIModel,
    OpenAIMCPModel,
    MistralMCPModel,
    OllamaMCPModel,
)
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
                "local": "local",
                "anthropic": "claude-haiku-4-5-20251001",
                "openai": "gpt-4o",
                "ollama": "minimax-m2:cloud",
                "anthropic_mcp": "claude-sonnet-4-5-20250929",
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
            self.trace_logger.log({
                "timestamp": datetime.now().isoformat(),
                "event": "provider_preference_resolved",
                "resolution_status": resolution_status,
                "original_preference": provider_preference,
                "resolved_preference": resolved,
                "availability": availability,
            })
            self._provider_resolution_logged = True

        return resolved

    def provider_is_available(self, provider: str) -> bool:
        """Check if a provider appears available based on local tools/endpoints."""
        if provider in ["local"]:
            return True

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
                with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5):
                    available = True
            except Exception:
                available = False

        self._ollama_available_cache = available
        return available

    def get_model(self, provider: str, model_name: str, **kwargs):
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
        key = f"{provider}:{model_name}:{extra_key}" if extra_key else f"{provider}:{model_name}"

        if key not in self._models:
            # Reload anthropic_ollama module to ensure latest fixes
            if provider == "anthropic_ollama":
                import sys
                if 'hillstar.models.anthropic_ollama_api_model' in sys.modules:
                    importlib.reload(sys.modules['hillstar.models.anthropic_ollama_api_model'])
            # Get API key from config or environment (for providers that need it)
            api_key = self.config_validator.get_api_key_for_provider(provider)

            if provider == "anthropic":
                self._models[key] = AnthropicModel(model_name, api_key=api_key)
            elif provider == "anthropic_ollama":
                self._models[key] = AnthropicOllamaAPIModel(
                    model_name=model_name
                )
            elif provider == "anthropic_mcp":
                self._models[key] = AnthropicMCPModel(model_name, api_key=api_key)
            elif provider in ("openai", "openai_mcp"):
                self._models[key] = OpenAIMCPModel(model_name, api_key=api_key)
            elif provider == "mistral":
                self._models[key] = MistralAPIModel(model_name, api_key=api_key)
            elif provider == "mistral_mcp":
                self._models[key] = MistralMCPModel(model_name, api_key=api_key)
            elif provider == "ollama_mcp":
                self._models[key] = OllamaMCPModel(model_name)
            elif provider in ["devstral", "devstral_local", "local"]:
                self._models[key] = DevstralLocalModel(model_name)
            else:
                raise ValueError(f"Unknown provider: {provider}")

        return self._models[key]
