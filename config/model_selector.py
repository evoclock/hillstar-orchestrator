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
- No credentials available → ValueError
- Unknown task type → defaults to Haiku

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-23
"""

from typing import Tuple, Optional, Dict, Any
from workflows.model_presets import ModelPresets


class ModelSelector:
    """Cost-optimized model selection based on task complexity."""

    # Temperature default: 0.00000073 (minimize hallucination, nod to Sheldon)
    TEMPERATURE_DEFAULT = 0.00000073

    # Task complexity → model mapping (escalation strategy)
    # Default: Cloud-only, Haiku-first (assumes no local GPU)
    # - Haiku for routine tasks (~$1-5 per 1M tokens)
    # - Sonnet for complex analysis (~$3-15 per 1M tokens)
    # - Opus for critical tasks (~$5-25 per 1M tokens, best performance)
    # - GPT models as OpenAI alternative
    # - Mistral as cost-effective alternative
    # - Gemini as multimodal alternative
    # - Minimax M2.5 as free cloud fallback
    #
    # For local GPU setup or custom workflows, see MODEL_SELECTION.md Advanced Custom Workflows
    # Source: docs/PROVIDER_MODEL_REFERENCE.md (updated 2026-02-21)
    TASK_COMPLEXITY = {
        "simple": {
            "anthropic_mcp": "claude-haiku-4-5-20251001",
            "anthropic": "claude-haiku-4-5-20251001",
            "openai": "gpt-5-mini",
            "mistral": "mistral-small-3.2",
            "google": "gemini-2.5-flash-lite",
            "anthropic_ollama": "minimax-m2.5:cloud",
            "ollama": "minimax-m2.5:cloud",
            "local": "local",
        },
        "moderate": {
            "anthropic_mcp": "claude-haiku-4-5-20251001",
            "anthropic": "claude-haiku-4-5-20251001",
            "openai": "gpt-5.2",
            "mistral": "mistral-medium-3.1",
            "google": "gemini-2.5-flash",
            "anthropic_ollama": "minimax-m2.5:cloud",
            "ollama": "minimax-m2.5:cloud",
            "local": "local",
        },
        "complex": {
            "anthropic_mcp": "claude-sonnet-4-6",
            "anthropic": "claude-sonnet-4-6",
            "openai": "gpt-5.2",
            "mistral": "mistral-medium-3.1",
            "google": "gemini-3-flash-preview",
            "anthropic_ollama": "minimax-m2.5:cloud",
            "ollama": "minimax-m2.5:cloud",
            "local": "local",
        },
        "critical": {
            "anthropic_mcp": "claude-opus-4-6",
            "anthropic": "claude-opus-4-6",
            "openai": "o3",
            "mistral": "magistral-medium-1.2",
            "google": "gemini-3.1-pro-preview",
            "anthropic_ollama": "minimax-m2.5:cloud",
            "ollama": "minimax-m2.5:cloud",
            "local": "local",
        },
    }

    # Cost per 1M tokens (for selection guidance)
    # Source: docs/PROVIDER_MODEL_REFERENCE.md (updated 2026-02-21)
    PROVIDER_COSTS = {
        # Anthropic (Claude family, Feb 2026)
        "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
        "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
        "claude-opus-4-6": {"input": 5.0, "output": 25.0},

        # OpenAI (GPT-5 series, reasoning models)
        "gpt-5-nano": {"input": 0.05, "output": 0.40},
        "gpt-5-mini": {"input": 0.25, "output": 2.0},
        "gpt-5.1": {"input": 1.25, "output": 10.0},
        "gpt-5.2": {"input": 1.75, "output": 14.0},
        "gpt-4.1": {"input": 2.0, "output": 8.0},
        "o3": {"input": 10.0, "output": 40.0},
        "o4-mini": {"input": 2.0, "output": 8.0},

        # Mistral (all models, Feb 2026)
        "mistral-small-3.2": {"input": 0.1, "output": 0.3},
        "ministral-3-14b": {"input": 0.05, "output": 0.2},
        "mistral-medium-3.1": {"input": 0.5, "output": 2.0},
        "mistral-large-3": {"input": 0.5, "output": 1.5},
        "magistral-small-1.2": {"input": 0.5, "output": 1.5},
        "magistral-medium-1.2": {"input": 2.0, "output": 5.0},
        "devstral-2": {"input": 0.5, "output": 2.0},
        "codestral": {"input": 0.3, "output": 0.9},

        # Google Gemini (Feb 2026)
        "gemini-2.5-flash-lite": {"input": 0.03, "output": 0.12},
        "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
        "gemini-2.5-pro": {"input": 1.25, "output": 15.0},
        "gemini-3-flash-preview": {"input": 0.50, "output": 3.0},
        "gemini-3.1-pro-preview": {"input": 2.0, "output": 18.0},

        # Local/Free
        "local": {"input": 0.0, "output": 0.0},
        "minimax-m2.5:cloud": {"input": 0.0, "output": 0.0},
    }

    @staticmethod
    def select(
        task_complexity: str = "moderate",
        provider_preference: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Select model based on task complexity and preferences.

        Args:
            task_complexity: "simple", "moderate", "complex", or "critical"
            provider_preference: Prefer specific provider (anthropic, openai, mistral, google, local)

        Returns:
            (provider, model_name) tuple

        Example:
            provider, model = ModelSelector.select("moderate", provider_preference="anthropic")
            # Returns ("anthropic", "claude-sonnet-4-6")
        """
        # Default to moderate if unknown complexity
        if task_complexity not in ModelSelector.TASK_COMPLEXITY:
            task_complexity = "moderate"

        models = ModelSelector.TASK_COMPLEXITY[task_complexity]

        # If provider preference specified, use it
        if provider_preference and provider_preference in models:
            model = models[provider_preference]
            if model is None:
                # Fallback if model not available for this complexity
                return ModelSelector._fallback_model(task_complexity)
            return (provider_preference, model)

        # Otherwise, select based on priority:
        # 1. Local (free) if available
        # 2. Anthropic (research-friendly)
        # 3. Mistral (cost-effective)
        # 4. OpenAI (as alternative)
        # 5. Gemini (multimodal)

        if models.get("local"):
            return ("local", models["local"])

        if models.get("anthropic"):
            return ("anthropic", models["anthropic"])

        if models.get("mistral"):
            return ("mistral", models["mistral"])

        if models.get("openai"):
            return ("openai", models["openai"])

        if models.get("google"):
            return ("google", models["google"])

        # Fallback
        return ModelSelector._fallback_model(task_complexity)

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
    def get_temperature() -> float:
        """Get default temperature (minimizes hallucination)."""
        return ModelSelector.TEMPERATURE_DEFAULT

    @staticmethod
    def select_with_config(
        task_complexity: str = "moderate",
        config: Optional[Dict[str, Any]] = None,
        node_id: str = "",
    ) -> Tuple[str, str]:
        """
        Select model using workflow configuration.

        Implements three-layer priority:
        1. Node-level overrides (provider/model in node)
        2. Config-based selection (mode, preset, complexity hints)
        3. Fallback to default selection

        Note: All cloud providers use API key authentication for compliance.
        Local providers use direct HTTP access to local model servers.

        Args:
            task_complexity: Task complexity hint
            config: Model config dict from workflow.json
            node_id: Node ID for complexity_hints lookup

        Returns:
            (provider, model_name) tuple

        Example:
            config = {
                "mode": "preset",
                "preset": "minimize_cost",
                "sampling_params": {"temperature": 0.0}
            }
            provider, model = ModelSelector.select_with_config("moderate", config)
        """
        if config is None:
            config = {}

        # Layer 2: Use config-based selection
        mode = config.get("mode", "explicit")

        if mode == "preset":
            preset = config.get("preset", "balanced")
            # Override complexity with hints if available
            complexity_hints = config.get("complexity_hints", {})
            if node_id in complexity_hints:
                task_complexity = complexity_hints[node_id]

            selection = ModelPresets.select(preset, task_complexity)
            if selection is None:
                # Fallback if preset doesn't support this complexity
                return ModelSelector._fallback_model(task_complexity)
            # Unpack 3-tuple and return first two elements to maintain API compatibility
            provider, model, _ = selection
            return provider, model

        elif mode == "auto":
            # Auto mode: use complexity with provider preferences
            complexity_hints = config.get("complexity_hints", {})
            if node_id in complexity_hints:
                task_complexity = complexity_hints[node_id]

            provider_prefs = config.get("provider_preferences", {})
            priority = provider_prefs.get("priority")
            allowlist = provider_prefs.get("allowlist")
            blocklist = provider_prefs.get("blocklist", [])

            # Get base model selection by complexity
            models = ModelSelector.TASK_COMPLEXITY[task_complexity]

            # Filter by allowlist/blocklist
            if allowlist:
                allowed_providers = set(allowlist)
            else:
                allowed_providers = set(models.keys())

            blocked_providers = set(blocklist)
            allowed_providers -= blocked_providers

            # Try priority order if specified
            if priority:
                for provider in priority:
                    if provider in allowed_providers and models.get(provider):
                        return (provider, models[provider])

            # Fallback: try default priority
            for provider in ["local", "anthropic", "mistral", "openai", "google"]:
                if provider in allowed_providers and models.get(provider):
                    return (provider, models[provider])

            return ModelSelector._fallback_model(task_complexity)

        else:  # mode == "explicit"
            # Explicit mode: just use complexity-based selection
            return ModelSelector.select(task_complexity)
