"""
Model Selection Presets

PURPOSE:
--------
Data-driven preset system for intelligent model selection with
temperature constraint enforcement. Provides four strategies (cost_saver,
balanced, quality_first, premium) for different research contexts.

ARCHITECTURE:
-------------
- PresetResolver: resolves (preset, complexity) to
  (provider, model, suggested_parameters)
- Data-driven tier assignment based on pricing formulas (not hardcoded)
- Parameter support inference with fallback logic for registry gaps
- Non-negotiable temperature constraints enforced per model class
- Backward compatibility: legacy ModelPresets class preserved

USAGE:
------
resolver = PresetResolver(
    preset_name="balanced",
    configured_providers=["openai", "anthropic"]
)
provider, model_id, params = resolver.resolve(
    complexity="moderate",
    use_case="code_writing"
)

CONSTRAINTS (Non-Negotiable):
------------------------------
- General tasks: Temperature <= 0.3
- Code writing: Temperature = 7.3e-7
- Codebase exploration: 0.7 (Devstral-2 only)
- Claude/OpenAI/Gemini: NO temperature (use effort/thinking)
- Mistral: 0.3-1.0 for exploration
- Local models: <= 0.15

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ====== Tier Assignment Strategy ======
# Effective cost = (input_cost + output_cost) / 2 per 1M tokens
#
# TIER_0_COST: $0/1M (free models)
# TIER_1_COST: $0-$1/1M (ultra-budget)
# TIER_2_BALANCED: $1-$5/1M (balanced cost/quality)
# TIER_3_QUALITY: $5-$20/1M (high quality)
# TIER_4_MAX_QUALITY: $20+/1M (frontier)

TIER_NAMES = [
    "TIER_0_COST",
    "TIER_1_COST",
    "TIER_2_BALANCED",
    "TIER_3_QUALITY",
    "TIER_4_MAX_QUALITY",
]

# Preset tier sequences - each preset uses a sequence of tiers
# Resolver escalates through these tiers based on complexity
# NOTE: Registry uses mixed tier naming
#       (old: cheap/standard/expensive; new: TIER_0_COST/etc)
# Resolver handles both formats
PRESET_TIERS: Dict[str, List[str]] = {
    "cost_saver": [
        "free",
        "cheap",
        "TIER_0_COST",
        "TIER_1_COST",
    ],
    "balanced": [
        "cheap",
        "standard",
        "TIER_1_COST",
        "TIER_2_BALANCED",
    ],
    "quality_first": [
        "standard",
        "expensive",
        "TIER_2_BALANCED",
        "TIER_3_QUALITY",
    ],
    "premium": [
        "expensive",
        "TIER_3_QUALITY",
        "TIER_4_MAX_QUALITY",
    ],
}


def parse_price_field(price_str: str) -> float:
    """
    Convert markdown price field (e.g., '$0.12', '$0', '$8') to float.

    Args:
        price_str: Price string from markdown table

    Returns:
        Float price per 1M tokens

    Raises:
        ValueError: If price string cannot be parsed
    """
    try:
        # Remove "$" and any whitespace
        clean = price_str.strip().replace("$", "").replace(",", "")
        return float(clean)
    except ValueError:
        raise ValueError(f"Cannot parse price: {price_str}")


def derive_tier_for_model(input_price: float, output_price: float) -> str:
    """
    Derive tier name based on effective cost.

    Effective cost = (input_price + output_price) / 2 per 1M tokens

    Args:
        input_price: Price per 1M input tokens
        output_price: Price per 1M output tokens

    Returns:
        Tier name (TIER_0_COST through TIER_4_MAX_QUALITY)
    """
    effective_cost = (input_price + output_price) / 2

    if effective_cost == 0:
        return "TIER_0_COST"
    elif effective_cost <= 1:
        return "TIER_1_COST"
    elif effective_cost <= 5:
        return "TIER_2_BALANCED"
    elif effective_cost <= 20:
        return "TIER_3_QUALITY"
    else:
        return "TIER_4_MAX_QUALITY"


def parse_model_reference(markdown_path: str) -> Dict[str, Any]:
    """
    Parse PROVIDER_MODEL_REFERENCE markdown to extract model metadata.

    Extracts pricing (including cached input + cache storage), context windows,
    parameter support flags, and temperature guidance from the markdown file.

    Handles pricing columns:
    - input_price: Base input tokens
    - cached_input: Cached input tokens (prompt caching)
    - output_price: Output tokens
    - cache_storage: Cache storage cost (Google models)

    Args:
        markdown_path: Path to PROVIDER_MODEL_REFERENCE.md

    Returns:
        Dict with structure: {provider: {model_name: {pricing, context, flags, ...}}}
    """
    result: Dict[str, Any] = {}

    if not Path(markdown_path).exists():
        raise FileNotFoundError(f"Reference file not found: {markdown_path}")

    with open(markdown_path, "r") as f:
        content = f.read()

    # Split by provider sections (##. Provider Name)
    provider_pattern = r"^## (.+?)$"
    sections = re.split(provider_pattern, content, flags=re.MULTILINE)

    # Process pairs (provider_name, section_content)
    for i in range(1, len(sections), 2):
        provider_name = sections[i].strip().lower()
        section_content = sections[i + 1] if i + 1 < len(sections) else ""

        # Simplify provider name (e.g., "Anthropic Models" -> "anthropic")
        provider_key = provider_name.split()[0]
        if provider_key not in result:
            result[provider_key] = {}

        # Parse markdown tables in this section
        # Table format: | Model | ... | Price | ...
        table_pattern = r"\|\s*\*\*([^|\*]+)\*\*\s*\|"
        matches = re.finditer(table_pattern, section_content)

        for match in matches:
            model_name = match.group(1).strip()
            # Extract pricing from the same line or nearby
            line_start = max(0, match.start() - 200)
            line_end = min(len(section_content), match.end() + 400)
            context = section_content[line_start:line_end]

            # Try to extract pricing
            price_pattern = r"\$[\d.]+(?:/1M|k)?"
            price_matches = re.findall(price_pattern, context)

            if price_matches and model_name not in result[provider_key]:
                try:
                    # For models with input/output pricing
                    if len(price_matches) >= 2:
                        input_price = parse_price_field(price_matches[0])
                        output_price = parse_price_field(price_matches[1])
                    elif len(price_matches) == 1:
                        # Single price, use as both
                        price = parse_price_field(price_matches[0])
                        input_price = price
                        output_price = price
                    else:
                        continue

                    tier = derive_tier_for_model(input_price, output_price)

                    # Extract cached input if available (3rd price)
                    cached_input_price = None
                    if len(price_matches) >= 3:
                        try:
                            cached_input_price = parse_price_field(
                                price_matches[2]
                            )
                        except ValueError:
                            pass

                    # Extract cache storage if available (4th price, Google only)
                    cache_storage_price = None
                    if len(price_matches) >= 4:
                        try:
                            cache_storage_price = parse_price_field(
                                price_matches[3]
                            )
                        except ValueError:
                            pass

                    result[provider_key][model_name] = {
                        "input_price_per_mil": input_price,
                        "cached_input_price_per_mil": cached_input_price,
                        "output_price_per_mil": output_price,
                        "cache_storage_per_mil_per_hour": cache_storage_price,
                        "effective_cost": (input_price + output_price) / 2,
                        "derived_tier": tier,
                    }
                except ValueError:
                    # Skip models where pricing couldn't be parsed
                    pass

    return result


def build_provider_tiers(registry_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Build PROVIDER_TIERS mapping from registry: {provider: {tier: [models]}}.

    Args:
        registry_path: Path to provider_registry.default.json

    Returns:
        Dict mapping providers to tier-to-models mapping
    """
    provider_tiers: Dict[str, Dict[str, List[str]]] = {}

    if not Path(registry_path).exists():
        return provider_tiers

    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Iterate providers and models
    for provider_name, provider_data in registry.get("providers", {}).items():
        if provider_name.startswith("_"):  # Skip metadata keys
            continue

        provider_tiers[provider_name] = {}

        # For each model in this provider
        for model_name, model_config in provider_data.get("models", {}).items():
            # Get tier from model config or derive it
            tier = model_config.get("tier")
            if not tier:
                # Try to derive from pricing
                pricing = model_config.get("pricing", {})
                input_price = pricing.get("input_per_1m_usd", 0)
                output_price = pricing.get("output_per_1m_usd", 0)
                tier = derive_tier_for_model(input_price, output_price)

            # Add model to tier list
            if tier not in provider_tiers[provider_name]:
                provider_tiers[provider_name][tier] = []
            provider_tiers[provider_name][tier].append(model_name)

    return provider_tiers


class PresetResolver:
    """
    Data-driven model resolver that enforces temperature and parameter constraints.

    Selects models based on preset tier sequences, complexity escalation,
    and enforces all non-negotiable temperature rules per model class.
    """

    def __init__(
        self,
        preset_name: str,
        configured_providers: List[str],
        registry_path: Optional[str] = None,
    ):
        """
        Initialize resolver with preset and available providers.

        Args:
            preset_name: One of cost_saver, balanced, quality_first, premium
            configured_providers: List of provider names in preference order
            registry_path: Optional path to provider_registry.default.json
                          (defaults to standard location)
        """
        if preset_name not in PRESET_TIERS:
            raise ValueError(
                f"Unknown preset: {preset_name}. "
                f"Valid presets: {list(PRESET_TIERS.keys())}"
            )

        self.preset_name = preset_name
        self.configured_providers = configured_providers
        self.tier_sequence = PRESET_TIERS[preset_name]

        # Load registry
        if registry_path is None:
            # Default to standard location
            # Path: workflows/model_presets.py -> workflows -> (root)
            script_dir = Path(__file__).parent  # workflows
            root_dir = script_dir.parent  # root
            registry_path = str(root_dir / "config" / "provider_registry.default.json")

        self.registry_path = registry_path
        self._load_registry()

    def _load_registry(self) -> None:
        """Load provider registry from JSON file."""
        if not Path(self.registry_path).exists():
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")

        with open(self.registry_path, "r") as f:
            self.registry = json.load(f)

        # Build PROVIDER_TIERS cache
        self.provider_tiers = build_provider_tiers(self.registry_path)

    def resolve(
        self,
        complexity: str = "moderate",
        use_case: Optional[str] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        Resolve (preset, complexity) to (provider, model, suggested_parameters).

        Enforces all non-negotiable temperature constraints:
        - Temperature <= 0.3 for general tasks (all providers)
        - Temperature 0.7 ONLY for Devstral-2 + codebase_exploration
        - Temperature 0.00000073 for code_writing (any model)
        - No temperature for Claude/OpenAI/Gemini (use effort/thinking)
        - Mistral: allow 0.3-1.0 for exploration tasks
        - devstral-small-2 (local): CRITICAL cap <= 0.15

        Args:
            complexity: simple, moderate, complex, critical
            use_case: Optional use case context
                     (general, codebase_exploration, code_writing, etc.)

        Returns:
            Tuple of (provider, model_id, suggested_parameters) or None

            suggested_parameters contains:
            - temperature (if supported by model)
            - reasoning_effort or thinking (if reasoning model)
            - max_tokens
            - context_window
            - supports_temperature, supports_thinking, supports_reasoning_effort
        """
        if complexity not in ["simple", "moderate", "complex", "critical"]:
            raise ValueError(
                f"Invalid complexity: {complexity}. "
                f"Valid: simple, moderate, complex, critical"
            )

        # Map complexity to tier index in the preset sequence
        # simple: prefer lower tiers (earlier in sequence)
        # critical: prefer higher tiers (later in sequence)
        complexity_to_tier_index = {
            "simple": 0,
            "moderate": 1,
            "complex": 1,
            "critical": 2,
        }

        tier_index = complexity_to_tier_index.get(complexity, 1)
        # Clamp to valid range
        tier_index = min(tier_index, len(self.tier_sequence) - 1)

        # Try each tier starting from the preferred one, escalating if needed
        for idx in range(tier_index, len(self.tier_sequence)):
            tier_name = self.tier_sequence[idx]

            # Try each configured provider in order
            # Support provider aliases (e.g., "openai" -> "openai_mcp",
            #                          "anthropic" -> "anthropic_mcp")
            for provider_name in self.configured_providers:
                # Try exact match first, then try with _mcp suffix
                provider_variants = [provider_name]
                if not provider_name.endswith("_mcp"):
                    provider_variants.append(f"{provider_name}_mcp")

                for prov_variant in provider_variants:
                    if prov_variant not in self.provider_tiers:
                        continue

                    # Get models available in this tier for this provider
                    models = self.provider_tiers[prov_variant].get(tier_name, [])
                    if not models:
                        continue

                    # Use first available model
                    model_name = models[0]

                    # Get model config from registry
                    registry_providers = self.registry.get("providers", {})
                    provider_config = registry_providers.get(prov_variant)
                    if not provider_config:
                        continue

                    model_config = provider_config.get("models", {}).get(model_name, {})

                    # Build suggested parameters with constraint enforcement
                    suggested_params = self._build_suggested_parameters(
                        prov_variant, model_name, model_config, complexity, use_case
                    )

                    return (prov_variant, model_name, suggested_params)

        # No matching model found
        return None

    def _build_suggested_parameters(
        self,
        provider_name: str,
        model_name: str,
        model_config: Dict[str, Any],
        complexity: str,
        use_case: Optional[str],
    ) -> Dict[str, Any]:
        """
        Build suggested parameters with constraint enforcement.

        Applies temperature constraints based on model class and use case.
        """
        params: Dict[str, Any] = {}

        # Add context window
        context_window = model_config.get("context_window")
        if context_window:
            params["context_window"] = context_window

        # Add max_tokens suggestion
        max_output = model_config.get("max_output_tokens", 8192)
        params["max_tokens"] = min(max_output, 8192)

        # Get parameter support flags (infer if not explicitly set)
        supports_temp = model_config.get("supports_temperature")
        supports_thinking = model_config.get("supports_thinking")
        supports_reasoning = model_config.get("supports_reasoning_effort")

        # Infer support from model config if not explicitly set
        if supports_temp is None:
            # Check if model has temperature in default params
            has_default_temp = "temperature" in model_config.get(
                "default_sampling_params", {}
            )
            has_default_temp = (
                has_default_temp or
                model_config.get("default_temperature") is not None
            )
            # Mistral, local models, and general models support temperature
            # Claude, OpenAI reasoning, Gemini do NOT
            provider_lower = provider_name.lower()
            model_lower = model_name.lower()
            mistral_local_providers = [
                "mistral", "ollama", "devstral", "local"
            ]
            claude_openai_providers = [
                "claude", "opus", "sonnet", "haiku", "openai", "gpt", "gemini"
            ]
            if any(
                x in provider_lower or x in model_lower
                for x in mistral_local_providers
            ):
                supports_temp = True
            elif any(
                x in provider_lower or x in model_lower
                for x in claude_openai_providers
            ):
                supports_temp = False
            else:
                supports_temp = has_default_temp

        if supports_thinking is None:
            # Claude and Gemini models support thinking
            provider_lower = provider_name.lower()
            model_lower = model_name.lower()
            thinking_providers = [
                "claude", "opus", "sonnet", "haiku", "gemini"
            ]
            supports_thinking = any(
                x in provider_lower or x in model_lower
                for x in thinking_providers
            )

        if supports_reasoning is None:
            # OpenAI reasoning models (GPT-5, o3) support reasoning_effort
            provider_lower = provider_name.lower()
            model_lower = model_name.lower()
            supports_reasoning = any(x in model_lower for x in ["gpt-5", "o3"])

        params["supports_temperature"] = supports_temp
        params["supports_thinking"] = supports_thinking
        params["supports_reasoning_effort"] = supports_reasoning

        # Determine temperature based on model class and use case
        model_lower = model_name.lower()
        provider_lower = provider_name.lower()

        temperature = self._get_temperature_for_model(
            provider_lower, model_lower, complexity, use_case
        )

        if temperature is not None and supports_temp:
            params["temperature"] = temperature

        # Add reasoning_effort/thinking suggestions for reasoning models
        if supports_reasoning:
            effort = self._get_reasoning_effort(complexity)
            params["reasoning_effort"] = effort

        if supports_thinking:
            # Claude/Gemini: suggest thinking effort
            effort = self._get_thinking_effort(complexity)
            params["thinking"] = {
                "type": "adaptive" if "opus" in model_lower else "enabled",
                "effort": effort,
            }

        return params

    def _get_temperature_for_model(
        self,
        provider_lower: str,
        model_lower: str,
        complexity: str,
        use_case: Optional[str],
    ) -> Optional[float]:
        """
        Determine temperature for model based on constraints.

        CRITICAL CONSTRAINTS:
        - Temperature <= 0.3 for general tasks
        - Temperature 0.7 ONLY for devstral-2 + codebase_exploration
        - Temperature 0.00000073 for code_writing
        - NO temperature for Claude/OpenAI/Gemini (use effort/thinking)
        - Mistral: 0.3-1.0 for exploration
        - devstral-small-2 (local): <= 0.15 CRITICAL
        """
        use_case = use_case or "general"

        # Code writing: ABSOLUTE constraint (highest precedence)
        if use_case == "code_writing":
            return 7.3e-7

        # Claude/OpenAI/Gemini: don't use temperature
        non_temp_providers = [
            "claude", "opus", "sonnet", "haiku", "openai", "gpt", "gemini"
        ]
        if any(
            x in provider_lower or x in model_lower
            for x in non_temp_providers
        ):
            return None

        # devstral-small-2 (local): CRITICAL cap <= 0.15
        if "devstral-small-2" in model_lower or "devstral-small-2-24b" in model_lower:
            return 0.1  # Conservative for local

        # devstral-2: 0.7 only for codebase_exploration
        if "devstral-2" in model_lower and "devstral-small" not in model_lower:
            if use_case == "codebase_exploration":
                return 0.7
            else:
                return 0.3

        # Mistral: allow 0.3-1.0 for exploration
        if "mistral" in provider_lower or "mistral" in model_lower:
            if use_case in ["exploration", "codebase_exploration"]:
                return 0.7
            else:
                return 0.3

        # Default: general tasks get <= 0.3
        return 0.3

    def _get_reasoning_effort(self, complexity: str) -> str:
        """Get reasoning_effort level for OpenAI reasoning models."""
        if complexity == "simple":
            return "low"
        elif complexity in ["moderate", "complex"]:
            return "medium"
        else:  # critical
            return "high"

    def _get_thinking_effort(self, complexity: str) -> str:
        """Get thinking effort level for Claude/Gemini models."""
        if complexity == "simple":
            return "low"
        elif complexity in ["moderate", "complex"]:
            return "medium"
        else:  # critical
            return "high"


def parse_and_update_registry(
    reference_path: Optional[str] = None,
    registry_path: Optional[str] = None,
) -> Tuple[int, int]:
    """
    Parse reference markdown and update provider registry.

    This is the main entry point for populating the registry from
    the authoritative PROVIDER_MODEL_REFERENCE markdown file.

    Args:
        reference_path: Path to PROVIDER_MODEL_REFERENCE.md
                        (defaults to docs/PROVIDER_MODEL_REFERENCE.md)
        registry_path: Path to provider_registry.default.json
                       (defaults to python/hillstar/config/
                        provider_registry.default.json)

    Returns:
        Tuple of (models_added, models_updated)
    """
    # Determine default paths
    if reference_path is None:
        # Path: workflows/model_presets.py -> workflows -> root
        script_dir = Path(__file__).parent  # workflows
        root_dir = script_dir.parent  # root
        reference_path = str(root_dir / "docs" / "PROVIDER_MODEL_REFERENCE.md")

    if registry_path is None:
        script_dir = Path(__file__).parent  # workflows
        root_dir = script_dir.parent  # root
        registry_path = str(root_dir / "config" / "provider_registry.default.json")

    # Ensure both are strings
    reference_path = str(reference_path) if not isinstance(reference_path, str) else reference_path
    registry_path = str(registry_path) if not isinstance(registry_path, str) else registry_path

    # Parse reference
    try:
        parsed_data = parse_model_reference(reference_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Cannot parse reference: {e}")

    # Load existing registry
    with open(registry_path, "r") as f:
        registry = json.load(f)

    models_added = 0
    models_updated = 0

    # Update registry with parsed data
    for provider_key, models in parsed_data.items():
        # Ensure provider exists in registry
        if provider_key not in registry.get("providers", {}):
            registry.setdefault("providers", {})[provider_key] = {
                "display_name": provider_key.title(),
                "models": {}
            }

        provider = registry["providers"][provider_key]

        # Update/add models
        for model_name, model_meta in models.items():
            if model_name not in provider.get("models", {}):
                models_added += 1
            else:
                models_updated += 1

            # Ensure model entry exists
            if "models" not in provider:
                provider["models"] = {}

            if model_name not in provider["models"]:
                provider["models"][model_name] = {}

            # Update model with parsed pricing and tier info
            model_entry = provider["models"][model_name]
            model_entry["pricing"] = {
                "input_per_1m_usd": model_meta["input_price_per_mil"],
                "output_per_1m_usd": model_meta["output_price_per_mil"],
            }

            # Add cached input if available
            if model_meta.get("cached_input_price_per_mil") is not None:
                model_entry["pricing"]["cached_input_per_1m_usd"] = (
                    model_meta["cached_input_price_per_mil"]
                )

            # Add cache storage if available (Google models)
            if model_meta.get("cache_storage_per_mil_per_hour") is not None:
                model_entry["pricing"]["cache_storage_per_1m_per_hour_usd"] = (
                    model_meta["cache_storage_per_mil_per_hour"]
                )

            model_entry["tier"] = model_meta["derived_tier"]

    # Set flag indicating registry has been auto-populated
    registry["registry_auto_populated"] = True
    registry["last_updated"] = "2026-02-19"

    # Write updated registry
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)

    return models_added, models_updated


# ====== Backward Compatibility: Legacy ModelPresets class ======
# Kept for compatibility with existing code that imports ModelPresets
# New code should use PresetResolver instead

class ModelPresets:
    """
    Legacy class for backward compatibility.

    New code should use PresetResolver instead.

    Named strategies for model selection based on use case.
    Presets are dynamically generated from the ProviderRegistry.
    """

    # Tier mapping for preset selection
    TIER_MAPPING = {
        "minimize_cost": "cheap",
        "balanced": "standard",
        "maximize_quality": "expensive",
        "local_only": "free",
    }

    # Complexity to capabilities mapping
    CAPABILITY_MAPPING = {
        "simple": ["reasoning", "analysis"],
        "moderate": ["reasoning", "coding", "analysis"],
        "complex": ["reasoning", "coding", "analysis", "complex_planning"],
        "critical": ["reasoning", "coding", "analysis", "complex_planning"],
    }

    @staticmethod
    def select(
        preset_name: str,
        complexity: str = "moderate",
        provider_preference: Optional[List[str]] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        Select model from a preset strategy (legacy).

        Args:
            preset_name: One of "minimize_cost", "balanced", "maximize_quality", "local_only"
            complexity: Task complexity ("simple", "moderate", "complex", "critical")
            provider_preference: Optional list of preferred providers in order

        Returns:
            Tuple of (provider, model_id, model_config), or None if no model available
        """
        # This imports here to avoid circular dependency issues
        from ..config.provider_registry import ProviderRegistry

        if preset_name not in ModelPresets.TIER_MAPPING:
            raise KeyError(
                f"Unknown preset: {preset_name}. "
                f"Valid presets: {list(ModelPresets.TIER_MAPPING.keys())}"
            )

        registry = ProviderRegistry()
        max_tier = ModelPresets.TIER_MAPPING[preset_name]
        required_caps = ModelPresets.CAPABILITY_MAPPING.get(
            complexity, ModelPresets.CAPABILITY_MAPPING["moderate"]
        )

        # Get cheapest matching model
        result = registry.get_cheapest_model(
            capabilities=required_caps,
            provider_preference=provider_preference,
        )

        if result:
            provider, model_id, model_config = result
            # Check tier if not local_only (which is always free)
            if preset_name != "local_only":
                tier_order = ["free", "cheap", "standard", "expensive", "premium"]
                if tier_order.index(model_config.get("tier", "standard")) <= tier_order.index(
                    max_tier
                ):
                    return result

        # Fallback: return None if no model matches criteria
        return None

    @staticmethod
    def select_simple(
        preset_name: str,
        provider_preference: Optional[List[str]] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Select model for simple tasks using a preset."""
        return ModelPresets.select(preset_name, "simple", provider_preference)

    @staticmethod
    def select_moderate(
        preset_name: str,
        provider_preference: Optional[List[str]] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Select model for moderate tasks using a preset."""
        return ModelPresets.select(preset_name, "moderate", provider_preference)

    @staticmethod
    def select_complex(
        preset_name: str,
        provider_preference: Optional[List[str]] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Select model for complex tasks using a preset."""
        return ModelPresets.select(preset_name, "complex", provider_preference)

    @staticmethod
    def select_critical(
        preset_name: str,
        provider_preference: Optional[List[str]] = None,
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Select model for critical tasks using a preset."""
        return ModelPresets.select(preset_name, "critical", provider_preference)

    @staticmethod
    def get_available_presets() -> List[str]:
        """Get list of available preset names."""
        return list(ModelPresets.TIER_MAPPING.keys())

    @staticmethod
    def describe_preset(preset_name: str) -> Dict:
        """Get description of a preset strategy."""
        descriptions = {
            "minimize_cost": {
                "description": "Cheapest reasoning models (Haiku, GPT-5-nano, o3-mini)",
                "use_case": "Budget-constrained labs, high-volume experimentation",
                "pros": [
                    "Minimum cost ($0.10-5.00 per 1M tokens)",
                    "Good for simple/moderate tasks",
                    "Free local option available",
                ],
                "cons": ["Limited model quality for complex tasks"],
                "max_tier": "cheap",
            },
            "balanced": {
                "description": "Mix of providers with intelligent escalation",
                "use_case": "General research, no local GPU requirement",
                "pros": [
                    "Cost-effective ($0.10-15 per 1M tokens)",
                    "Cloud-friendly (no GPU required)",
                    "Good balance of cost and quality",
                ],
                "cons": ["Escalates to costlier models for complex tasks"],
                "max_tier": "standard",
            },
            "maximize_quality": {
                "description": "Best-in-class models (Opus 4.6, GPT-5.2, o3)",
                "use_case": "Research requiring high accuracy (papers, publications)",
                "pros": [
                    "Best results",
                    "Consistent quality",
                    "Handles complex reasoning well",
                ],
                "cons": ["Higher cost ($5-40 per 1M tokens)"],
                "max_tier": "expensive",
            },
            "local_only": {
                "description": "Air-gapped: Only use local models (Devstral via Ollama)",
                "use_case": "Sensitive data, disconnected networks, regulatory compliance",
                "pros": [
                    "Privacy-preserving",
                    "No external dependencies",
                    "Cost-free (once model is downloaded)",
                ],
                "cons": [
                    "Limited to simple/moderate tasks",
                    "Requires local GPU for acceptable performance",
                ],
                "max_tier": "free",
            },
        }
        return descriptions.get(preset_name, {})

    @staticmethod
    def get_preset_for_use_case(
        use_case: str,
        has_local_gpu: bool = False,
        budget_constraint: bool = False,
    ) -> str:
        """
        Get recommended preset based on use case and constraints.

        Args:
            use_case: One of "research", "production", "experimentation", "publication"
            has_local_gpu: Whether the user has a local GPU available
            budget_constraint: Whether budget is a primary concern

        Returns:
            Preset name recommendation
        """
        if budget_constraint:
            return "minimize_cost"
        elif has_local_gpu:
            return "local_only" if use_case in ["experimentation", "research"] else "balanced"
        elif use_case == "publication":
            return "maximize_quality"
        elif use_case == "production":
            return "balanced"
        else:
            return "balanced"  # Default

    @staticmethod
    def get_fallback_chain(
        preset_name: str,
        complexity: str,
        provider_preference: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Get provider fallback chain for a preset.

        Args:
            preset_name: Preset name
            complexity: Task complexity
            provider_preference: Preferred providers

        Returns:
            List of providers in fallback order
        """
        from ..config.provider_registry import ProviderRegistry

        registry = ProviderRegistry()
        return registry.get_fallback_chain(complexity, provider_preference)


if __name__ == "__main__":
    # Convenience: run parse_and_update_registry() when executed directly
    added, updated = parse_and_update_registry()
    print(f"Registry updated: {added} models added, {updated} models updated")
