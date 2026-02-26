# Hillstar API Reference & User Manual
**Package:** hillstar-orchestrator
**Version:** 1.0.0
**Description:** Security and reproducibility-first workflow orchestrator for research environments
**Author:** Julen Gamboa (<julen.gamboa.ds@gmail.com>)
**License:** Apache-2.0
**Repository:** <https://github.com/evoclock/hillstar-orchestrator>
**Python:** >=3.10

## Table of Contents

1. [Overview](#overview)
2. [Installation & Dependencies](#installation--dependencies)
3. [Architecture](#architecture)
4. [Module Structure](#module-structure)
5. [API Reference](#api-reference)
6. [Class Index](#class-index)
7. [Function Index](#function-index)
8. [Module Dependencies](#module-dependencies)

## Overview

Hillstar is a research-grade workflow orchestration system designed for multi-agent AI pipelines and classification tasks. It provides a modular architecture with support for multiple LLM providers, governance policies, and comprehensive execution tracing.

## Installation & Dependencies

```bash
pip install hillstar-orchestrator
```

### Core Dependencies

- `anthropic>=0.7.0`
- `requests>=2.31.0`

## Architecture

Hillstar consists of several key components:

```text
hillstar/
├── config/ - Configuration management
├── execution/ - Workflow execution engine
├── governance/ - Compliance and policy enforcement
├── models/ - LLM provider implementations
├── utils/ - Utilities (logging, tracing, redaction)
├── workflows/ - Workflow discovery and validation
└── cli.py - Command-line interface
```

## Module Structure

### Configuration & Provider Registry

- `hillstar-orchestrator.config.__init__`
- `hillstar-orchestrator.config.config`
- `hillstar-orchestrator.config.model_selector`
- `hillstar-orchestrator.config.provider_registry`
- `hillstar-orchestrator.config.setup_wizard`

### Workflow Execution

- `hillstar-orchestrator.execution.__init__`
- `hillstar-orchestrator.execution.checkpoint`
- `hillstar-orchestrator.execution.config_validator`
- `hillstar-orchestrator.execution.cost_manager`
- `hillstar-orchestrator.execution.graph`
- `hillstar-orchestrator.execution.model_selector`
- `hillstar-orchestrator.execution.node_executor`
- `hillstar-orchestrator.execution.observability`
- `hillstar-orchestrator.execution.runner`
- `hillstar-orchestrator.execution.trace`

### Compliance & Governance

- `hillstar-orchestrator.governance.__init__`
- `hillstar-orchestrator.governance.compliance`
- `hillstar-orchestrator.governance.enforcer`
- `hillstar-orchestrator.governance.hooks`
- `hillstar-orchestrator.governance.policy`
- `hillstar-orchestrator.governance.project_init`

### LLM Model Providers

- `hillstar-orchestrator.models.__init__`
- `hillstar-orchestrator.models.anthropic_mcp_model`
- `hillstar-orchestrator.models.anthropic_model`
- `hillstar-orchestrator.models.anthropic_ollama_api_model`
- `hillstar-orchestrator.models.devstral_local_model`
- `hillstar-orchestrator.models.mcp_model`
- `hillstar-orchestrator.models.mistral_api_model`
- `hillstar-orchestrator.models.mistral_mcp_model`
- `hillstar-orchestrator.models.ollama_mcp_model`
- `hillstar-orchestrator.models.openai_mcp_model`

### Utilities

- `hillstar-orchestrator.utils.__init__`
- `hillstar-orchestrator.utils.credential_redactor`
- `hillstar-orchestrator.utils.exceptions`
- `hillstar-orchestrator.utils.json_output_viewer`
- `hillstar-orchestrator.utils.report`

### Workflow Discovery & Validation

- `hillstar-orchestrator.workflows.__init__`
- `hillstar-orchestrator.workflows.auto_discover`
- `hillstar-orchestrator.workflows.discovery`
- `hillstar-orchestrator.workflows.model_presets`
- `hillstar-orchestrator.workflows.validator`

## API Reference

### **Init**

#### Module: `hillstar-orchestrator.__init__`

*Hillstar Orchestrator v1.0.0.*

### Cli

#### Module: `hillstar-orchestrator.cli`

-

Script
------
cli.py

Path
----
python/hillstar/cli.py

Purpose
-------
Command-line interface for workflow orchestration.

Usage
-----
 hillstar discover [PATH] Find workflows in current or specified directory
 hillstar validate WORKFLOW_PATH Validate a workflow
 hillstar execute WORKFLOW_PATH [DIR] Execute a workflow
 hillstar presets List available presets
 hillstar wizard Run interactive setup wizard
 hillstar mode dev|normal Set development mode for commits
 hillstar enforce check|status|... Governance enforcement
 hillstar loon reduce WORKFLOW Reduce workflow to Loon format
 hillstar loon expand LOON Expand Loon back to standard format
 hillstar loon estimate WORKFLOW Estimate token savings
 hillstar execute-node WORKFLOW NODE Execute a single node
 hillstar --version Show version
 hillstar --help Show this help message

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
import sys
import os
import json
import argparse
from .workflows import WorkflowDiscovery, WorkflowValidator, ModelPresets
from .execution import WorkflowRunner
from .config import SetupWizard
from .utils import HillstarException
from .governance import GovernanceEnforcer, HookManager
```

**Functions:**

- `cmd_discover(args)`
 Find workflows in a directory.
- `cmd_validate(args)`
 Validate a workflow.
- `cmd_execute(args)`
 Execute a workflow.
- `cmd_presets(args)`
 List available presets.
- `cmd_enforce(args)`
 Governance enforcement commands.
- `cmd_wizard(args)`
 Run setup wizard.
- `cmd_mode(args)`
 Set development mode for development commits.
- `main()`
 Main CLI entry point.
- `cmd_execute_node(args)`
 Execute a single node from a workflow.

### Configuration & Provider Registry

#### Module: `hillstar-orchestrator.config.__init__`

*Configuration & Setup Layer for Hillstar Orchestrator.*

**Imports:**

```python
from .config import HillstarConfig
from .setup_wizard import SetupWizard
from .model_selector import ModelSelector
from .provider_registry import ProviderRegistry, get_registry, reset_registry
```

#### Module: `hillstar-orchestrator.config.config`

-

Script
------
config.py

Purpose
-------
Unified configuration management for Hillstar.

Handles:

- Loading default registry from provider_registry.default.json
- Merging user overrides from user config
- Validating provider configurations against registry schema
- Compliance checks for provider configurations
- Managing user-level API keys and settings

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-22
*

**Imports:**

```python
import json
import os
from pathlib import Path
from typing import Any, Optional
from .provider_registry import ProviderRegistry
```

**Classes:**

### `class HillstarConfig` {#hillstar-orchestrator-config-config-hillstarconfig}

Unified configuration management for Hillstar.

Combines registry-based provider configuration with user-level
API key management. Provides methods for:

- Loading and merging configurations
- Validating provider configurations
- Managing user API keys and settings
- Checking compliance requirements

*Methods:*

- `__init__(self)`
 Initialize HillstarConfig with user and default configurations.
- `set_provider_key(self, provider: str, api_key: str) -> None`
 Store API key for a provider.

Args:
 provider: Provider name (e.g., 'anthropic', 'openai')
 api_key: API key value

Raises:
 ValueError: If provider name or api_key is empty

- `get_provider_key(self, provider: str) -> Optional[str]`
 Retrieve API key for a provider.

Args:
 provider: Provider name

Returns:
 API key if configured, None otherwise

- `list_configured_providers(self) -> list[str]`
 List providers that have API keys configured.

Returns:
 List of provider names with keys configured

- `list_missing_providers(self, all_providers: Optional[list[str]] = None) -> list[str]`
 List providers not yet configured.

Args:
 all_providers: List of provider names to check against.
 If None, uses default provider list.

Returns:
 List of provider names without keys configured

- `validate_key(self, provider: str, api_key: str) -> bool`
 Validate that an API key is non-empty and reasonably formatted.

This is basic validation (non-empty, reasonable length).
Full validation (API call) deferred to runtime.

Args:
 provider: Provider name
 api_key: API key to validate

Returns:
 True if key passes basic validation, False otherwise

- `save_config(self) -> None`
 Write configuration to ~/.hillstar/provider_registry.json.

Creates the directory if it doesn't exist.

Raises:
 IOError: If unable to write file

- `load_config(self) -> None`
 Load configuration from ~/.hillstar/provider_registry.json.

Creates empty config if file doesn't exist.

- `get_merged_registry(self) -> ProviderRegistry`
 Get the complete registry with user overrides applied.
- `validate_provider_config(self, provider: str, config: dict[(str, Any)]) -> list[str]`
 Validate provider configuration against registry.

Args:
 provider: Provider name
 config: Provider configuration dict

Returns:
 List of validation error messages (empty if valid)

- `check_compliance(self, provider: str, config: dict[(str, Any)]) -> tuple[(bool, list[str])]`
 Check compliance requirements for a provider.

Args:
 provider: Provider name
 config: Provider configuration

Returns:
 (is_compliant: bool, issues: List[str])

- `get_provider_info(self, provider: str) -> Optional[dict[(str, Any)]]`
 Get full provider configuration from registry.
- `list_available_providers(self) -> list[str]`
 List all available providers from registry.
- `list_available_models(self, provider: str) -> list[str]`
 List all available models for a provider.
- `merge_configs(self, user_config: dict[(str, Any)], workflow_config: dict[(str, Any)]) -> dict[(str, Any)]`
 Merge user configuration with workflow configuration.

Workflow configuration takes precedence over user config.

Args:
 user_config: User provider configuration overrides
 workflow_config: Workflow-specific model configuration

Returns:
 Merged configuration dictionary

#### Module: `hillstar-orchestrator.config.model_selector`

-

Script
------
model_selector.py

Path
----
python/hillstar/model_selector.py

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

- No credentials available ValueError
- Unknown task type defaults to Haiku

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
*

**Classes:**

### `class ModelSelector` {#hillstar-orchestrator-config-model_selector-modelselector}

Cost-optimized model selection based on task complexity.

*Methods:*

- `select(task_complexity: str = 'moderate', provider_preference: Optional[str] = None) -> Tuple[(str, str)]`
 Select model based on task complexity and preferences.

Args:
 task_complexity: "simple", "moderate", "complex", or "critical"
 provider_preference: Prefer specific provider (anthropic, openai, local, devstral)

Returns:
 (provider, model_name) tuple

Example:
 provider, model = ModelSelector.select("moderate", provider_preference="anthropic")
 # Returns ("anthropic", "claude-sonnet-4-5-20250929")

- `get_temperature() -> float`
 Get default temperature (minimizes hallucination).
- `select_with_config(task_complexity: str = 'moderate', config: Optional[Dict[(str, Any)]] = None, node_id: str = '') -> Tuple[(str, str)]`
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

#### Module: `hillstar-orchestrator.config.provider_registry`

-

Script
------
provider_registry.py

Path
----
python/hillstar/config/provider_registry.py

Purpose
-------
Provider Registry: Central registry for LLM providers, models, and compliance rules.

Provides a ProviderRegistry class that loads provider configurations from JSON
and provides lookup methods for model selection, cost estimation, and compliance
verification. Supports package defaults with user overrides for customization.

Inputs
------
Provider registry JSON files (default + optional user override)

Outputs
-------
Registry instance with lookup methods for providers, models, and compliance

Assumptions
-----------

- Default registry file exists at package location
- User override follows same schema as default

Parameters
----------
None (per-query)

Failure Modes
-------------

- Missing default registry FileNotFoundError
- Malformed JSON JSONDecodeError
- Invalid provider/model Returns None

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-14

Last Edited
-----------
2026-02-14 (initial implementation)
*

**Classes:**

### `class ProviderRegistry` {#hillstar-orchestrator-config-provider_registry-providerregistry}

Load and query the provider registry with fallback to user overrides.

The registry is loaded from:

1. Package default: python/hillstar/config/provider_registry.default.json
2. User override: ~/.hillstar/provider_registry.json (optional)

*Properties:*

- `version` -> str
 Get registry version.
- `last_updated` -> str
 Get last update timestamp.

*Methods:*

- `__init__(self, custom_registry_path: Optional[str] = None)`
 Initialize the provider registry.

Args:
 custom_registry_path: Optional path to a custom registry file.
 If provided, this takes precedence over both default and user override.

- `list_providers(self, provider_type: Optional[str] = None) -> List[str]`
 List available providers, optionally filtered by type.

Args:
 provider_type: Optional filter: "cloud_api", "local", "local_proxy"

Returns:
 List of provider names

- `get_provider(self, provider_name: str) -> Optional[Dict[(str, Any)]]`
 Get full provider configuration.
- `get_provider_compliance(self, provider_name: str) -> Optional[Dict[(str, Any)]]`
 Get compliance rules for a provider.
- `get_model(self, provider_name: str, model_id: str) -> Optional[Dict[(str, Any)]]`
 Get model configuration.

Args:
 provider_name: Provider identifier (e.g., "anthropic")
 model_id: Model identifier (e.g., "claude-opus-4-6")

Returns:
 Model configuration dict or None

- `find_models(self, capabilities: Optional[List[str]] = None, max_tier: Optional[str] = None, provider_type: Optional[str] = None, require_ollama: Optional[bool] = None) -> List[Dict[(str, Any)]]`
 Find models matching criteria.

Args:
 capabilities: List of required capabilities (e.g., ["coding", "reasoning"])
 max_tier: Maximum cost tier (e.g., "cheap", "standard")
 provider_type: Filter by provider type (e.g., "cloud_api", "local")
 require_ollama: If True, only return models requiring Ollama

Returns:
 List of matching model configs with provider context

- `get_cheapest_model(self, capabilities: Optional[List[str]] = None, provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
 Get the cheapest model matching criteria, respecting provider preference.

Args:
 capabilities: Required capabilities
 provider_preference: Preferred provider order (e.g., ["anthropic", "openai"])

Returns:
 Tuple of (provider, model_id, model_config) or None

- `estimate_cost(self, provider_name: str, model_id: str, input_tokens: int, output_tokens: int) -> float`
 Estimate cost for a model call.

Args:
 provider_name: Provider identifier
 model_id: Model identifier
 input_tokens: Number of input tokens
 output_tokens: Number of output tokens

Returns:
 Estimated cost in USD

- `get_fallback_chain(self, complexity: str, provider_preference: Optional[List[str]] = None) -> List[str]`
 Get provider fallback chain for a complexity level.

Args:
 complexity: Task complexity ("simple", "moderate", "complex", "critical")
 provider_preference: Preferred providers (highest priority first)

Returns:
 List of providers in fallback order

- `is_usage_compliant(self, provider_name: str, use_case: str) -> Tuple[(bool, str)]`
 Check if a use case is compliant for a provider.

Args:
 provider_name: Provider identifier
 use_case: Intended use case (e.g., "research", "commercial")

Returns:
 Tuple of (is_compliant, reason)

- `get_model_sampling_params(self, provider_name: str, model_id: str) -> Dict[(str, Any)]`
 Get default sampling parameters for a model.
- `get_all_models_flat(self) -> Dict[(Tuple[(str, str)], Dict[(str, Any)])]`
 Get a flat dictionary of all (provider, model_id) -> model_config.
- `describe(self) -> str`
 Get a human-readable description of the registry.

**Functions:**

- `get_registry() -> 'ProviderRegistry'`
 Get the global registry instance.
- `reset_registry() -> None`
 Reset the global registry instance (useful for testing).

#### Module: `hillstar-orchestrator.config.setup_wizard`

-

Script
------
setup_wizard.py

Path
----
python/hillstar/config/setup_wizard.py

Purpose
-------
Interactive setup wizard for Hillstar provider configuration.

Guides users through:

1. Cloud provider API key setup (Anthropic, OpenAI, Google, Mistral)
2. Local provider testing (Ollama, Devstral local)
3. Validated config saved to ~/.hillstar/provider_registry.json

Inputs
------
(interactive prompts)

Outputs
-------
~/.hillstar/provider_registry.json with user configuration merged over defaults

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-14
*

**Imports:**

```python
import json
import os
import sys
from typing import Any, Optional
import httpx
from .provider_registry import ProviderRegistry
```

**Classes:**

### `class SetupWizard` {#hillstar-orchestrator-config-setup_wizard-setupwizard}

Interactive wizard for Hillstar provider configuration.

*Methods:*

- `__init__(self)`
- `run(self) -> None`
 Run the setup wizard.

**Functions:**

- `main()`
 Entry point for setup wizard.

### Deprecated

#### Module: `hillstar-orchestrator.deprecated.runner_deprecated`

-

Script
------
runner.py

Path
----
execution/runner.py

Purpose
-------
Workflow Runner (Original Monolith): Main orchestration engine.

[DEPRECATED: Use runner_refactored.py for modularized version]

This file is kept for reference and compatibility.
New code should use runner_refactored.py which uses:

- CostManager, ConfigValidator, ModelFactory, NodeExecutor

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>
*

### Module: `hillstar-orchestrator.deprecated.runner_original_backup`

-

Script
------
runner.py

Path
----
python/hillstar/runner.py

Purpose
-------
Workflow Runner: Main orchestration engine for research classification workflows.

Executes workflows with full auditability, model selection, checkpoint management,
and trace logging. Integrates smart model selection based on task complexity
and institutional pricing model.

Inputs
------
workflow_path (str): Path to workflow.json file
output_dir (str): Directory for traces and checkpoints

Outputs
-------
Dictionary: {workflow_id, status, outputs, trace_file}

Assumptions
-----------

- Workflow file is valid JSON matching python/hillstar/schemas/workflow-schema.json
- Output directory can be created with write permissions
- Model credentials available (env vars or API keys)

Parameters
----------
None (per-workflow)

Failure Modes
-------------

- Invalid workflow JSON json.JSONDecodeError
- Missing model credentials ValueError
- Node execution error Exception logged and re-raised
- Timeout on model call requests.exceptions.Timeout

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-08 (error checking in _execute_model_call)
*

**Classes:**

### `class WorkflowRunner` {#hillstar-orchestrator-deprecated-runner_original_backup-workflowrunner}

Execute research workflows with full auditability and smart model selection.

*Methods:*

- `__init__(self, workflow_path: str, output_dir: str = './.hillstar')`
 Args:
 workflow_path: Path to workflow.json file
 output_dir: Directory for traces and checkpoints
- `get_model(self, provider: str, model_name: str, **kwargs)`
 Get or create model instance with smart selection.

Args:
 provider: Provider name.
 model_name: Model identifier.
 **kwargs: Provider-specific options (e.g., sandbox, approval_policy
 for codex_mcp).

- `execute_node(self, node_id: str, node: dict, inputs: Any) -> dict[(str, Any)]`
 Execute a single node.
- `execute(self, resume_from: str = None) -> dict[(str, Any)]`
 Execute the workflow, optionally resuming from a checkpoint.

Args:
 resume_from: Checkpoint file path or node_id to resume from

### Dev

#### Module: `hillstar-orchestrator.dev.testing.openai_token_diagnostic`

-

Script
------
openai_token_diagnostic.py

Path
----
dev/testing/openai_token_diagnostic.py

Purpose
-------
Diagnose which OpenAI subscription tokens are needed for third-party harness auth.

Test OpenAI's auth.json structure and determine:

1. Which tokens are actually required
2. Which tokens work for API authentication
3. Recommended env var names
4. Token refresh/expiration handling

Usage
-----
python openai_token_diagnostic.py [--auth-json PATH]

Output
------
Results saved to: .test-results/openai_token_diagnostic_output.txt

Requires
--------

- OpenAI auth.json file (from ~/.config/openai/auth.json or specified path)
- Network access to test against OpenAI API
- (optional) OPENAI_API_KEY for fallback testing

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
*

**Imports:**

```python
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
```

**Functions:**

- `load_auth_json(path: Optional[str] = None) -> Dict[(str, Any)]`
 Load auth.json from repo root or OpenAI config directory.
- `analyze_tokens(auth_data: Dict[(str, Any)], output_file: Path) -> None`
 Analyze available tokens in auth.json and write to file.
- `main()`
 Main entry point.

### Docs

#### Module: `hillstar-orchestrator.docs.doc_generator`

-

Script
------
doc_generator.py

Path
----
python/hillstar/utils/doc_generator.py

Purpose
-------
AST-based User Manual documentation generator for Hillstar.

This module provides comprehensive documentation generation from Python source code
using the ast module. It parses all Python files in a package and generates structured
markdown documentation with full type hints, docstrings, hierarchical organization,
cross-references, module dependencies, and searchable indices for the User Manual.

Features:

- Complete AST-based analysis of all classes, functions, methods, properties
- Cross-references between modules and components
- Module dependency graph and analysis
- Comprehensive class and function indices
- Searchable markdown sections with proper anchor links

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re
```

**Classes:**

### `class DocParameter` {#hillstar-orchestrator-docs-doc_generator-docparameter}

Represents a function/method parameter with type information.

*Methods:*

- `__str__(self) -> str`

### `class DocFunction` {#hillstar-orchestrator-docs-doc_generator-docfunction}

Represents a function or method with metadata.

#### `class DocClass` {#hillstar-orchestrator-docs-doc_generator-docclass}

Represents a class with methods and properties.

##### `class DocModule` {#hillstar-orchestrator-docs-doc_generator-docmodule}

Represents a module with its contents.

##### `class CrossReferenceBuilder` {#hillstar-orchestrator-docs-doc_generator-crossreferencebuilder}

Builds cross-references between modules, classes, and functions.

*Methods:*

- `__init__(self, modules_data: Dict[(str, DocModule)])`
- `get_module_dependencies(self, module_name: str) -> List[str]`
 Get modules that a module depends on.
- `find_related_types(self, type_name: str) -> List[Tuple[(str, str)]]`
 Find modules and items using or returning a type.

##### `class ASTAnalyzer(ast.NodeVisitor)` {#hillstar-orchestrator-docs-doc_generator-astanalyzer}

Analyzes Python AST to extract documentation information.

*Methods:*

- `__init__(self, module_name: str, source_path: str)`
- `get_decorator_names(self, node: Any) -> List[str]`
 Extract decorator names from a node.
- `get_type_annotation(self, annotation: Optional[Any]) -> str`
 Convert annotation AST node to string.
- `get_default_value(self, default: Optional[Any]) -> Optional[str]`
 Convert default value AST node to string.
- `visit_Module(self, node: ast.Module) -> None`
 Visit module node.
- `visit_Import(self, node: ast.Import) -> None`
 Visit import statement.
- `visit_ImportFrom(self, node: ast.ImportFrom) -> None`
 Visit from...import statement.
- `visit_ClassDef(self, node: ast.ClassDef) -> None`
 Visit class definition.
- `visit_FunctionDef(self, node: ast.FunctionDef) -> None`
 Visit function definition.
- `visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None`
 Visit async function definition.
- `visit_Assign(self, node: ast.Assign) -> None`
 Visit assignment (constants/globals).

##### `class DocumentationGenerator` {#hillstar-orchestrator-docs-doc_generator-documentationgenerator}

Generates comprehensive markdown documentation from Python packages.

*Methods:*

- `__init__(self, package_path: str, setup_py_path: str)`
- `analyze_package(self) -> None`
 Analyze all Python files in package.
- `extract_setup_metadata(self) -> Dict[(str, Any)]`
 Extract metadata from setup.py.
- `generate_markdown(self) -> str`
 Generate comprehensive markdown documentation.
- `save_documentation(self, output_path: str) -> None`
 Save generated documentation to file.

**Functions:**

- `generate_user_manual(package_path: str = '/home/jgamboa/hillstar-orchestrator', setup_py_path: str = '/home/jgamboa/agentic-orchestrator/python/setup.py', output_path: str = '/home/jgamboa/hillstar-orchestrator/docs/User_Manual.md') -> None`
 Generate User Manual documentation for Hillstar package.

### Workflow Execution

#### Module: `hillstar-orchestrator.execution.__init__`

*Execution Engine for Hillstar Orchestrator.*

**Imports:**

```python
from .runner import WorkflowRunner
from .graph import WorkflowGraph
from .checkpoint import CheckpointManager
from .trace import TraceLogger
from .observability import ExecutionObserver
```

#### Module: `hillstar-orchestrator.execution.checkpoint`

-

Script
------
checkpoint.py

Path
----
python/hillstar/checkpoint.py

Purpose
-------
Checkpoint Manager: Save and restore workflow state for replay and recovery.

Creates JSON checkpoints after specified nodes complete, allowing workflows
to be resumed from intermediate states. Supports full state export/import.

Inputs
------
output_dir (str): Directory to store checkpoints
node_id (str): Node completing execution
state (dict): Workflow state to save

Outputs
-------
Checkpoint files (JSON): One checkpoint per node

Assumptions
-----------

- Output directory exists or can be created
- Write permissions to output_dir

Parameters
----------
None (per-node checkpointing)

Failure Modes
-------------

- No write permissions IOError
- Corrupt checkpoint file json.JSONDecodeError
- Missing checkpoint FileNotFoundError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
*

**Classes:**

##### `class CheckpointManager` {#hillstar-orchestrator-execution-checkpoint-checkpointmanager}

Manage workflow checkpoints for replay and recovery.

*Methods:*

- `__init__(self, output_dir: str)`
 Args:
 output_dir: Directory to store checkpoints
- `create(self, node_id: str, state: Dict[(str, Any)]) -> str`
 Create a checkpoint after node execution.

Args:
 node_id: Node that just completed
 state: Workflow state to save

Returns:
 Path to checkpoint file

- `list_checkpoints(self) -> Dict[(str, str)]`
 List all available checkpoints.
- `load(self, checkpoint_file: str) -> Dict[(str, Any)]`
 Load a checkpoint.

Args:
 checkpoint_file: Path to checkpoint file

Returns:
 Checkpoint data

- `get_latest_checkpoint(self, node_id: Optional[str] = None) -> Optional[str]`
 Get most recent checkpoint.

Args:
 node_id: Optionally filter by node (get all if None)

Returns:
 Path to latest checkpoint or None

#### Module: `hillstar-orchestrator.execution.config_validator`

-

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

- Invalid mode/preset combination ConfigurationError
- Budget constraints incoherent ConfigurationError
- Allowlist/blocklist overlap ConfigurationError
- API key not found Return None (model handles error)
- .env file missing Silently ignore

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
*

**Classes:**

##### `class ConfigValidator` {#hillstar-orchestrator-execution-config_validator-configvalidator}

Validate model configuration and manage API key retrieval.

*Methods:*

- `__init__(self, model_config: dict, graph: WorkflowGraph, trace_logger: TraceLogger)`
 Args:
 model_config: Model configuration dict to validate
 graph: WorkflowGraph instance for accessing workflow schema
 trace_logger: TraceLogger instance for logging warnings
- `load_env_file() -> None`
 Load .env file from repo root to ensure API keys are available.
- `validate_model_config(self) -> None`
 Validate model configuration for coherence.

Raises:
 ConfigurationError: If configuration is invalid

- `get_api_key_for_provider(self, provider: str) -> Optional[str]`
 Get API key for provider from config file or environment.

Priority:

1. ~/.hillstar/provider_registry.json (user config)
2. Environment variable
3. Return None (let model handle error)

Args:
 provider: Provider name (e.g., "anthropic")

Returns:
 API key string or None if not found

#### Module: `hillstar-orchestrator.execution.cost_manager`

-

Script
------
cost_manager.py

Path
----
execution/cost_manager.py

Purpose
-------
Cost Manager: Handle cost estimation, budget checking, and cost tracking for workflow execution.

Extracted from WorkflowRunner to enable modular unit testing and cost policy changes
without affecting node execution or model selection logic.

Inputs
------
model_config (dict): Model configuration with pricing and budget information
provider (str): Provider name (anthropic, openai, local, devstral, etc.)
model_name (str): Model identifier
input_tokens (int): Estimated input tokens for cost calculation
output_tokens (int): Estimated output tokens for cost calculation
estimated_cost (float): Cost to check against budget limits
node_id (str): Node identifier for error reporting
cost (float): Actual cost to record

Outputs
-------
estimated_cost (float): USD cost estimate for model call
None (methods modify internal state): cumulative_cost_usd, node_costs dict

Assumptions
-----------

- Pricing data is accurate and up-to-date
- Budget constraints are coherent (max_per_task <= max_workflow)
- Token estimates are reasonable approximations

Parameters
----------
None (per-workflow via model_config)

Failure Modes
-------------

- Unknown model Use fallback pricing
- Missing budget config No budget enforcement
- Negative costs Treated as 0.0

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
*

**Classes:**

##### `class CostManager` {#hillstar-orchestrator-execution-cost_manager-costmanager}

Manage cost estimation, budget enforcement, and cost tracking for models.

*Methods:*

- `__init__(self, model_config: dict)`
 Args:
 model_config: Model configuration dict with pricing and budget info
- `estimate_cost(self, provider: str, model_name: str, input_tokens: int, output_tokens: int) -> float`
 Estimate cost of a model call.

Args:
 provider: Provider name (anthropic, openai, local, devstral)
 model_name: Model name
 input_tokens: Estimated input tokens
 output_tokens: Estimated output tokens

Returns:
 Estimated cost in USD

- `check_budget(self, estimated_cost: float, node_id: str) -> None`
 Check if cost would exceed budget limits.

Args:
 estimated_cost: Estimated cost of this call in USD
 node_id: Node ID for logging

Raises:
 BudgetExceededError: If budget would be exceeded

- `record_cost(self, node_id: str, cost: float) -> None`
 Record actual cost for a node.

#### Module: `hillstar-orchestrator.execution.graph`

-

Script
------
graph.py

Path
----
python/hillstar/graph.py

Purpose
-------
Graph Execution Engine: DAG-based workflow runner with checkpointing.

Implements topological sort, cycle detection, and state management for
directed acyclic graph (DAG) workflows. Supports node execution, checkpoint
creation, and full auditability via trace logging.

Inputs
------
workflow_json (dict): Workflow definition with nodes, edges, state, permissions

Outputs
-------
Workflow execution state (node_outputs, trace, execution_order)

Assumptions
-----------

- Workflow is a valid DAG (no cycles)
- Node inputs can reference previous node outputs via {{ node_id.output }} syntax
- Permissions are specified per node (ask, always, never)
- Checkpoints created at specified nodes only

Parameters
----------
None (class-based)

Failure Modes
-------------

- Cycle detected in graph ValueError
- Invalid node reference KeyError
- Missing required node ValueError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-08 (error detection in execute_node)
*

**Classes:**

##### `class WorkflowGraph` {#hillstar-orchestrator-execution-graph-workflowgraph}

Directed Acyclic Graph (DAG) workflow executor.

*Methods:*

- `__init__(self, workflow_json: Dict[(str, Any)])`
 Args:
 workflow_json: Workflow definition (nodes + edges)
- `get_node_inputs(self, node_id: str) -> Any`
 Resolve node inputs, substituting references to previous outputs.
- `execute_node(self, node_id: str, executor_fn) -> Any`
 Execute a single node.
- `get_execution_order(self) -> List[str]`
 Return the order in which nodes should execute.
- `get_checkpoint_nodes(self) -> List[str]`
 Return nodes where checkpoints should be created.
- `export_state(self) -> Dict[(str, Any)]`
 Export complete execution state.
- `import_state(self, state: Dict[(str, Any)]) -> None`
 Import execution state from checkpoint for resumption.

Args:
 state: State dictionary from checkpoint

#### Module: `hillstar-orchestrator.execution.model_selector`

-

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

- Unknown provider ValueError
- Missing API key Model handles error
- Ollama unavailable Check fails, other providers tried
- Local tool missing Marked unavailable

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
*

**Classes:**

##### `class ModelFactory` {#hillstar-orchestrator-execution-model_selector-modelfactory}

Factory for creating and caching model instances with provider resolution.

*Methods:*

- `__init__(self, model_config: dict, trace_logger: TraceLogger, config_validator: ConfigValidator)`
 Args:
 model_config: Model configuration with provider preferences
 trace_logger: Logger for provider resolution and events
 config_validator: ConfigValidator for API key retrieval
- `select_model(self, node_id: str, node: dict) -> tuple`
 Select model for a node using three-layer priority.

Layer 1: Explicit node settings (provider/model)
Layer 2: Config-based selection (task_type/complexity + provider_preference)
Layer 3: Fallback defaults

Returns:
 (provider, model_name) tuple

- `resolve_provider_preference(self, provider_preference: list[str]) -> list[str]`
 Resolve provider preference list based on availability checks.
- `provider_is_available(self, provider: str) -> bool`
 Check if a provider appears available based on local tools/endpoints.
- `ollama_available(self) -> bool`
 Check if Ollama is available via CLI or HTTP.
- `get_model(self, provider: str, model_name: str, **kwargs)`
 Get or create model instance with smart selection.

Args:
 provider: Provider name.
 model_name: Model identifier.
 **kwargs: Provider-specific options (e.g., sandbox, approval_policy
 for codex_mcp).

#### Module: `hillstar-orchestrator.execution.node_executor`

-

Script
------
node_executor.py

Path
----
execution/node_executor.py

Purpose
-------
Node Executor: Execute individual workflow nodes with support for model calls, file operations, and scripting.

Extracted from WorkflowRunner to separate node execution logic from orchestration.
Handles model calls with fallback, file read/write, script execution, and git commits.

Inputs
------
node_id (str): Unique node identifier
node (dict): Node definition with tool, parameters, provider, model
inputs (Any): Input data from previous nodes
error_msg (str): Error message to check for fallback triggers
provider (str): Provider name for temperature normalization

Outputs
-------
result (dict): Node execution result with output, error, or return code
node_outputs (dict): Storage for successful node outputs
None (side effects): Executes scripts, writes files, creates commits

Assumptions
-----------

- Model instances are available from ModelFactory
- Node definitions follow workflow schema
- File paths are accessible and writable
- Git is available for commit operations

Parameters
----------
None (per-node via node definition)

Failure Modes
-------------

- Model call fails Fallback to next provider
- File not found Return error dict
- Script timeout Return timeout error
- Git commit fails Return git error
- Unknown tool Return unknown tool error

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
*

**Classes:**

##### `class NodeExecutor` {#hillstar-orchestrator-execution-node_executor-nodeexecutor}

Execute individual workflow nodes with comprehensive error handling.

*Methods:*

- `__init__(self, model_factory: ModelFactory, cost_manager: CostManager, trace_logger: TraceLogger, model_config: dict)`
 Args:
 model_factory: ModelFactory for model instantiation
 cost_manager: CostManager for cost tracking
 trace_logger: TraceLogger for execution logging
 model_config: Model configuration dict
- `execute_node(self, node_id: str, node: dict, inputs: Any) -> dict[(str, Any)]`
 Execute a single node.

#### Module: `hillstar-orchestrator.execution.observability`

-

Script
------
observability.py

Path
----
python/hillstar/execution/observability.py

Purpose
-------
Comprehensive observability layer for workflow execution with progress tracking,
timestamping, PID logging, hashing, and trace generation.

Inputs
------

- workflow_id (str): Current workflow identifier
- output_dir (str): Directory for logs and traces
- total_nodes (int): Total number of nodes to execute

Outputs
-------

- Real-time progress output to stdout and log files
- Trace file with detailed execution metadata

Assumptions
-----------

- Output directories exist or can be created
- Write permissions to output_dir

Parameters
----------

- verbose: Enable detailed logging
- use_tqdm: Use tqdm progress bars (True by default)

Failure Modes
-------------

- No write permissions IOError
- Disk full IOError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-17
*

**Constants:**

- `HAS_TQDM` = False

**Classes:**

##### `class TqdmFileWrapper` {#hillstar-orchestrator-execution-observability-tqdmfilewrapper}

Wrapper that captures tqdm output to log files while displaying on terminal.

Strips ANSI escape codes before writing to log files for cleaner output,
while preserving colored/animated bar on stdout/stderr for real-time viewing.

*Methods:*

- `__init__(self, log_file_path: Path, audit_log_file_path: Path)`
 Initialize wrapper with log file paths.

Args:
 log_file_path: Backwards-compat log file location
 audit_log_file_path: Audit directory log file location

- `write(self, text: str)`
 Write text to log files (with ANSI stripped) and original stderr.

Args:
 text: Raw text from tqdm (may contain ANSI escape codes)

- `flush(self)`
 Flush the original stderr.

##### `class ExecutionObserver` {#hillstar-orchestrator-execution-observability-executionobserver}

Real-time monitoring and logging of workflow execution.

*Methods:*

- `__init__(self, workflow_id: str, output_dir: str, total_nodes: int, use_tqdm: bool = True)`
 Initialize execution observer.

Args:
 workflow_id: Workflow identifier
 output_dir: Base output directory
 total_nodes: Total nodes in workflow
 use_tqdm: Use tqdm progress bars

- `node_start(self, node_id: str, node_index: int)`
 Record node execution start.
- `node_success(self, node_id: str, duration_seconds: float, output_hash: Optional[str] = None, output_summary: Optional[Dict] = None)`
 Record node execution success.
- `node_failure(self, node_id: str, error_msg: str, duration_seconds: float)`
 Record node execution failure.
- `workflow_complete(self, cumulative_cost_usd: float = 0.0)`
 Record workflow completion.
- `workflow_error(self, error_msg: str)`
 Record workflow error.
- `hash_output(data: Any) -> str`
 Generate SHA256 hash of output for auditability.

#### Module: `hillstar-orchestrator.execution.runner`

-

Script
------
runner.py

Path
----
execution/runner.py

Purpose
-------
Workflow Runner: Main orchestration engine with dependency injection.

Executes workflows with full auditability, model selection, checkpoint management,
and trace logging. Uses modular components for cost management, config validation,
model selection, and node execution.

Inputs
------
workflow_path (str): Path to workflow.json file
output_dir (str): Directory for traces and checkpoints

Outputs
-------
Execution result (dict): Final state with workflow_id, status, outputs, trace file, and cost

Assumptions
-----------

- Workflow JSON is valid and follows schema
- Output directory can be created
- Dependencies (checkpoint, trace, graph modules) are available

Parameters
----------
None (via WorkflowRunner constructor)

Failure Modes
-------------

- Invalid workflow JSON JSONDecodeError
- Missing required nodes ExecutionError
- API key unavailable APIKeyError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22 (Refactored with modular components)

Last Edited
-----------
2026-02-22 (Modularized into CostManager, ConfigValidator, ModelFactory, NodeExecutor)
*

**Classes:**

##### `class WorkflowRunner` {#hillstar-orchestrator-execution-runner-workflowrunner}

Execute research workflows with full auditability and smart model selection.

*Methods:*

- `__init__(self, workflow_path: str, output_dir: str = './.hillstar')`
 Args:
 workflow_path: Path to workflow.json file
 output_dir: Directory for traces and checkpoints
- `execute(self, resume_from: Optional[str] = None) -> dict[(str, Any)]`
 Execute the workflow, optionally resuming from a checkpoint.

#### Module: `hillstar-orchestrator.execution.trace`

-

Script
------
trace.py

Path
----
python/hillstar/trace.py

Purpose
-------
Trace Logger: Comprehensive audit trail for workflow execution.

Logs all events (node execution, errors, model calls) to JSONL file for auditability
and reproducibility. Timestamps all events automatically.

Inputs
------
output_dir (str): Directory to store trace files

Outputs
-------
Trace file (JSONL): One JSON object per line, each representing an event

Assumptions
-----------

- Output directory exists or can be created
- Write permissions to output_dir

Parameters
----------
None (append-only logging)

Failure Modes
-------------

- No write permissions IOError
- Disk full IOError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-08 (enforce traces/ subdirectory)
*

**Imports:**

```python
import json
```

**Classes:**

##### `class TraceLogger` {#hillstar-orchestrator-execution-trace-tracelogger}

Log all workflow executions for auditability and reproducibility.

*Methods:*

- `__init__(self, output_dir: str)`
 Args:
 output_dir: Directory to store trace files (will use output_dir/traces/)
- `log(self, event: Dict[(str, Any)]) -> None`
 Log a single event.

Args:
 event: Event dictionary (will be timestamped if not present)

- `finalize(self) -> str`
 Finalize trace and return file path.

Returns:
 Path to trace file

- `get_events(self) -> List[Dict]`
 Get all logged events.
- `get_cost_summary(self) -> Dict[(str, Any)]`
 Extract cost summary from logged events.

### Compliance & Governance

#### Module: `hillstar-orchestrator.governance.__init__`

-

Script
------
**init**.py

Path
----
python/hillstar/governance/**init**.py

Purpose
-------
Governance module: Enforce workflow-driven development by gating git commits
behind verified Hillstar workflow executions.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
*

**Imports:**

```python
from .enforcer import GovernanceEnforcer
from .hooks import HookManager
from .policy import GovernancePolicy
from .compliance import verify_hillstar_compliance
```

#### Module: `hillstar-orchestrator.governance.compliance`

-

Script
------
compliance.py

Path
----
python/hillstar/governance/compliance.py

Purpose
-------
Compliance enforcement module for Hillstar.

Enforce Hillstar's compliance architecture and prevent prohibited modifications.
This module verifies that only API-based orchestration is used, preventing
CLI/SDK access that would violate provider terms of service.

Providers Covered
-----------------

- Anthropic (Claude)
- Mistral AI (Le Chat)
- OpenAI (GPT, Codex)
- Google (Vertex AI, Gemini)
- Amazon (Bedrock)
- Microsoft (Azure AI)
- Meta (Llama)
- Cohere
- Ollama

Compliance Rules
----------------

1. API-only authentication for cloud providers
2. No CLI/SDK access methods
3. No mixing of access patterns
4. Proper provider attribution
5. User responsibility documentation

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-14

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
import inspect
from typing import List, Any
```

**Classes:**

##### `class ComplianceError(Exception)` {#hillstar-orchestrator-governance-compliance-complianceerror}

Raised when compliance violations are detected.

##### `class ComplianceEnforcer` {#hillstar-orchestrator-governance-compliance-complianceenforcer}

Enforce Hillstar's compliance architecture.

*Methods:*

- `__init__(self)`
- `check_provider_class(self, provider_name: str, provider_class: Any) -> bool`
 Check a provider class for compliance violations.
- `check_all_providers(self) -> bool`
 Check all provider implementations for compliance.
- `check_model_selector(self) -> bool`
 Check ModelSelector for compliance violations.
- `verify_compliance(self) -> bool`
 Run all compliance checks.
- `get_violations(self) -> List[str]`
 Get list of compliance violations.
- `print_compliance_report(self) -> None`
 Print compliance verification report.

**Functions:**

- `verify_hillstar_compliance() -> None`
 Verify Hillstar compliance at import time.

#### Module: `hillstar-orchestrator.governance.enforcer`

-

Script
------
enforcer.py

Path
----
python/hillstar/governance/enforcer.py

Purpose
-------
Core governance enforcement: validate that a Hillstar workflow was executed
before allowing a git commit to proceed.

Reads .hillstar/commit_ready.json written by runner.py on successful execution.
Checks age, workflow ID, and policy compliance.

Inputs
------

- hillstar_dir: path to .hillstar directory (default: .hillstar in cwd)
- policy: GovernancePolicy instance

Outputs
-------

- (compliant: bool, reason: str)

Assumptions
-----------

- runner.py writes commit_ready.json on successful workflow completion
- .hillstar/ directory exists in the project root

Parameters
----------
See GovernancePolicy

Failure Modes
-------------

- commit_ready.json missing: non-compliant
- commit_ready.json stale (age > max_age_seconds): non-compliant
- HILLSTAR_FORCE_COMMIT=1 env var: override allowed if policy permits

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
*

**Constants:**

- `COMMIT_READY_FILE` = 'commit_ready.json'

**Classes:**

##### `class GovernanceEnforcer` {#hillstar-orchestrator-governance-enforcer-governanceenforcer}

Enforce workflow-driven development before git commits.

*Methods:*

- `__init__(self, hillstar_dir: str = '.hillstar', policy: GovernancePolicy | None = None)`
- `check(self, dev_mode: bool = False) -> tuple[(bool, str)]`
 Check whether the current state is compliant for a git commit.

Args:
 dev_mode: If True (or HILLSTAR_DEV_MODE=1 in env), skip governance check.

Returns:
 (compliant, reason): compliant=True means commit is allowed.

- `write_marker(self, workflow_id: str, workflow_file: str, summary: str = '') -> None`
 Write commit_ready marker after successful workflow execution.
- `clear_marker(self) -> None`
 Clear the commit_ready marker (e.g. after commit completes).
- `status(self) -> dict`
 Return full status dictionary for display.

#### Module: `hillstar-orchestrator.governance.hooks`

-

Script
------
hooks.py

Path
----
python/hillstar/governance/hooks.py

Purpose
-------
Git hook management: install, remove, and verify pre-commit hooks that
enforce Hillstar workflow execution before allowing commits.

Inputs
------

- project_dir: path to the git repository root

Outputs
-------

- .git/hooks/pre-commit script that calls `hillstar enforce check`

Assumptions
-----------

- Git repository exists at project_dir
- hillstar CLI is on PATH

Parameters
----------

- project_dir: str

Failure Modes
-------------

- .git/hooks/ does not exist: not a git repo
- pre-commit hook already exists: prompts before overwriting

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
*

**Imports:**

```python
from __future__ import annotations
import os
```

**Constants:**

- `PRE_COMMIT_TEMPLATE` = '#!/usr/bin/env bash\n# Hillstar governance pre-commit hook\n# Auto-installed by: hillstar enforce install\n# DO NOT EDIT — managed by Hillstar governance module\n\nset -euo pipefail\n\n# Check if development mode is active\nDEV_MODE_FLAG=""\nif [[ "${HILLSTAR_DEV_MODE:-0}" == "1" ]]; then\n DEV_MODE_FLAG="--dev"\nfi\n\n# Allow bypass with env var\nif [[ "${HILLSTAR_FORCE_COMMIT:-0}" == "1" ]]; then\n echo "[hillstar] Force commit override active. Skipping governance check."\n exit 0\nfi\n\n# Check if hillstar is available\nif ! command -v hillstar &> /dev/null; then\n echo "[hillstar] WARNING: hillstar not found on PATH, skipping governance check."\n exit 0\nfi\n\n# Run governance check (with --dev flag if HILLSTAR_DEV_MODE=1)\necho "[hillstar] Checking workflow execution compliance..."\nif hillstar enforce check $DEV_MODE_FLAG; then\n echo "[hillstar] Governance check passed."\n exit 0\nelse\n echo ""\n echo "[hillstar] Commit blocked: no recent Hillstar workflow execution found."\n echo "[hillstar] Run: hillstar execute <workflow.json>"\n echo "[hillstar] Or use development mode: HILLSTAR_DEV_MODE=1 git commit ..."\n exit 1\nfi\n'

**Classes:**

##### `class HookManager` {#hillstar-orchestrator-governance-hooks-hookmanager}

Manage git hooks for Hillstar governance enforcement.

*Methods:*

- `__init__(self, project_dir: str = '.')`
- `is_git_repo(self) -> bool`
 Check if project_dir is a git repository.
- `is_installed(self) -> bool`
 Check if the Hillstar pre-commit hook is installed.
- `install(self, force: bool = False) -> tuple[(bool, str)]`
 Install the pre-commit hook.

Args:
 force: Overwrite existing hook without prompting.

Returns:
 (success, message)

- `uninstall(self) -> tuple[(bool, str)]`
 Remove the Hillstar pre-commit hook.
- `status(self) -> dict`
 Return hook installation status.

#### Module: `hillstar-orchestrator.governance.policy`

-

Script
------
policy.py

Path
----
python/hillstar/governance/policy.py

Purpose
-------
Governance policy definitions: what constitutes a valid workflow execution
for the purpose of gating git commits.

Inputs
------
None (configuration constants)

Outputs
-------
GovernancePolicy dataclass

Assumptions
-----------

- Policy is loaded from .hillstar/governance_policy.json if present,
 otherwise defaults apply.

Parameters
----------

- max_age_seconds: Maximum age of a commit_ready marker (default 3600 = 1 hour)
- allow_force_override: Whether HILLSTAR_FORCE_COMMIT env var is respected
- require_workflow_id: Whether a workflow ID must be present in the marker
- blocked_patterns: File patterns that always require a workflow (e.g. *.py,*.json)
- exempt_patterns: File patterns exempt from enforcement (e.g. *.md docs, logs)

Failure Modes
-------------

- policy.json malformed: falls back to defaults with a warning

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-08

Last Edited
-----------
2026-02-08
*

**Classes:**

##### `class GovernancePolicy` {#hillstar-orchestrator-governance-policy-governancepolicy}

Policy configuration for workflow enforcement.

*Methods:*

- `load(cls, hillstar_dir: str) -> 'GovernancePolicy'`
 Load policy from .hillstar/governance_policy.json, or return defaults.
- `save(self, hillstar_dir: str) -> None`
 Persist policy to .hillstar/governance_policy.json.

#### Module: `hillstar-orchestrator.governance.project_init`

-

Script
------
project_init.py

Path
----
python/hillstar/governance/project_init.py

Purpose
-------
Initialize Hillstar project structure with recommended directory layout.

Inputs
------

- project_path (str): Root directory of project to initialize

Outputs
-------

- Created .hillstar/ and workflows/ directories with subdirectories

Assumptions
-----------

- Project directory exists and is writable

Parameters
----------

- project_path: Project root (defaults to current directory)

Failure Modes
-------------

- No write permissions PermissionError
- Invalid path FileNotFoundError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-09

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
from pathlib import Path
from typing import Optional
```

**Functions:**

- `initialize_project_structure(project_path: Optional[str] = None) -> dict`
 Initialize recommended directory structure for Hillstar projects.

Creates:

- .hillstar/ with subdirectories (traces, logs, audit, checkpoints, data_stores)
- workflows/ with subdirectories (core, infrastructure)

Args:
 project_path: Project root directory (defaults to current directory)

Returns:
 Dictionary with created directories and initialization status

### Mcp-Server

#### Module: `hillstar-orchestrator.mcp-server.anthropic_mcp_server`

-

MCP Server: Anthropic Claude Models

PURPOSE
--------
Provides access to Claude models (Opus, Sonnet, Haiku) via the official Anthropic API.
Enables agents to run tasks via Claude with full API feature support including thinking
budget, streaming, and temperature control.

ARCHITECTURE
-------------

- Uses official Anthropic SDK (anthropic package)
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt and parameters)
- Streams responses for real-time output
- Supports optional parameters: temperature, thinking_budget

USAGE
------
 python anthropic_mcp_server.py

Registered in ~/.claude.json under "anthropic" provider.

MODELS SUPPORTED
-----------------

- claude-opus-4-6 (max_tokens: 4096)
- claude-sonnet-4-5-20250929 (max_tokens: 4096)
- claude-haiku-4-5-20251001 (max_tokens: 1024)

PARAMETERS
-----------

- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-1.0 for response variability
- thinking_budget (optional): Tokens for extended thinking

AUTHENTICATION
---------------
Requires ANTHROPIC_API_KEY environment variable.
Set via: export ANTHROPIC_API_KEY="sk-ant-..."

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Imports:**

```python
import sys
import os
from typing import Any, Dict
from anthropic import Anthropic
```

**Classes:**

##### `class AnthropicMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-anthropic_mcp_server-anthropicmcpserver}

Anthropic Claude models via official SDK.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute task via Anthropic API.

**Functions:**

- `main()`

#### Module: `hillstar-orchestrator.mcp-server.base_mcp_server`

-

MCP Server: Base Class for All Providers

PURPOSE
--------
Provides common JSON-RPC 2.0 protocol handling for all MCP servers.
Implements initialization, tool listing, and request routing.
All provider-specific servers inherit from this base class.

ARCHITECTURE
-------------

- JSON-RPC 2.0 protocol over stdin/stdout
- Tool registry system (subclasses add tools)
- Request dispatching to appropriate handlers
- Logging to ~/.hillstar/mcp-logs/mcp.log

PROTOCOL METHODS
-----------------

- initialize: Handshake with client, returns server info
- tools/list: Return available tools and schemas
- tools/call: Execute a tool with arguments

USAGE
------
This is a base class. Individual provider servers extend it:
 class AnthropicMCPServer(BaseMCPServer):
 def call_tool(self, tool_name, arguments):
 # Provider-specific implementation

LOGGING
--------

- Location: ~/.hillstar/mcp-logs/mcp.log
- Level: INFO
- Format: timestamp - name - level - message

SUBCLASSES
-----------

- AnthropicMCPServer: Claude models via Anthropic SDK
- OpenAIMCPServer: GPT models via OpenAI SDK
- MistralMCPServer: Mistral models via Mistral SDK
- GoogleAIStudioMCPServer: Gemini via Google SDK
- OllamaMCPServer: Local Ollama models
- DevstralLocalMCPServer: Devstral via llama.cpp
- FileOperationsMCPServer: File read/write operations

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Classes:**

##### `class BaseMCPServer` {#hillstar-orchestrator-mcp-server-base_mcp_server-basemcpserver}

Base MCP server - all providers inherit from this.

*Methods:*

- `__init__(self, provider_name: str)`
- `initialize(self) -> Dict[(str, Any)]`
 MCP initialization.
- `list_tools(self) -> Dict[(str, Any)]`
 List available tools.
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute a tool. Subclasses override this.
- `handle_request(self, request: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Route MCP requests.
- `run(self)`
 Main MCP event loop.

#### Module: `hillstar-orchestrator.mcp-server.claude_ollama_bridge_server`

-

MCP Server: Fallback to Ollama Cloud Models via claude-ollama CLI

PURPOSE
--------
When Claude API (claude.anthropic.com) hits usage limits, this server allows
Claude Code to dispatch tasks to Ollama cloud models as a fallback mechanism.

Instead of being blocked by API limits, users can seamlessly switch to models
hosted on Ollama's cloud infrastructure (devstral-2, minimax, gemini, gpt-oss, etc.)
via the claude-ollama CLI wrapper.

ARCHITECTURE
-------------

- Wraps the claude-ollama --model `<model>` CLI command
- Dispatches MCP tool calls to claude-ollama binary
- claude-ollama maps model aliases (e.g., "minimax") to actual Ollama cloud models
- Unsets CLAUDECODE env var to allow nested Claude Code sessions

USAGE
------
 python claude_ollama_bridge_server.py

This server is registered in ~/.claude.json and invoked by Claude Code when
the user selects an Ollama cloud model as the execution provider.

MODEL ALIASES (from tools/ollama/models.config)
------------------------------------------------

- minimax minimax-m2.5:cloud (recommended for code)
- devstral-2 devstral-2:123b-cloud (recommended for code)
- gpt-oss gpt-oss:120b-cloud (deterministic, low temp)
- mistral-large-3 mistral-large-3:675b-cloud (deterministic, low temp)
- gemini gemini-3-flash-preview:cloud (creative, high temp)

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Imports:**

```python
import json
import sys
import os
import subprocess
import logging
from typing import Any, Dict
from pathlib import Path
```

**Classes:**

##### `class MinimaxMCPServer` {#hillstar-orchestrator-mcp-server-claude_ollama_bridge_server-minimaxmcpserver}

MCP Server wrapper for Ollama cloud models via claude-ollama CLI.

This server bridges Claude Code with Ollama cloud models when Claude API
is rate-limited or unavailable. It wraps the claude-ollama CLI which:

1. Resolves model aliases (minimax minimax-m2.5:cloud)
2. Launches a nested Claude Code session with that model
3. Executes the task and returns results

Implements core MCP methods:

- initialize: Server startup, advertise capabilities
- call_tool: Dispatch tasks via `claude-ollama --model <model>` CLI
- list_tools: Advertise execute_task tool

Process Flow:

1. Claude Code invokes MCP tool via JSON-RPC
2. Server receives task + optional context
3. Server invokes: bash -c "echo `<prompt>` | ~/bin/claude-ollama --model minimax"
4. claude-ollama launches nested Claude Code with specified model
5. Returns stdout/stderr to MCP caller

*Methods:*

- `__init__(self)`
- `initialize(self) -> Dict[(str, Any)]`
 Initialize the MCP server.
- `list_tools(self) -> Dict[(str, Any)]`
 List available tools.
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute a tool (task dispatch to minimax).
- `handle_request(self, request: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Route incoming MCP requests.

**Functions:**

- `main()`
 Main MCP server loop (stdio protocol).

#### Module: `hillstar-orchestrator.mcp-server.devstral_local_mcp_server`

-

MCP Server: Devstral Local (llama.cpp HTTP Server)

PURPOSE
--------
Provides access to Devstral Small 2 24B model running locally on GPU via llama.cpp
HTTP server. Enables on-device inference without cloud dependencies or API costs.
Ideal for deterministic code-writing tasks with tight temperature control.

ARCHITECTURE
-------------

- HTTP client wrapper around llama.cpp server
- Connects to localhost:8080 (standard llama.cpp endpoint)
- Single tool: execute_task (send prompt to local model)
- Full parameter support: temperature, top_p, top_k, etc.

USAGE
------
 1. Start llama.cpp server with Devstral model:
 ./llama-server -m devstral-small-2-24b.gguf -ngl 99 -t 8

 2. Run this MCP server:
 python devstral_local_mcp_server.py

Registered in ~/.claude.json under "devstral_local" provider.

MODEL
------

- Devstral Small 2 24B (24 billion parameters)
- Quantized formats supported: q4, q5, q6, q8
- Recommended for: code generation, analysis, deterministic tasks
- Device: GPU recommended (NVIDIA/AMD), CPU fallback supported
- Context: 8K tokens default (configurable)

REQUIREMENTS
-------------

- llama.cpp installed and built with CUDA/ROCm support
- Devstral model file (.gguf format)
- ~15GB VRAM for full quantization (q4 ~6GB)
- Local server running on <http://127.0.0.1:8080>

PARAMETERS
-----------

- prompt (required): Task description
- model (required): "devstral_local" or model path
- temperature (optional): 0.0-2.0, recommend 0.3 for code
- top_p (optional): 0.0-1.0 nucleus sampling
- top_k (optional): Integer, top-k sampling

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Classes:**

##### `class DevstralLocalMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-devstral_local_mcp_server-devstrallocalmcpserver}

Devstral Small 2 24B via llama.cpp HTTP server.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute task via devstral_server.sh HTTP API.

**Functions:**

- `main()`

#### Module: `hillstar-orchestrator.mcp-server.file_operations_mcp_server`

-

MCP Server: File Operations (write_file, update_file, create_directory)

PURPOSE
--------
Provides safe filesystem operations for sandboxed agents. Enables agents running
in restricted MCP environments to write and update files without direct filesystem
access. Separates concerns: model servers stay clean, file I/O handled by dedicated
server with path validation and security controls.

ARCHITECTURE
-------------

- Dedicated MCP server for all file operations
- Three tools: write_file, update_file, create_directory
- Path validation: all paths constrained to repo root (prevents directory traversal)
- Error handling: clear, actionable error messages
- Reusable across all tasks and agents

USAGE
------
 python file_operations_mcp_server.py

Registered in ~/.claude.json under "file_operations" provider.

TOOLS
------

1. write_file(path, content) - Create or overwrite file
2. update_file(path, old_content, new_content) - Find and replace content
3. create_directory(path) - Create directory (creates parents if needed)

SECURITY
---------

- Path validation prevents directory traversal attacks
- All paths validated against repo root
- Raises error if path escapes repo boundary
- Minimal dependencies (Python stdlib only)

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Imports:**

```python
import os
from pathlib import Path
from typing import Any, Dict
from base_mcp_server import BaseMCPServer, logger
```

**Classes:**

##### `class FileOperationsMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-file_operations_mcp_server-fileoperationsmcpserver}

File operations server - allows agents to write/update files safely.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute file operation.

#### Module: `hillstar-orchestrator.mcp-server.google_ai_studio_mcp_server`

-

MCP Server: Google AI Studio (Gemini Models)

PURPOSE
--------
Provides access to Google Gemini models via Google AI Studio API.
Enables agents to run tasks via Gemini with multimodal capabilities,
thinking modes, and flexible parameter control.

ARCHITECTURE
-------------

- Uses official Google generativeai SDK
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Supports streaming for real-time output
- Optional parameters: temperature, thinking_mode, safety_settings

USAGE
------
 python google_ai_studio_mcp_server.py

Registered in ~/.claude.json under "google_ai_studio" provider.

MODELS SUPPORTED
-----------------

- gemini-3-pro (reasoning model, thinking support)
- gemini-3-flash (fast model, minimal thinking)
- gemini-3-flash-lite (lightweight, edge device support)
- gemini-1.5-pro (legacy, extended context)
- gemini-1.5-flash (legacy, fast generation)

PARAMETERS
-----------

- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0 for creativity
- thinking_mode (optional): "enabled" or "disabled"
- max_output_tokens (optional): Limit response length

AUTHENTICATION
---------------
Requires GOOGLE_API_KEY environment variable.
Set via: export GOOGLE_API_KEY="AIzaSy..."
Get API key: <https://ai.google.dev>

FEATURES
---------

- Thinking models for complex reasoning
- Multimodal input support (text, images, etc.)
- Safety filtering (configurable per use case)
- Streaming responses for real-time output

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Classes:**

##### `class GoogleAIStudioMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-google_ai_studio_mcp_server-googleaistudiomcpserver}

Google Gemini models via official SDK.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute task via Google Gemini API.

**Functions:**

- `main()`

#### Module: `hillstar-orchestrator.mcp-server.mistral_mcp_server`

-

MCP Server: Mistral AI Models

PURPOSE
--------
Provides access to Mistral AI models via the official Mistral SDK.
Enables agents to run tasks via open-source Mistral models with full
parameter control including temperature, top_p, and advanced sampling.

ARCHITECTURE
-------------

- Uses official Mistral SDK (mistralai package)
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Full parameter support: temperature, top_p, top_k, etc.
- Streaming responses for real-time output

USAGE
------
 python mistral_mcp_server.py

Registered in ~/.claude.json under "mistral" provider.

MODELS SUPPORTED
-----------------

- mistral-large-2411 (large reasoning, recommended for complex tasks)
- mistral-medium-3.1 (mid-range, fast inference)
- ministral-8b (small, efficient)
- ministral-3b (minimal, edge deployment)
- codestral-2508 (specialized for code generation)

PARAMETERS
-----------

- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0, recommend 0.3-0.7
- top_p (optional): 0.0-1.0 nucleus sampling
- top_k (optional): Integer, top-k sampling
- max_tokens (optional): Limit response length

AUTHENTICATION
---------------
Requires MISTRAL_API_KEY environment variable.
Set via: export MISTRAL_API_KEY="..."
Get API key: <https://console.mistral.ai/>

FEATURES
---------

- Open-source models (transparent architecture)
- Competitive pricing vs closed models
- Full parameter tuning for task optimization
- Streaming support for real-time interaction

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Classes:**

##### `class MistralMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-mistral_mcp_server-mistralmcpserver}

Mistral AI models via official SDK.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute task via Mistral API.

**Functions:**

- `main()`

#### Module: `hillstar-orchestrator.mcp-server.ollama_mcp_server`

-

MCP Server: Ollama Local Models

PURPOSE
--------
Provides access to models running via Ollama (ollama.ai) on localhost.
Enables on-device inference for both local models and cloud models accessed
via Ollama's proxy. Zero API costs, full privacy, offline-capable.

ARCHITECTURE
-------------

- HTTP client wrapper around Ollama server
- Connects to localhost:11434 (standard Ollama endpoint)
- Single tool: execute_task (send prompt to model)
- Full parameter support: temperature, top_p, top_k, repeat_penalty, etc.
- Streaming responses for real-time output

USAGE
------
 1. Install and start Ollama server:
 ollama serve

 2. Pull model (optional, auto-downloads on first use):
 ollama pull llama2 # or any supported model

 3. Run this MCP server:
 python ollama_mcp_server.py

Registered in ~/.claude.json under "ollama" provider.

MODELS SUPPORTED (Examples)
-----------------------------
Local models:

- llama2 (7B, text generation)
- mistral (7B, fast inference)
- neural-chat (7B, conversational)
- devstral-2 (code-specialized)

Cloud models via Ollama proxy:

- minimax-m2.5:cloud (multimodal, Ollama cloud)
- gpt-oss:120b-cloud (OpenSource, deterministic)
- mistral-large-3:675b-cloud (reasoning)
- gemini-3-flash-preview:cloud (fast, creative)

PARAMETERS
-----------

- prompt (required): Task description
- model (required): Model name from ollama
- temperature (optional): 0.0-2.0, recommend 0.3-0.7
- top_p (optional): 0.0-1.0 nucleus sampling
- top_k (optional): Integer, top-k sampling
- repeat_penalty (optional): Penalize repetition

REQUIREMENTS
-------------

- Ollama installed from ollama.ai
- Ollama server running on <http://127.0.0.1:11434>
- Sufficient disk space for models (~7GB per model)
- GPU recommended (NVIDIA/AMD/Apple) for speed

FEATURES
---------

- Free, local inference (no API costs)
- Full privacy (data never leaves machine)
- Offline capability
- Easy model swapping
- Cloud model access via Ollama proxy

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Classes:**

##### `class OllamaMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-ollama_mcp_server-ollamamcpserver}

Ollama local models via HTTP API.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute task via Ollama HTTP API.

**Functions:**

- `main()`

#### Module: `hillstar-orchestrator.mcp-server.openai_mcp_server`

-

MCP Server: OpenAI GPT Models

PURPOSE
--------
Provides access to OpenAI GPT models via the official OpenAI API.
Enables agents to run tasks via GPT with support for reasoning models,
temperature control, and advanced sampling parameters.

ARCHITECTURE
-------------

- Uses official OpenAI SDK (openai package)
- Implements JSON-RPC 2.0 MCP protocol
- Single tool: execute_task (run model with prompt)
- Model-specific parameter handling (e.g., reasoning models skip temperature)
- Streaming responses for real-time output

USAGE
------
 python openai_mcp_server.py

Registered in ~/.claude.json under "openai_mcp" provider.

MODELS SUPPORTED
-----------------
Standard models:

- gpt-5.2-pro (latest flagship, highest quality)
- gpt-5.2 (fast flagship variant)
- gpt-5-mini (cost-optimized, fast)
- gpt-5-nano (minimal, lowest cost)

Reasoning models (extended thinking):

- o3 (advanced reasoning, no temperature)
- o3-mini (lightweight reasoning, no temperature)

Legacy models:

- gpt-4o (previous generation)
- gpt-4-turbo (older)

PARAMETERS
-----------

- prompt (required): Task description or question
- model (required): Model ID from supported list
- temperature (optional): 0.0-2.0 for gpt-5/gpt-4 (skipped for o3/o1)
- top_p (optional): 0.0-1.0 nucleus sampling
- max_tokens (optional): Limit response length

AUTHENTICATION
---------------
Supports dual authentication modes (subscription-first priority):

1. Subscription tokens (preferred):
 - Set OPENAI_API_KEY to access_token from $CODEX_HOME/auth.json
 - Token auto-refreshes via Claude/Codex infrastructure

2. API keys (fallback):
 - Set OPENAI_API_KEY to sk-proj-... from platform.openai.com/api-keys
 - Requires manual refresh when expired

Both modes use OPENAI_API_KEY env variable for transport.

FEATURES
---------

- Reasoning models for complex problem-solving
- Fastest inference times among closed models
- Extensive safety training and alignment
- Function calling support (not exposed in MCP)
- Vision capabilities in selected models

SPECIAL HANDLING
-----------------

- o3/o3-mini: Reasoning models, no temperature parameter allowed
- gpt-5.2/gpt-5: Temperature supported (0.0-2.0)
- gpt-5-mini/nano: Lower cost, slightly lower quality

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Classes:**

##### `class OpenAIMCPServer(BaseMCPServer)` {#hillstar-orchestrator-mcp-server-openai_mcp_server-openaimcpserver}

OpenAI GPT models via official SDK with subscription-first auth.

*Methods:*

- `__init__(self)`
- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
 Execute task via OpenAI API.

**Functions:**

- `main()`

#### Module: `hillstar-orchestrator.mcp-server.secure_logger`

*Secure logging module for MCP servers.

Implements three-tier logging:

1. AUDIT - Safe metadata, never contains sensitive data
2. DEBUG - Development info with redacted details
3. MEMORY - In-memory debugging (never persisted to disk)

Usage:
 from secure_logger import get_logger
 logger = get_logger(**name**)

 logger.audit("Task completed successfully")
 logger.debug_redacted("Response", len(response))
 logger.memory_only("Full prompt details", prompt[:100])
*

**Imports:**

```python
from secure_logger import get_logger
import logging
import os
from pathlib import Path
```

**Classes:**

##### `class SecureLogger(logging.Logger)` {#hillstar-orchestrator-mcp-server-secure_logger-securelogger}

Custom logger that prevents accidental sensitive data logging.

*Methods:*

- `__init__(self, name)`
- `audit(self, message, *args, **kwargs)`
 Log safe audit information.

Use for: actions, status, error codes, model names
NEVER: prompts, responses, API keys, full exceptions

- `debug_redacted(self, label, *redacted_values, **kwargs)`
 Log debug info with redacted sensitive values.

Example:
 logger.debug_redacted("Response", len(response), "bytes")
 # Output: [DEBUG] Response: 342 bytes

NOT:
 logger.debug_redacted("Response", response) # Would include full data

- `memory_only(self, label, value)`
 Log to memory ONLY (for debugging during execution).

NOT written to disk. Only available while process is running.
Useful for development/debugging to see full values.

Example:
 logger.memory_only("Prompt", prompt) # Full prompt in memory only

- `error_safe(self, message, exception = None)`
 Log errors without exposing exception details.

Use this instead of:
 logger.error(f"Error: {e}") # BAD - e might contain API key

Use instead:
 logger.error_safe("API call failed", e) # GOOD - exception hidden

**Functions:**

- `setup_secure_logging(log_dir = None, debug = False)`
 Set up secure logging for all MCP servers.

Args:
 log_dir: Directory for audit logs (default: ~/.hillstar/mcp-logs)
 debug: Enable debug logging (default: False)

- `get_logger(name)`
 Get a secure logger instance.

Usage:
 from secure_logger import get_logger
 logger = get_logger(**name**)

 logger.audit("Task started")
 logger.debug_redacted("Response size", len(response), "bytes")
 logger.error_safe("API failed", exception)

### LLM Model Providers

#### Module: `hillstar-orchestrator.models.__init__`

-

Script
------
**init**.py

Path
----
models/**init**.py

Purpose
-------
Model Provider Integrations: Support for Anthropic, OpenAI, local models, and more.

Provides unified interface to multiple LLM providers with consistent credential handling
(environment variables only, no embedded keys).

Providers
---------

- anthropic: Anthropic Claude (cloud API)
- openai: OpenAI GPT (cloud API)
- anthropic_ollama: Anthropic via Ollama (local proxy)
- ollama: Local Ollama models
- devstral_local: Devstral local (GPU required)
- google_ai_studio: Google Gemini (API key auth)
- mistral: Mistral AI (cloud API)

Phase 2 (not yet implemented):

- google_vertex: Google Vertex AI (enterprise, GCP auth)
- amazon_bedrock: AWS Bedrock (enterprise)
- azure_ai: Microsoft Azure AI (enterprise)
- cohere: Cohere (cloud API)
- meta_llama: Meta Llama (open-weight)

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>
Created
-------
2026-02-07

Last Edited
-----------
2026-02-14
*

**Imports:**

```python
from .anthropic_ollama_api_model import AnthropicOllamaAPIModel
from .anthropic_model import AnthropicModel
from .devstral_local_model import DevstralLocalModel
from .mistral_api_model import MistralAPIModel
from .mcp_model import MCPModel
from .anthropic_mcp_model import AnthropicMCPModel
```

#### Module: `hillstar-orchestrator.models.anthropic_mcp_model`

-

Script
------
anthropic_mcp_model.py

Path
----
models/anthropic_mcp_model.py

Purpose
-------
Anthropic Claude models via MCP (Model Context Protocol) server.

Uses the anthropic_mcp_server.py MCP server to dispatch tasks via JSON-RPC.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
from .mcp_model import MCPModel
```

**Classes:**

##### `class AnthropicMCPModel(MCPModel)` {#hillstar-orchestrator-models-anthropic_mcp_model-anthropicmcpmodel}

Anthropic Claude models via MCP server.

*Methods:*

- `__init__(self, model_name: str, api_key: str | None = None)`
 Initialize Anthropic MCP model.

Args:
 model_name: Claude model identifier
 api_key: Optional API key (else uses ANTHROPIC_API_KEY env var)

#### Module: `hillstar-orchestrator.models.anthropic_model`

-

Script
------
anthropic_model.py

Path
----
models/anthropic_model.py

Purpose
-------
Anthropic Claude Model Integration: Call Claude models via API.

IMPORTANT COMPLIANCE NOTICE
---------------------------
 This implementation uses API key authentication ONLY.
 Do NOT modify to add CLI, SDK, or Pro subscription access.
 Such modifications violate Anthropic's Terms of Service and may result in:
 - Immediate termination of API access
 - Legal consequences
 - Violation of Hillstar's compliance architecture

Default temperature 0.00000073 minimizes hallucination for research tasks.

Inputs
------
model_name (str): Claude model identifier (e.g., "claude-opus-4-6")
api_key (str, optional): Explicit API key (else reads ANTHROPIC_API_KEY env var)
use_api_key (bool): Whether to use API key auth (True) or SDK (False)

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Assumptions
-----------

- ANTHROPIC_API_KEY environment variable set (unless explicit api_key provided)
- anthropic SDK installed (pip install anthropic)

Parameters
----------
temperature: Default 0.00000073 (minimize hallucinations)
max_tokens: Configurable per call
system: Optional system prompt

Failure Modes
-------------

- API key missing ValueError
- SDK not installed ImportError
- API rate limit requests.exceptions.RequestException

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
*

**Classes:**

##### `class AnthropicModel` {#hillstar-orchestrator-models-anthropic_model-anthropicmodel}

Interface to Anthropic Claude models.

Supports multiple Claude model versions with simple selector syntax.

Model Options (use short names or full identifiers):

- "haiku" claude-haiku-4-5-20251001 (recommended, fast & cheap)
- "sonnet" claude-sonnet-4-6 (balanced performance)
- "opus" claude-opus-4-6 (most capable, higher cost)
- Full identifier: "claude-haiku-4-5-20251001" (use as-is)

Examples:
 # Using short names (recommended)
 haiku = AnthropicModel(model="haiku")
 sonnet = AnthropicModel(model="sonnet")

 # Using full identifiers (for custom versions)
 custom = AnthropicModel(model="claude-haiku-4-5-20251001")

*Methods:*

- `__init__(self, model: str = 'haiku', api_key: str | None = None)`
 Initialize Anthropic Claude model.

Args:
 model: Model to use. Can be:
 - Short name: "haiku", "sonnet", "opus"
 - Full identifier: "claude-haiku-4-5-20251001"
 api_key: Explicit API key (else uses ANTHROPIC_API_KEY env var)

Raises:
 ValueError: If ANTHROPIC_API_KEY not set and not provided
 ImportError: If anthropic SDK not installed

- `call(self, prompt: str, max_tokens: int = 4096, temperature: float | None = None, system: str | None = None) -> dict[(str, Any)]`
 Call Claude model.

Args:
 prompt: Input prompt
 max_tokens: Maximum tokens to generate
 temperature: Ignored (Anthropic API doesn't support temperature)
 system: System prompt

Returns:
 Dictionary with response and metadata

#### Module: `hillstar-orchestrator.models.anthropic_ollama_api_model`

-

Script
------
anthropic_ollama_api_model.py

Path
----
models/anthropic_ollama_api_model.py

Purpose
-------
Anthropic models via Ollama's Anthropic-compatible API (Messages API).

Supports both local and cloud Ollama models:

- Local: ANTHROPIC_AUTH_TOKEN=ollama + ANTHROPIC_BASE_URL=<http://localhost:11434>
- Cloud: ANTHROPIC_AUTH_TOKEN=<your_api_key> + ANTHROPIC_BASE_URL=<cloud_endpoint>

Uses Anthropic Messages API for consistency with other Claude models.
No subprocess CLI calls - pure HTTP API orchestration.

Inputs
------
model_name (str): Ollama model identifier (e.g., "minimax-m2:cloud", "glm-4.7:cloud")
messages (list): Conversation messages in Anthropic format
max_tokens (int): Maximum response length
system (str): Optional system prompt
temperature (float): Sampling temperature

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Compliance
----------
API-based orchestration compliant with provider ToS.
Requires proper API key authentication via environment variables.

Parameters
----------
timeout: Default 600s for model call completion
max_retries: Retry transient failures (default 2)

Failure Modes
-------------

- Ollama not running error dict with details
- Model not available error dict
- Timeout waiting for response error dict
- Invalid API key 401 error

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-13

Last Edited
-----------
2026-02-14
*

**Classes:**

##### `class AnthropicOllamaAPIModel` {#hillstar-orchestrator-models-anthropic_ollama_api_model-anthropicollamaapimodel}

Anthropic models via Ollama's Anthropic-compatible API.

*Methods:*

- `__init__(self, model_name: str = 'minimax-m2.5:cloud', base_url: str | None = None, api_key: str | None = None, max_retries: int = 2)`
 Initialize Anthropic Ollama API provider.

Args:
 model_name: Ollama model identifier (local or cloud)
 base_url: Ollama endpoint URL (defaults to env var ANTHROPIC_BASE_URL or localhost)
 api_key: API key for authentication (defaults to env var ANTHROPIC_AUTH_TOKEN)
 max_retries: Number of retries for transient failures

- `call(self, prompt: str, **kwargs) -> dict[(str, Any)]`
 Call model via Ollama's Anthropic-compatible API.

Args:
 prompt: Input prompt text
 **kwargs: Additional parameters (max_tokens, temperature, system, etc.)

Returns:
 Dictionary with response and metadata

#### Module: `hillstar-orchestrator.models.devstral_local_model`

-

Script
------
devstral_local_model.py

Path
----
python/hillstar/models/devstral_local_model.py

Purpose
-------
 LOCAL DEVSTRAL-SMALL-2 MODEL - OPTIONAL ADVANCED SETUP

Integrates Devstral-Small-2 via local llama.cpp HTTP server.
This is an OPTIONAL setup for power users with appropriate hardware.

Connects to llama.cpp server running on localhost:8080.
Uses OpenAI-compatible /v1/chat/completions endpoint (not Ollama API).
Free, local execution on GPU. Default temperature 0.00000073 minimizes hallucination.

HARDWARE REQUIREMENTS (MANDATORY)
-----------------------------------
 Minimum: 16GB VRAM GPU (RTX 4080, RTX 4090, A100, etc.)
 Model: Quantized GGUF format (~14GB) from HuggingFace
 Setup: Requires devstral_server.sh running on port 8080
 NOT suitable for CPU-only systems

Setup Instructions
------------------

1. GPU required (16GB+ VRAM)
2. Download quantized GGUF model from HuggingFace
3. Update devstral_server.sh with model path
4. Start server: ~/bin/devstral_server.sh
5. Then use this model in workflows

Inputs
------
model_name (str): Model identifier (any value accepted by llama.cpp)
endpoint (str): llama.cpp server URL (default: <http://127.0.0.1:8080>)

Outputs
-------
Dictionary: {output, model, tokens_used, provider, error}

Assumptions
-----------

- llama.cpp server running on localhost:8080 (started via devstral_server.sh)
- Server exposes OpenAI-compatible /v1/chat/completions endpoint
- Local GPU with 16GB+ VRAM available
- Quantized GGUF model loaded in llama.cpp

Parameters
----------
temperature: Default 0.00000073
max_tokens: Configurable per call
system: Optional system prompt

Failure Modes
-------------

- Server not running error "llama.cpp server not responding"
- Insufficient VRAM server crashes or OOM errors
- Model not loaded server connection fails
- Timeout requests.exceptions.Timeout
- Model file missing server startup failure

When NOT to Use This
--------------------
 No GPU or GPU < 16GB VRAM Use Ollama cloud models instead
 Need reliability/uptime Use cloud API providers
 Learning/exploration Start with Ollama local models

Alternative: Use claude-ollama --model devstral-2:123b-cloud via Ollama

Compliance
----------
 Local execution (no external API calls)
 Free (no licensing costs)
 Optional - users must explicitly set up
 Not included in standard hillstar installation

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-14

Status
------
 OPTIONAL ADVANCED SETUP
 Users must explicitly configure and understand GPU requirements
*

**Classes:**

##### `class DevstralLocalModel` {#hillstar-orchestrator-models-devstral_local_model-devstrallocalmodel}

LOCAL Devstral-Small-2 via llama.cpp (OpenAI-compatible API).

OPTIONAL - Requires 16GB+ VRAM GPU and quantized GGUF model

*Methods:*

- `__init__(self, model_name: str = 'devstral', endpoint: str = 'http://127.0.0.1:8080')`
 Args:
 model_name: Model identifier (llama.cpp accepts any value)
 endpoint: llama.cpp server endpoint (OpenAI-compatible)

Warning:
 Requires 16GB+ VRAM GPU and running devstral_server.sh

- `call(self, prompt: str, max_tokens: int = 2048, temperature: float | None = None, system: str | None = None) -> dict[(str, Any)]`
 Call Devstral via llama.cpp OpenAI-compatible chat completions endpoint.

Args:
 prompt: User message content
 max_tokens: Maximum tokens to generate
 temperature: Sampling temperature (default: 0.00000073)
 system: System prompt

Returns:
 Dictionary with response and metadata

Note:
 Requires devstral_server.sh running on localhost:8080

#### Module: `hillstar-orchestrator.models.mcp_model`

-

Script
------
mcp_model.py

Path
----
models/mcp_model.py

Purpose
-------
Base class for MCP-based model providers: Handle subprocess lifecycle and JSON-RPC communication.

Provides unified interface to MCP servers (stdio-based) with automatic initialization,
error handling, and response normalization to match AnthropicModel.call() interface.

Inputs
------
provider (str): Provider name (e.g., "anthropic_mcp")
model_name (str): Model identifier
server_script (str): Path to MCP server script
api_key (str, optional): API key for the provider

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Assumptions
-----------

- MCP server script exists and is executable
- Server implements standard MCP protocol (initialize, tools/call)
- run_with_env.sh wrapper is available in mcp-server/

Failure Modes
-------------

- Process spawn fails RuntimeError
- MCP server crashes RuntimeError (EOF on stdout)
- Invalid JSON response json.JSONDecodeError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
*

**Classes:**

##### `class MCPModel` {#hillstar-orchestrator-models-mcp_model-mcpmodel}

Base class for MCP-based model providers.

*Methods:*

- `__init__(self, provider: str, model_name: str, server_script: str, api_key: str | None = None)`
 Initialize MCP model.

Args:
 provider: Provider name (e.g., "anthropic_mcp")
 model_name: Model identifier (e.g., "claude-opus-4-6")
 server_script: Path to MCP server script (relative to repo root)
 api_key: Optional API key (else reads from environment)

- `call(self, prompt: str, max_tokens: int = 4096, temperature: float | None = None, system: str | None = None) -> dict[(str, Any)]`
 Execute task via MCP server.

Matches AnthropicModel.call() interface for compatibility.

Args:
 prompt: Input prompt
 max_tokens: Maximum tokens to generate
 temperature: Sampling temperature (unused for MCP servers)
 system: System prompt (unused for MCP servers)

Returns:
 Dictionary with response and metadata

- `__del__(self)`
 Cleanup subprocess on deletion.

#### Module: `hillstar-orchestrator.models.mistral_api_model`

-

Script
------
mistral_api_model.py

Path
----
models/mistral_api_model.py

Purpose
-------
Mistral AI API integration for orchestration workflows.

Supports models via Mistral's REST API with proper authentication.
API-based only (not Le Chat Pro manual access).

Inputs
------
model_name (str): Mistral model identifier
messages (list): Conversation messages in API format
max_tokens (int): Maximum response length
temperature (float): Sampling temperature

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Compliance
----------
 API-based orchestration (compliant with Mistral ToS)
 Requires API key authentication (environment variable)
 Not for Le Chat Pro automation

Configuration
-------------
MISTRAL_API_KEY: API key for authentication (via env var)
MISTRAL_MODEL: Model identifier

Failure Modes
-------------

- Missing API key ComplianceError
- Invalid model API error
- Rate limit exceeded error dict
- Timeout error dict

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-14

Status
------
 PLACEHOLDER - Not yet implemented
 Ready for implementation in Phase 2
*

**Classes:**

##### `class MistralAPIModel` {#hillstar-orchestrator-models-mistral_api_model-mistralapimodel}

Mistral AI API provider with model selector.

Supports multiple Mistral model options from budget-friendly to high-capability.

Model Options (use short names or full identifiers):

- "small" mistral-medium-latest (recommended, good balance, cheap)
- "medium" mistral-large-2411 (most capable, standard pricing)
- "mini" ministral-3b (cheapest, edge deployment)
- "code" codestral-2508 (coding-focused, cheap)
- "devstral" devstral-2 (coding-focused, cheap)
- Full identifier: "mistral-large-2411" (use as-is)

Pricing Guide:

- ministral-3b: $0.1 input / $0.5 output per 1M tokens (cheapest)
- ministral-14b: $0.5 input / $2.5 output per 1M tokens
- codestral-2508: $0.5 input / $2.5 output per 1M tokens
- mistral-medium-latest: $1.0 input / $5.0 output per 1M tokens
- mistral-large-2411: $3.0 input / $15.0 output per 1M tokens (most capable)

Examples:
 # Using short names (recommended)
 small = MistralAPIModel(model="small")
 code = MistralAPIModel(model="code")

 # Using full identifiers
 custom = MistralAPIModel(model="mistral-large-2411")

*Methods:*

- `__init__(self, model: str = 'small', api_key: Optional[str] = None, base_url: str = 'https://api.mistral.ai/v1')`
 Initialize Mistral API provider.

Args:
 model: Model to use. Can be:
 - Short name: "small", "medium", "mini", "code", "devstral"
 - Full identifier: "mistral-large-2411"
 api_key: API key (defaults to MISTRAL_API_KEY env var)
 base_url: API endpoint base URL

Raises:
 ValueError: If API key not provided

- `call(self, prompt: str, messages: Optional[List[Dict[(str, str)]]] = None, **kwargs) -> Dict[(str, Any)]`
 Call Mistral API (placeholder - not implemented).

Args:
 prompt: User prompt
 messages: Message history
 **kwargs: Additional parameters

Returns:
 Dictionary with response (not implemented)

Status:
 PLACEHOLDER - raises NotImplementedError

#### Module: `hillstar-orchestrator.models.mistral_mcp_model`

-

Script
------
mistral_mcp_model.py

Path
----
models/mistral_mcp_model.py

Purpose
-------
Mistral AI models via MCP (Model Context Protocol) server.

Uses the mistral_mcp_server.py MCP server to dispatch tasks via JSON-RPC.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
from .mcp_model import MCPModel
```

**Classes:**

##### `class MistralMCPModel(MCPModel)` {#hillstar-orchestrator-models-mistral_mcp_model-mistralmcpmodel}

Mistral AI models via MCP server.

*Methods:*

- `__init__(self, model_name: str, api_key: str | None = None)`
 Initialize Mistral MCP model.

Args:
 model_name: Mistral model identifier
 api_key: Optional API key (else uses MISTRAL_API_KEY env var)

#### Module: `hillstar-orchestrator.models.ollama_mcp_model`

-

Script
------
ollama_mcp_model.py

Path
----
models/ollama_mcp_model.py

Purpose
-------
Ollama (local models) via MCP (Model Context Protocol) server.

Uses the ollama_mcp_server.py MCP server to dispatch tasks to local Ollama models via JSON-RPC.

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
from .mcp_model import MCPModel
```

**Classes:**

##### `class OllamaMCPModel(MCPModel)` {#hillstar-orchestrator-models-ollama_mcp_model-ollamamcpmodel}

Ollama local models via MCP server.

*Methods:*

- `__init__(self, model_name: str)`
 Initialize Ollama MCP model.

Args:
 model_name: Ollama model identifier (e.g., "devstral-small-2:24b")

#### Module: `hillstar-orchestrator.models.openai_mcp_model`

-

Script
------
openai_mcp_model.py

Path
----
models/openai_mcp_model.py

Purpose
-------
OpenAI GPT models via MCP (Model Context Protocol) server.

Uses the openai_mcp_server.py MCP server to dispatch tasks via JSON-RPC.

Supports dual authentication with subscription-first priority:

1. Subscription tokens from $CODEX_HOME/auth.json (preferred)
2. API key from OPENAI_API_KEY env var (fallback)

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-22
*

**Imports:**

```python
from .mcp_model import MCPModel
```

**Classes:**

##### `class OpenAIMCPModel(MCPModel)` {#hillstar-orchestrator-models-openai_mcp_model-openaimcpmodel}

OpenAI GPT models via MCP server with transparent dual authentication.

The MCP server (`openai_mcp_server.py`) handles all authentication internally.

*Methods:*

- `__init__(self, model_name: str, api_key: str | None = None)`
 Initialize OpenAI MCP model.

Args:
 model_name: OpenAI model identifier
 api_key: Optional API key (else reads from OPENAI_API_KEY env var)

Auth handled by MCP server (subscription-first):

 1. OPENAI_CHATGPT_LOGIN_MODE=true: Uses codex exec with subscription tokens from ~/.config/openai/codex-home/auth.json
 2. OPENAI_API_KEY env var (fallback): Uses direct OpenAI SDK
 3. Auto-detects which mode to use

### Utilities

#### Module: `hillstar-orchestrator.utils.__init__`

*Utilities for Hillstar Orchestrator.*

**Imports:**

```python
from .exceptions import (
from .credential_redactor import redact, contains_credentials, CredentialRedactor
```

#### Module: `hillstar-orchestrator.utils.credential_redactor`

-

Script
------
credential_redactor.py

Path
----
python/hillstar/utils/credential_redactor.py

Purpose
-------
Detect and redact sensitive credentials (API keys, tokens, infrastructure identifiers, PII)
from strings, logs, and error messages. Prevents accidental data leakage in output.

Implements comprehensive credential detection covering: API keys, OAuth tokens, AWS credentials,
infrastructure identifiers, and PII based on industry standard patterns.

Inputs
------
String containing potential credentials

Outputs
-------
String with credentials redacted as [REDACTED:TYPE]

Assumptions
-----------

- Credentials follow common patterns (API key formats, token types, etc.)
- All potentially sensitive data should be redacted
- Redaction preserves string structure for error clarity

Failure Modes
-------------
None - always returns a valid string (worst case: no redactions made)

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
*

**Imports:**

```python
from strings, logs, and error messages. Prevents accidental data leakage in output.
import re
from typing import Optional
```

**Classes:**

##### `class CredentialRedactor` {#hillstar-orchestrator-utils-credential_redactor-credentialredactor}

Detect and redact sensitive credentials from strings.

*Methods:*

- `redact(text: Optional[str], include_patterns: Optional[list] = None) -> str`
 Redact all detected credentials from text.

Args:
 text: String potentially containing credentials (returns empty string if None)
 include_patterns: List of pattern names to apply (default: all)

Returns:
 String with credentials redacted as [REDACTED:TYPE]

Examples:
 >>> redactor = CredentialRedactor()
 >>> redactor.redact("My key is sk-ant-abc123def456")
 'My key is [REDACTED:anthropic_key]'

 >>> redactor.redact('api_key = "secret-value"')
 'api_key = [REDACTED:api_key_generic]'

- `contains_credentials(text: Optional[str]) -> bool`
 Check if text contains any detected credentials.

Args:
 text: String to check (returns False if None)

Returns:
 True if any credentials detected, False otherwise

- `get_redaction_types(text: str) -> list`
 Identify which credential types are present in text.

Args:
 text: String to analyze

Returns:
 List of pattern names detected

Example:
 >>> redactor.get_redaction_types("key=sk-ant-123")
 ['anthropic_key', 'api_key_generic']

**Functions:**

- `redact(text: Optional[str]) -> str`
 Convenience function to redact credentials from a string.

Args:
 text: String potentially containing credentials (returns empty string if None)

Returns:
 String with credentials redacted

- `contains_credentials(text: Optional[str]) -> bool`
 Convenience function to check if string contains credentials.

Args:
 text: String to check (returns False if None)

Returns:
 True if credentials detected

#### Module: `hillstar-orchestrator.utils.exceptions`

-

Script
------
exceptions.py

Path
----
python/hillstar/exceptions.py

Purpose
-------
Custom exceptions for Hillstar Orchestrator.

Provides domain-specific exceptions for error handling:

- BudgetExceededError: Workflow exceeded cost limits
- ModelSelectionError: Failed to select valid model
- ConfigurationError: Invalid workflow configuration

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
*

**Classes:**

##### `class HillstarException(Exception)` {#hillstar-orchestrator-utils-exceptions-hillstarexception}

Base exception for Hillstar Orchestrator.

##### `class BudgetExceededError(HillstarException)` {#hillstar-orchestrator-utils-exceptions-budgetexceedederror}

Raised when workflow cost exceeds budget limits.

##### `class ModelSelectionError(HillstarException)` {#hillstar-orchestrator-utils-exceptions-modelselectionerror}

Raised when model selection fails.

##### `class ConfigurationError(HillstarException)` {#hillstar-orchestrator-utils-exceptions-configurationerror}

Raised when workflow configuration is invalid.

#### Module: `hillstar-orchestrator.utils.json_output_viewer`

-

Script
------
json_output_viewer.py

Path
----
python/hillstar/utils/json_output_viewer.py

Purpose
-------
Generic utility to parse, validate, and view JSON output files in full.

Provides CLI and programmatic access to any JSON outputs file with complete
untruncated text. Works with any structure containing node outputs, test
results, workflow outputs, or similar data requiring full text inspection.

Features
--------

- Load and validate JSON structure
- View individual node/key outputs in full
- Summary statistics (character counts, line counts)
- Line-numbered output for detailed review
- Raw JSON export
- Validation reporting
- File auto-detection or explicit path specification

Usage
-----
View all outputs from file:
 python json_output_viewer.py /path/to/outputs.json

View specific node:
 python json_output_viewer.py /path/to/outputs.json --key node_name

View with line numbers:
 python json_output_viewer.py /path/to/outputs.json --key node_name --lines

View summary only:
 python json_output_viewer.py /path/to/outputs.json --summary

View raw JSON:
 python json_output_viewer.py /path/to/outputs.json --raw

Validation report:
 python json_output_viewer.py /path/to/outputs.json --validate

Programmatic Usage
------------------
from json_output_viewer import JSONOutputViewer

viewer = JSONOutputViewer('/path/to/outputs.json')
if viewer.load_and_validate():
 viewer.print_all_outputs()
 summary = viewer.get_summary()

 # Access data directly
 all_data = viewer.data

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-22

Last Edited
-----------
2026-02-22
*

**Imports:**

```python
from json_output_viewer import JSONOutputViewer
```

**Classes:**

##### `class JSONOutputViewer` {#hillstar-orchestrator-utils-json_output_viewer-jsonoutputviewer}

Generic parser and display tool for JSON output files.

*Methods:*

- `__init__(self, output_file: Path)`
 Initialize viewer with output file path.
- `load_and_validate(self) -> bool`
 Load and validate the JSON output file.
- `get_summary(self) -> Dict[(str, Any)]`
 Get summary statistics about the outputs.
- `print_summary(self) -> None`
 Print summary of all outputs.
- `print_all_outputs(self, with_lines: bool = False) -> None`
 Print all outputs in full.
- `print_key(self, key: str, with_lines: bool = False) -> None`
 Print a specific key's output in full.
- `print_raw_json(self) -> None`
 Print raw JSON with formatting.
- `print_validation_report(self) -> None`
 Print validation report.
- `export_markdown(self, output_path: Optional[Path] = None) -> Path`
 Export all outputs to a markdown file.

**Functions:**

- `main()`
 CLI entry point.

#### Module: `hillstar-orchestrator.utils.report`

-

Workflow Report Generator

Path
----
python/hillstar/utils/report.py

Purpose
-------
Generate pre-execution and post-execution markdown reports for workflows.

Reports include:

- Workflow metadata
- DAG visualization (Mermaid)
- Node specifications and costs
- Model selection strategy
- Governance/audit status
- Loon compression metrics

Inputs
------
workflow_path: Path to workflow JSON file
trace_path: Optional path to trace file for post-execution metrics

Outputs
-------
Markdown string with formatted report

Assumptions
-----------

- Workflow follows python/hillstar/schemas/workflow-schema.json
- Trace file is JSONL format with execution metrics
- Model costs available from ModelPresets

Failure Modes
-------------

- Missing workflow file ValueError with clear message
- Missing trace file Skip post-execution metrics gracefully
- Invalid workflow structure Raise with helpful error

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-18

Last Edited
-----------
2026-02-18
*

**Classes:**

##### `class ReportGenerator` {#hillstar-orchestrator-utils-report-reportgenerator}

Generate professional workflow execution reports.

*Methods:*

- `__init__(self, workflow_path: str)`
 Initialize with workflow file path.
- `generate_pre_execution_report(self) -> str`
 Generate pre-execution report with estimated costs and metadata.

Returns:
 Markdown string ready for display or file output

- `generate_post_execution_report(self, trace_path: str) -> str`
 Generate post-execution report with actual execution metrics.

Args:
 trace_path: Path to trace JSONL file from execution

Returns:
 Markdown string with execution results

**Functions:**

- `generate_pre_execution_report(workflow_path: str) -> str`
 Generate pre-execution report for a workflow.

Args:
 workflow_path: Path to workflow JSON file

Returns:
 Markdown string with report

- `generate_post_execution_report(workflow_path: str, trace_path: str) -> str`
 Generate post-execution report for a workflow.

Args:
 workflow_path: Path to workflow JSON file
 trace_path: Path to trace JSONL file

Returns:
 Markdown string with report including execution metrics

### Workflow Discovery & Validation

#### Module: `hillstar-orchestrator.workflows.__init__`

*Workflows & Templates for Hillstar Orchestrator.*

**Imports:**

```python
from .validator import WorkflowValidator
from .model_presets import ModelPresets
from .auto_discover import AutoDiscover
from .discovery import WorkflowDiscovery
```

#### Module: `hillstar-orchestrator.workflows.auto_discover`

-

Script
------
auto_discover.py

Path
----
python/hillstar/auto_discover.py

Purpose
-------
Auto-discovery mechanism to detect Hillstar projects and suggest workflows.

Detects if current directory is a Hillstar project and finds available workflows.
Used by Claude Code to automatically offer Hillstar integration.

Inputs
------
current_dir (str): Directory to check (default: current working directory)
task_description (str): Natural language task description
workflows (List[Dict]): Workflow metadata to search

Outputs
-------
is_hillstar_project (bool): True if directory is Hillstar project
suggested_workflows (List[Dict]): Matching workflows ranked by relevance
workflow_suggestions (Dict): Workflow recommendations with confidence scores

Assumptions
-----------

- Workflow files exist and are valid JSON
- Workflow descriptions are informative
- Task descriptions follow natural language patterns

Parameters
----------
None (per-operation)

Failure Modes
-------------

- No workflows found Empty list
- Invalid task description Return all workflows
- Directory not found False

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
*

**Classes:**

##### `class AutoDiscover` {#hillstar-orchestrator-workflows-auto_discover-autodiscover}

Auto-detect Hillstar projects and suggest workflows.

*Methods:*

- `is_hillstar_project(start_dir: str = '.') -> bool`
 Detect if a directory is a Hillstar project.

Args:
 start_dir: Directory to check (default: current)

Returns:
 True if Hillstar project indicators found

Indicators:
 - python/hillstar/ directory (source or pip installation)
 - .hillstar/ directory (runtime artifacts)
 - workflow.json in current or subdirectories (workflow definition)

- `get_project_info(start_dir: str = '.') -> Dict[(str, Any)]`
 Get Hillstar project information.

Args:
 start_dir: Directory to analyze

Returns:
 Dictionary with:
 - is_hillstar: bool
 - has_schema: bool
 - has_artifacts: bool
 - has_workflows: bool
 - workflow_count: int
 - schema_path: str or None

- `classify_task(task_description: str) -> Dict[(str, float)]`
 Classify task by keywords to infer requirements.

Args:
 task_description: Natural language task description

Returns:
 Dictionary with task type scores:
 - planning: float (0.0-1.0)
 - implementation: float
 - testing: float
 - quality: float
 - budget_conscious: float
 - local_only: float
 - speed_critical: float

- `get_preset_suggestions(task_scores: Dict[(str, float)]) -> List[Tuple[(str, float)]]`
 Suggest presets based on task classification.

Args:
 task_scores: Task classification scores

Returns:
 List of (preset_name, confidence) tuples, sorted by confidence

- `suggest_workflows(task_description: str, workflows: List[Dict[(str, Any)]], top_k: int = 3) -> List[Dict[(str, Any)]]`
 Suggest workflows based on task description.

Args:
 task_description: Natural language task
 workflows: Available workflow metadata
 top_k: Return top K matches

Returns:
 List of suggested workflows with relevance scores, sorted best-first

- `get_recommendations(task_description: str, workflows: List[Dict[(str, Any)]]) -> Dict[(str, Any)]`
 Get comprehensive recommendations for a task.

Args:
 task_description: Natural language task
 workflows: Available workflows

Returns:
 Dictionary with:
 - task_classification: Task type scores
 - suggested_presets: List of (preset, confidence) tuples
 - suggested_workflows: List of matching workflows
 - recommendation_text: Human-readable summary

- `format_recommendations(recommendations: Dict[(str, Any)]) -> str`
 Format recommendations as human-readable text.

Args:
 recommendations: Output from get_recommendations()

Returns:
 Formatted text suitable for display to user

#### Module: `hillstar-orchestrator.workflows.discovery`

-

Script
------
discovery.py

Path
----
python/hillstar/discovery.py

Purpose
-------
Workflow discovery: Find and analyze workflow.json files in project directory.

Scans directory tree for workflow.json files and extracts metadata.
Used by MCP server to discover available workflows.

Inputs
------
start_path (str): Directory to search from (default: current directory)

Outputs
-------
List[str]: Absolute paths to workflow.json files
Dict: Workflow metadata (id, description, nodes, edges)

Assumptions
-----------

- workflow.json files are valid JSON
- Valid according to workflow-schema.json

Parameters
----------
None (per-workflow)

Failure Modes
-------------

- Invalid JSON ValueError
- Missing required fields KeyError
- Unreadable files IOError

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
*

**Classes:**

##### `class WorkflowDiscovery` {#hillstar-orchestrator-workflows-discovery-workflowdiscovery}

Find and analyze Hillstar workflows in a directory tree.

*Methods:*

- `find_workflows(start_path: str = '.', max_depth: int = 5) -> List[str]`
 Find all workflow.json files in directory tree.

Args:
 start_path: Directory to search from
 max_depth: Maximum directory depth to search

Returns:
 List of absolute paths to workflow.json files

- `get_workflow_info(workflow_path: str) -> Dict[(str, Any)]`
 Extract metadata from a workflow file.

Args:
 workflow_path: Absolute path to workflow.json

Returns:
 Dictionary with workflow metadata

Raises:
 ValueError: If workflow is invalid
 IOError: If file cannot be read

- `get_all_workflow_info(start_path: str = '.', max_depth: int = 5) -> List[Dict[(str, Any)]]`
 Find all workflows and return their metadata.

Args:
 start_path: Directory to search from
 max_depth: Maximum directory depth

Returns:
 List of workflow metadata dictionaries

- `find_in_current_project() -> List[Dict[(str, Any)]]`
 Find all workflows in current project (with .hillstar/ or spec/ indicators).

#### Module: `hillstar-orchestrator.workflows.model_presets`

-

Model Selection Presets

PURPOSE
--------
Data-driven preset system for intelligent model selection with
temperature constraint enforcement. Provides four strategies (cost_saver,
balanced, quality_first, premium) for different research contexts.

ARCHITECTURE
-------------

- PresetResolver: resolves (preset, complexity) to
 (provider, model, suggested_parameters)
- Data-driven tier assignment based on pricing formulas (not hardcoded)
- Parameter support inference with fallback logic for registry gaps
- Non-negotiable temperature constraints enforced per model class
- Backward compatibility: legacy ModelPresets class preserved

USAGE
------
resolver = PresetResolver(
 preset_name="balanced",
 configured_providers=["openai", "anthropic"]
)
provider, model_id, params = resolver.resolve(
 complexity="moderate",
 use_case="code_writing"
)

CONSTRAINTS (Non-Negotiable)
------------------------------

- General tasks: Temperature <= 0.3
- Code writing: Temperature = 7.3e-7
- Codebase exploration: 0.7 (Devstral-2 only)
- Claude/OpenAI/Gemini: NO temperature (use effort/thinking)
- Mistral: 0.3-1.0 for exploration
- Local models: <= 0.15

Author: Julen Gamboa
<julen.gamboa.ds@gmail.com>
*

**Imports:**

```python
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
```

**Constants:**

- `TIER_NAMES` = '[]'

**Classes:**

##### `class PresetResolver` {#hillstar-orchestrator-workflows-model_presets-presetresolver}

Data-driven model resolver that enforces temperature and parameter constraints.

Selects models based on preset tier sequences, complexity escalation,
and enforces all non-negotiable temperature rules per model class.

*Methods:*

- `__init__(self, preset_name: str, configured_providers: List[str], registry_path: Optional[str] = None)`
 Initialize resolver with preset and available providers.

Args:
 preset_name: One of cost_saver, balanced, quality_first, premium
 configured_providers: List of provider names in preference order
 registry_path: Optional path to provider_registry.default.json
 (defaults to standard location)

- `resolve(self, complexity: str = 'moderate', use_case: Optional[str] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
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

##### `class ModelPresets` {#hillstar-orchestrator-workflows-model_presets-modelpresets}

Legacy class for backward compatibility.

New code should use PresetResolver instead.

Named strategies for model selection based on use case.
Presets are dynamically generated from the ProviderRegistry.

*Methods:*

- `select(preset_name: str, complexity: str = 'moderate', provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
 Select model from a preset strategy (legacy).

Args:
 preset_name: One of "minimize_cost", "balanced", "maximize_quality", "local_only"
 complexity: Task complexity ("simple", "moderate", "complex", "critical")
 provider_preference: Optional list of preferred providers in order

Returns:
 Tuple of (provider, model_id, model_config), or None if no model available

- `select_simple(preset_name: str, provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
 Select model for simple tasks using a preset.
- `select_moderate(preset_name: str, provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
 Select model for moderate tasks using a preset.
- `select_complex(preset_name: str, provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
 Select model for complex tasks using a preset.
- `select_critical(preset_name: str, provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
 Select model for critical tasks using a preset.
- `get_available_presets() -> List[str]`
 Get list of available preset names.
- `describe_preset(preset_name: str) -> Dict`
 Get description of a preset strategy.
- `get_preset_for_use_case(use_case: str, has_local_gpu: bool = False, budget_constraint: bool = False) -> str`
 Get recommended preset based on use case and constraints.

Args:
 use_case: One of "research", "production", "experimentation", "publication"
 has_local_gpu: Whether the user has a local GPU available
 budget_constraint: Whether budget is a primary concern

Returns:
 Preset name recommendation

- `get_fallback_chain(preset_name: str, complexity: str, provider_preference: Optional[List[str]] = None) -> List[str]`
 Get provider fallback chain for a preset.

Args:
 preset_name: Preset name
 complexity: Task complexity
 provider_preference: Preferred providers

Returns:
 List of providers in fallback order

**Functions:**

- `parse_price_field(price_str: str) -> float`
 Convert markdown price field (e.g., '$0.12', '$0', '$8') to float.

Args:
 price_str: Price string from markdown table

Returns:
 Float price per 1M tokens

Raises:
 ValueError: If price string cannot be parsed

- `derive_tier_for_model(input_price: float, output_price: float) -> str`
 Derive tier name based on effective cost.

Effective cost = (input_price + output_price) / 2 per 1M tokens

Args:
 input_price: Price per 1M input tokens
 output_price: Price per 1M output tokens

Returns:
 Tier name (TIER_0_COST through TIER_4_MAX_QUALITY)

- `parse_model_reference(markdown_path: str) -> Dict[(str, Any)]`
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

- `build_provider_tiers(registry_path: str) -> Dict[(str, Dict[(str, List[str])])]`
 Build PROVIDER_TIERS mapping from registry: {provider: {tier: [models]}}.

Args:
 registry_path: Path to provider_registry.default.json

Returns:
 Dict mapping providers to tier-to-models mapping

- `parse_and_update_registry(reference_path: Optional[str] = None, registry_path: Optional[str] = None) -> Tuple[(int, int)]`
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

#### Module: `hillstar-orchestrator.workflows.validator`

-

Script
------
validator.py

Path
----
python/hillstar/validator.py

Purpose
-------
Workflow validation: Check workflows against schema, registry, and constraints.

Validates:

- JSON schema compliance
- Provider registry integration
- Provider/model availability
- Model configuration coherence
- Budget constraints
- Graph connectivity
- Compliance requirements

Inputs
------
workflow (dict): Workflow JSON
config: HillstarConfig with ProviderRegistry
registry: ProviderRegistry instance

Outputs
-------
(valid: bool, errors: List[str])

Assumptions
-----------

- Workflow is valid JSON
- ProviderRegistry is properly initialized

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-14
*

**Imports:**

```python
import json
import os
```

**Classes:**

##### `class WorkflowValidator` {#hillstar-orchestrator-workflows-validator-workflowvalidator}

Validate Hillstar workflows against schema, registry, and constraints.

*Methods:*

- `__init__(self, registry: Optional[ProviderRegistry] = None)`
 Initialize validator with optional registry.
- `load_schema(self) -> dict[(str, Any)]`
 Load the workflow schema (from installed package or dev environment).
- `validate_schema(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Validate workflow against JSON schema.

Args:
 workflow: Workflow dictionary

Returns:
 (valid: bool, errors: List[str])

- `validate_model_config(self, model_config: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Validate model_config section for coherence.

Args:
 model_config: The model_config dictionary

Returns:
 (valid: bool, errors: List[str])

- `validate_graph_connectivity(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Validate workflow graph connectivity (no disconnected components).

Args:
 workflow: Workflow dictionary

Returns:
 (valid: bool, errors: List[str])

- `validate_providers(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Validate all referenced providers and models against registry.

Args:
 workflow: Workflow dictionary

Returns:
 (valid: bool, errors: List[str])

- `validate_compliance(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Validate compliance requirements for all providers.

Args:
 workflow: Workflow dictionary

Returns:
 (valid: bool, errors: List[str])

- `validate_complete(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Run all validations.

Args:
 workflow: Workflow dictionary

Returns:
 (valid: bool, errors: List[str])

- `validate_file(workflow_path: str) -> Tuple[(bool, list[str])]`
 Validate a workflow file.

Args:
 workflow_path: Path to workflow.json

Returns:
 (valid: bool, errors: List[str])

- `validate_schema_static(workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Static wrapper for validate_schema.
- `validate_model_config_static(model_config: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Static wrapper for validate_model_config.
- `validate_providers_static(workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Static wrapper for validate_providers.
- `validate_complete_static(workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
 Static wrapper for validate_complete.
- `validate_file_static(workflow_path: str) -> Tuple[(bool, list[str])]`
 Static wrapper for file validation.

## Class Index

### hillstar-orchestrator.config.config

- [HillstarConfig](#hillstar-orchestrator-config-config-hillstarconfig)

### hillstar-orchestrator.config.model_selector

- [ModelSelector](#hillstar-orchestrator-config-model_selector-modelselector)

### hillstar-orchestrator.config.provider_registry

- [ProviderRegistry](#hillstar-orchestrator-config-provider_registry-providerregistry)

### hillstar-orchestrator.config.setup_wizard

- [SetupWizard](#hillstar-orchestrator-config-setup_wizard-setupwizard)

### hillstar-orchestrator.docs.doc_generator

- [ASTAnalyzer](#hillstar-orchestrator-docs-doc_generator-astanalyzer)
- [CrossReferenceBuilder](#hillstar-orchestrator-docs-doc_generator-crossreferencebuilder)
- [DocClass](#hillstar-orchestrator-docs-doc_generator-docclass)
- [DocFunction](#hillstar-orchestrator-docs-doc_generator-docfunction)
- [DocModule](#hillstar-orchestrator-docs-doc_generator-docmodule)
- [DocParameter](#hillstar-orchestrator-docs-doc_generator-docparameter)
- [DocumentationGenerator](#hillstar-orchestrator-docs-doc_generator-documentationgenerator)

### hillstar-orchestrator.execution.checkpoint

- [CheckpointManager](#hillstar-orchestrator-execution-checkpoint-checkpointmanager)

### hillstar-orchestrator.execution.config_validator

- [ConfigValidator](#hillstar-orchestrator-execution-config_validator-configvalidator)

### hillstar-orchestrator.execution.cost_manager

- [CostManager](#hillstar-orchestrator-execution-cost_manager-costmanager)

### hillstar-orchestrator.execution.graph

- [WorkflowGraph](#hillstar-orchestrator-execution-graph-workflowgraph)

### hillstar-orchestrator.execution.model_selector

- [ModelFactory](#hillstar-orchestrator-execution-model_selector-modelfactory)

### hillstar-orchestrator.execution.node_executor

- [NodeExecutor](#hillstar-orchestrator-execution-node_executor-nodeexecutor)

### hillstar-orchestrator.execution.observability

- [ExecutionObserver](#hillstar-orchestrator-execution-observability-executionobserver)
- [TqdmFileWrapper](#hillstar-orchestrator-execution-observability-tqdmfilewrapper)

### hillstar-orchestrator.execution.runner

- [WorkflowRunner](#hillstar-orchestrator-execution-runner-workflowrunner)

### hillstar-orchestrator.execution.trace

- [TraceLogger](#hillstar-orchestrator-execution-trace-tracelogger)

### hillstar-orchestrator.governance.compliance

- [ComplianceEnforcer](#hillstar-orchestrator-governance-compliance-complianceenforcer)
- [ComplianceError](#hillstar-orchestrator-governance-compliance-complianceerror)

### hillstar-orchestrator.governance.enforcer

- [GovernanceEnforcer](#hillstar-orchestrator-governance-enforcer-governanceenforcer)

### hillstar-orchestrator.governance.hooks

- [HookManager](#hillstar-orchestrator-governance-hooks-hookmanager)

### hillstar-orchestrator.governance.policy

- [GovernancePolicy](#hillstar-orchestrator-governance-policy-governancepolicy)

### hillstar-orchestrator.mcp-server.anthropic_mcp_server

- [AnthropicMCPServer](#hillstar-orchestrator-mcp-server-anthropic_mcp_server-anthropicmcpserver)

### hillstar-orchestrator.mcp-server.base_mcp_server

- [BaseMCPServer](#hillstar-orchestrator-mcp-server-base_mcp_server-basemcpserver)

### hillstar-orchestrator.mcp-server.claude_ollama_bridge_server

- [MinimaxMCPServer](#hillstar-orchestrator-mcp-server-claude_ollama_bridge_server-minimaxmcpserver)

### hillstar-orchestrator.mcp-server.devstral_local_mcp_server

- [DevstralLocalMCPServer](#hillstar-orchestrator-mcp-server-devstral_local_mcp_server-devstrallocalmcpserver)

### hillstar-orchestrator.mcp-server.file_operations_mcp_server

- [FileOperationsMCPServer](#hillstar-orchestrator-mcp-server-file_operations_mcp_server-fileoperationsmcpserver)

### hillstar-orchestrator.mcp-server.google_ai_studio_mcp_server

- [GoogleAIStudioMCPServer](#hillstar-orchestrator-mcp-server-google_ai_studio_mcp_server-googleaistudiomcpserver)

### hillstar-orchestrator.mcp-server.mistral_mcp_server

- [MistralMCPServer](#hillstar-orchestrator-mcp-server-mistral_mcp_server-mistralmcpserver)

### hillstar-orchestrator.mcp-server.ollama_mcp_server

- [OllamaMCPServer](#hillstar-orchestrator-mcp-server-ollama_mcp_server-ollamamcpserver)

### hillstar-orchestrator.mcp-server.openai_mcp_server

- [OpenAIMCPServer](#hillstar-orchestrator-mcp-server-openai_mcp_server-openaimcpserver)

### hillstar-orchestrator.mcp-server.secure_logger

- [SecureLogger](#hillstar-orchestrator-mcp-server-secure_logger-securelogger)

### hillstar-orchestrator.models.anthropic_mcp_model

- [AnthropicMCPModel](#hillstar-orchestrator-models-anthropic_mcp_model-anthropicmcpmodel)

### hillstar-orchestrator.models.anthropic_model

- [AnthropicModel](#hillstar-orchestrator-models-anthropic_model-anthropicmodel)

### hillstar-orchestrator.models.anthropic_ollama_api_model

- [AnthropicOllamaAPIModel](#hillstar-orchestrator-models-anthropic_ollama_api_model-anthropicollamaapimodel)

### hillstar-orchestrator.models.devstral_local_model

- [DevstralLocalModel](#hillstar-orchestrator-models-devstral_local_model-devstrallocalmodel)

### hillstar-orchestrator.models.mcp_model

- [MCPModel](#hillstar-orchestrator-models-mcp_model-mcpmodel)

### hillstar-orchestrator.models.mistral_api_model

- [MistralAPIModel](#hillstar-orchestrator-models-mistral_api_model-mistralapimodel)

### hillstar-orchestrator.models.mistral_mcp_model

- [MistralMCPModel](#hillstar-orchestrator-models-mistral_mcp_model-mistralmcpmodel)

### hillstar-orchestrator.models.ollama_mcp_model

- [OllamaMCPModel](#hillstar-orchestrator-models-ollama_mcp_model-ollamamcpmodel)

### hillstar-orchestrator.models.openai_mcp_model

- [OpenAIMCPModel](#hillstar-orchestrator-models-openai_mcp_model-openaimcpmodel)

### hillstar-orchestrator.utils.credential_redactor

- [CredentialRedactor](#hillstar-orchestrator-utils-credential_redactor-credentialredactor)

### hillstar-orchestrator.utils.exceptions

- [BudgetExceededError](#hillstar-orchestrator-utils-exceptions-budgetexceedederror)
- [ConfigurationError](#hillstar-orchestrator-utils-exceptions-configurationerror)
- [HillstarException](#hillstar-orchestrator-utils-exceptions-hillstarexception)
- [ModelSelectionError](#hillstar-orchestrator-utils-exceptions-modelselectionerror)

### hillstar-orchestrator.utils.json_output_viewer

- [JSONOutputViewer](#hillstar-orchestrator-utils-json_output_viewer-jsonoutputviewer)

### hillstar-orchestrator.utils.report

- [ReportGenerator](#hillstar-orchestrator-utils-report-reportgenerator)

### hillstar-orchestrator.workflows.auto_discover

- [AutoDiscover](#hillstar-orchestrator-workflows-auto_discover-autodiscover)

### hillstar-orchestrator.workflows.discovery

- [WorkflowDiscovery](#hillstar-orchestrator-workflows-discovery-workflowdiscovery)

### hillstar-orchestrator.workflows.model_presets

- [ModelPresets](#hillstar-orchestrator-workflows-model_presets-modelpresets)
- [PresetResolver](#hillstar-orchestrator-workflows-model_presets-presetresolver)

### hillstar-orchestrator.workflows.validator

- [WorkflowValidator](#hillstar-orchestrator-workflows-validator-workflowvalidator)

## Function Index

### hillstar-orchestrator.cli

- `cmd_discover()`
- `cmd_enforce()`
- `cmd_execute()`
- `cmd_execute_node()`
- `cmd_mode()`
- `cmd_presets()`
- `cmd_validate()`
- `cmd_wizard()`

### hillstar-orchestrator.config.provider_registry

- `get_registry()`
- `reset_registry()`

### hillstar-orchestrator.dev.testing.openai_token_diagnostic

- `analyze_tokens()`
- `load_auth_json()`

### hillstar-orchestrator.docs.doc_generator

- `generate_user_manual()`

### hillstar-orchestrator.governance.compliance

- `verify_hillstar_compliance()`

### hillstar-orchestrator.governance.project_init

- `initialize_project_structure()`

### hillstar-orchestrator.mcp-server.secure_logger

- `get_logger()`
- `setup_secure_logging()`

### hillstar-orchestrator.utils.credential_redactor

- `contains_credentials()`
- `redact()`

### hillstar-orchestrator.utils.json_output_viewer

- `main()`

### hillstar-orchestrator.utils.report

- `generate_post_execution_report()`
- `generate_pre_execution_report()`

### hillstar-orchestrator.workflows.model_presets

- `build_provider_tiers()`
- `derive_tier_for_model()`
- `parse_and_update_registry()`
- `parse_model_reference()`
- `parse_price_field()`

## Module Dependencies

---

*Generated with AST-based documentation generator*
*Last Updated: 2026*
