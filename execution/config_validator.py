"""
Script
------
config_validator.py

Path
----
execution/config_validator.py

Purpose
-------
Config Validator: Validate model configuration, load environment files, and manage API key retrieval.

Extracted from WorkflowRunner to separate configuration concerns from execution logic.
Validates coherence of model config, loads .env files, and provides API key management.

Inputs
------
model_config (dict): Model configuration to validate
graph (WorkflowGraph): Workflow graph for schema access
trace_logger (TraceLogger): Logger for warnings
provider (str): Provider name for API key lookup

Outputs
-------
validated (bool): True if config passes validation (raises on failure)
api_key (str|None): API key from config or environment
None (side effects): Logs warnings, loads environment variables

Assumptions
-----------
- Workflow file is valid JSON matching schema
- .env file exists or environment is pre-configured
- API keys are stored in config file or environment variables

Parameters
----------
None (per-workflow via model_config and graph)

Failure Modes
-------------
- Invalid mode/preset combination → ConfigurationError
- Budget constraints incoherent → ConfigurationError
- Allowlist/blocklist overlap → ConfigurationError
- API key not found → Return None (model handles error)
- .env file missing → Silently ignore

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
"""

import os
from pathlib import Path
from typing import Optional
from .graph import WorkflowGraph
from .trace import TraceLogger
from utils import ConfigurationError


class ConfigValidator:
    """Validate model configuration and manage API key retrieval."""

    def __init__(
        self,
        model_config: dict,
        graph: WorkflowGraph,
        trace_logger: TraceLogger,
    ):
        """
        Args:
            model_config: Model configuration dict to validate
            graph: WorkflowGraph instance for accessing workflow schema
            trace_logger: TraceLogger instance for logging warnings
        """
        self.model_config = model_config
        self.graph = graph
        self.trace_logger = trace_logger

    @staticmethod
    def load_env_file() -> None:
        """Load .env file from repo root to ensure API keys are available."""
        # Find repo root by looking for .env starting from current directory
        repo_root = Path.cwd()
        env_file = None

        # Search up to 3 levels for .env
        for _ in range(3):
            candidate = repo_root / ".env"
            if candidate.exists():
                env_file = candidate
                break
            if repo_root.parent == repo_root:  # Reached filesystem root
                break
            repo_root = repo_root.parent

        if not env_file:
            # .env not found, but that's okay - environment may already be set
            return

        # Load .env file
        try:
            from dotenv import load_dotenv
            # Override=True ensures .env values replace environment variables
            load_dotenv(env_file, override=True)
        except ImportError:
            # dotenv not available, try manual loading
            try:
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            # Always set from .env (override any existing value)
                            os.environ[key] = value.strip('"\'')
            except Exception:
                # Silently ignore errors loading .env
                pass

    def validate_model_config(self) -> None:
        """Validate model configuration for coherence.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.model_config:
            return

        mode = self.model_config.get("mode", "explicit")
        preset = self.model_config.get("preset")

        # Validate mode/preset relationship
        if mode == "preset" and not preset:
            raise ConfigurationError("mode=preset requires preset field")

        if preset and preset not in ["minimize_cost", "balanced", "maximize_quality", "local_only"]:
            raise ConfigurationError(f"Unknown preset: {preset}")

        # Validate budget constraints
        budget = self.model_config.get("budget", {})
        max_per_task = budget.get("max_per_task_usd")
        max_workflow = budget.get("max_workflow_usd")

        if max_per_task and max_workflow and max_per_task > max_workflow:
            raise ConfigurationError("max_per_task_usd cannot exceed max_workflow_usd")

        # Validate provider constraints
        provider_prefs = self.model_config.get("provider_preferences", {})
        allowlist = set(provider_prefs.get("allowlist", []))
        blocklist = set(provider_prefs.get("blocklist", []))

        if allowlist and blocklist and allowlist & blocklist:
            raise ConfigurationError("allowlist and blocklist cannot have overlapping providers")

        # Warn if local_only with critical tasks
        if preset == "local_only":
            from datetime import datetime
            for node_id, node in self.graph.nodes.items():
                complexity = node.get("complexity", "moderate")
                if complexity in ["complex", "critical"]:
                    self.trace_logger.log({
                        "timestamp": datetime.now().isoformat(),
                        "type": "warning",
                        "message": f"preset=local_only but found {complexity} task (may be unresolvable)",
                    })

    def get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for provider from config file or environment.

        Priority:
        1. ~/.hillstar/provider_registry.json (user config)
        2. Environment variable
        3. Return None (let model handle error)

        Args:
            provider: Provider name (e.g., "anthropic")

        Returns:
            API key string or None if not found
        """
        from config import HillstarConfig

        # Strip "_mcp" suffix if present (anthropic_mcp -> anthropic)
        base_provider = provider.replace("_mcp", "")

        # Try config file first
        try:
            config = HillstarConfig()
            api_key = config.get_provider_key(base_provider)
            if api_key:
                return api_key
        except Exception:
            pass

        # Fall back to environment variable
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "google_ai_studio": "GOOGLE_API_KEY",
        }
        env_var = env_var_map.get(base_provider)
        if env_var:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key

        # Not found
        return None
