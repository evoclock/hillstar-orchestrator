# Hillstar API Reference & User Manual

![Hillstar Logo](../assets/icons/Hillstar_icon_small.png)

| | |
|---|---|
| **Package** | hillstar-orchestrator |
| **Version** | 1.0.0 |
| **Description** | A security and reproducibility-first workflow orchestration tool |
| **Author** | Julen Gamboa |
| **License** | Apache-2.0 |
| **Repository** | <https://github.com/evoclock/agentic-orchestrator> |
| **Python** | >=3.10 |

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
├── config/       - Configuration management
├── execution/    - Workflow execution engine
├── governance/   - Compliance and policy enforcement
├── models/       - LLM provider implementations
├── utils/        - Utilities (logging, tracing, redaction)
├── workflows/    - Workflow discovery and validation
└── cli.py        - Command-line interface
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

### MCP Servers

- `hillstar-orchestrator.mcp-server.anthropic_mcp_server`
- `hillstar-orchestrator.mcp-server.base_mcp_server`
- `hillstar-orchestrator.mcp-server.claude_ollama_bridge_server`
- `hillstar-orchestrator.mcp-server.devstral_local_mcp_server`
- `hillstar-orchestrator.mcp-server.file_operations_mcp_server`
- `hillstar-orchestrator.mcp-server.google_ai_studio_mcp_server`
- `hillstar-orchestrator.mcp-server.mistral_mcp_server`
- `hillstar-orchestrator.mcp-server.ollama_mcp_server`
- `hillstar-orchestrator.mcp-server.openai_mcp_server`
- `hillstar-orchestrator.mcp-server.secure_logger`

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

### Core

#### Module: `hillstar-orchestrator (package)`

Hillstar Orchestrator v1.0.0.

---

#### Module: `hillstar-orchestrator.cli`

Command-line interface for workflow orchestration.

##### cmd_discover

```python
cmd_discover(args)
```

Find workflows in a directory.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### cmd_validate

```python
cmd_validate(args)
```

Validate a workflow.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### cmd_execute

```python
cmd_execute(args)
```

Execute a workflow.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### cmd_presets

```python
cmd_presets(args)
```

List available presets.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### cmd_enforce

```python
cmd_enforce(args)
```

Governance enforcement commands.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### cmd_wizard

```python
cmd_wizard(args)
```

Run setup wizard.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### cmd_mode

```python
cmd_mode(args)
```

Set development mode for development commits.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `args` | - | - | - |

##### main

```python
main()
```

Main CLI entry point.

---

### Configuration & Provider Registry

#### Module: `hillstar-orchestrator.config (package)`

Configuration & Setup Layer for Hillstar Orchestrator.

---

#### Module: `hillstar-orchestrator.config.config`

Unified configuration management for Hillstar.

##### class HillstarConfig

Unified configuration management for Hillstar.

**Methods:**

- `set_provider_key(self, provider: str, api_key: str) -> None`
  Store API key for a provider.

- `get_provider_key(self, provider: str) -> Optional[str]`
  Retrieve API key for a provider.

- `list_configured_providers(self) -> list[str]`
  List providers that have API keys configured.

- `list_missing_providers(self, all_providers: Optional[list[str]] = None) -> list[str]`
  List providers not yet configured.

- `validate_key(self, provider: str, api_key: str) -> bool`
  Validate that an API key is non-empty and reasonably formatted.

- `save_config(self) -> None`
  Write configuration to ~/.hillstar/provider_registry.json.

- `load_config(self) -> None`
  Load configuration from ~/.hillstar/provider_registry.json.

- `get_merged_registry(self) -> ProviderRegistry`
  Get the complete registry with user overrides applied.

- `validate_provider_config(self, provider: str, config: dict[(str, Any)]) -> list[str]`
  Validate provider configuration against registry.

- `check_compliance(self, provider: str, config: dict[(str, Any)]) -> tuple[(bool, list[str])]`
  Check compliance requirements for a provider.

- `get_provider_info(self, provider: str) -> Optional[dict[(str, Any)]]`
  Get full provider configuration from registry.

- `list_available_providers(self) -> list[str]`
  List all available providers from registry.

- `list_available_models(self, provider: str) -> list[str]`
  List all available models for a provider.

- `merge_configs(self, user_config: dict[(str, Any)], workflow_config: dict[(str, Any)]) -> dict[(str, Any)]`
  Merge user configuration with workflow configuration.

**Used in:** `hillstar-orchestrator.config.__init__`

---

#### Module: `hillstar-orchestrator.config.model_selector`

Smart Model Selection: Cost-optimized model selection based on task complexity.

##### class ModelSelector

Cost-optimized model selection based on task complexity.

**Methods:**

- `select(task_complexity: str = 'moderate', provider_preference: Optional[str] = None) -> Tuple[(str, str)]`
  Select model based on task complexity and preferences.

- `select_new(task_complexity: str = 'moderate', provider_preference: Optional[str] = None) -> Tuple[(str, str)]`
  NEW: Select model based on task complexity using registry queries.

- `get_temperature() -> float`
  Get default temperature (minimizes hallucination).

**Used in:** `hillstar-orchestrator.config.__init__`

---

#### Module: `hillstar-orchestrator.config.provider_registry`

Provider Registry: Central registry for LLM providers, models, and compliance rules.

##### class ProviderRegistry

Load and query the provider registry with fallback to user overrides.

**Constructor:**

```python
__init__(self, custom_registry_path: Optional[str] = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `custom_registry_path` | `Optional[str]` | `None` | Optional path to a custom registry file. If provided, this takes precedence over both default and user override. |

**Properties:**

- `version` -> `str`
  Get registry version.

- `last_updated` -> `str`
  Get last update timestamp.

**Methods:**

- `list_providers(self, provider_type: Optional[str] = None) -> List[str]`
  List available providers, optionally filtered by type.

- `get_provider(self, provider_name: str) -> Optional[Dict[(str, Any)]]`
  Get full provider configuration.

- `get_provider_compliance(self, provider_name: str) -> Optional[Dict[(str, Any)]]`
  Get compliance rules for a provider.

- `get_model(self, provider_name: str, model_id: str) -> Optional[Dict[(str, Any)]]`
  Get model configuration.

- `find_models(self, capabilities: Optional[List[str]] = None, max_tier: Optional[str] = None, provider_type: Optional[str] = None, require_ollama: Optional[bool] = None) -> List[Dict[(str, Any)]]`
  Find models matching criteria.

- `get_cheapest_model(self, capabilities: Optional[List[str]] = None, provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
  Get the cheapest model matching criteria, respecting provider preference.

- `estimate_cost(self, provider_name: str, model_id: str, input_tokens: int, output_tokens: int) -> float`
  Estimate cost for a model call.

- `get_fallback_chain(self, complexity: str, provider_preference: Optional[List[str]] = None) -> List[str]`
  Get provider fallback chain for a complexity level.

- `is_usage_compliant(self, provider_name: str, use_case: str) -> Tuple[(bool, str)]`
  Check if a use case is compliant for a provider.

- `get_model_sampling_params(self, provider_name: str, model_id: str) -> Dict[(str, Any)]`
  Get default sampling parameters for a model.

- `get_all_models_flat(self) -> Dict[(Tuple[(str, str)], Dict[(str, Any)])]`
  Get a flat dictionary of all (provider, model_id) -> model_config.

- `describe(self) -> str`
  Get a human-readable description of the registry.

**Used in:** `hillstar-orchestrator.config.__init__`, `hillstar-orchestrator.config.config`

##### get_registry

```python
get_registry() -> 'ProviderRegistry'
```

Get the global registry instance.

**Returns:**

`'ProviderRegistry'`

**Used in:** `hillstar-orchestrator.config.__init__`

##### reset_registry

```python
reset_registry() -> None
```

Reset the global registry instance (useful for testing).

**Returns:**

`None`

**Used in:** `hillstar-orchestrator.config.__init__`

---

#### Module: `hillstar-orchestrator.config.setup_wizard`

Interactive setup wizard for Hillstar provider configuration.

##### class SetupWizard

Interactive wizard for Hillstar provider configuration with keyring-based credential storage.

**Methods:**

- `run(self) -> None`
  Run the setup wizard.

**Used in:** `hillstar-orchestrator.cli`, `hillstar-orchestrator.config.__init__`

##### main

```python
main()
```

Entry point for setup wizard.

---

### Workflow Execution

#### Module: `hillstar-orchestrator.execution (package)`

Execution Engine for Hillstar Orchestrator.

---

#### Module: `hillstar-orchestrator.execution.checkpoint`

Checkpoint Manager: Save and restore workflow state for replay and recovery.

##### class CheckpointManager

Manage workflow checkpoints for replay and recovery.

**Constructor:**

```python
__init__(self, output_dir: str)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | `str` | - | Directory to store checkpoints |

**Methods:**

- `create(self, node_id: str, state: Dict[(str, Any)]) -> str`
  Create a checkpoint after node execution.

- `list_checkpoints(self) -> Dict[(str, str)]`
  List all available checkpoints.

- `load(self, checkpoint_file: str) -> Dict[(str, Any)]`
  Load a checkpoint.

- `get_latest_checkpoint(self, node_id: Optional[str] = None) -> Optional[str]`
  Get most recent checkpoint.

**Used in:** `hillstar-orchestrator.execution.__init__`

---

#### Module: `hillstar-orchestrator.execution.config_validator`

Config Validator: Validate model configuration, load environment files, and manage API key retrieval.

##### class ConfigValidator

Validate model configuration and manage API key retrieval.

**Constructor:**

```python
__init__(self, model_config: dict, graph: WorkflowGraph, trace_logger: TraceLogger)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_config` | `dict` | - | Model configuration dict to validate |
| `graph` | `WorkflowGraph` | - | WorkflowGraph instance for accessing workflow schema |
| `trace_logger` | `TraceLogger` | - | TraceLogger instance for logging warnings |

**Methods:**

- `load_env_file() -> None`
  Load .env file from repo root to ensure API keys are available.

- `validate_model_config(self) -> None`
  Validate model configuration for coherence.

- `get_api_key_for_provider(self, provider: str) -> Optional[str]`
  Get API key for provider from config file or environment.

---

#### Module: `hillstar-orchestrator.execution.cost_manager`

Cost Manager: Handle cost estimation, budget checking, and cost tracking for workflow execution.

##### class CostManager

Manage cost estimation, budget enforcement, and cost tracking for models.

**Constructor:**

```python
__init__(self, model_config: dict)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_config` | `dict` | - | Model configuration dict with budget info |

**Methods:**

- `estimate_cost(self, provider: str, model_name: str, input_tokens: int, output_tokens: int) -> float`
  Estimate cost of a model call using provider_registry pricing.

- `check_budget(self, estimated_cost: float, node_id: str) -> None`
  Check if cost would exceed budget limits.

- `record_cost(self, node_id: str, cost: float) -> None`
  Record actual cost for a node.

---

#### Module: `hillstar-orchestrator.execution.graph`

Graph Execution Engine: DAG-based workflow runner with checkpointing.

##### class WorkflowGraph

Directed Acyclic Graph (DAG) workflow executor.

**Constructor:**

```python
__init__(self, workflow_json: Dict[(str, Any)])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_json` | `Dict[(str, Any)]` | - | Workflow definition (nodes + edges) |

**Methods:**

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

**Used in:** `hillstar-orchestrator.execution.__init__`

---

#### Module: `hillstar-orchestrator.execution.model_selector`

Model Factory: Manage model instantiation, caching, and provider selection logic for execution.

##### class ModelFactory

Factory for creating and caching model instances with provider resolution.

**Constructor:**

```python
__init__(self, model_config: dict, trace_logger: TraceLogger, config_validator: ConfigValidator)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_config` | `dict` | - | Model configuration with provider preferences |
| `trace_logger` | `TraceLogger` | - | Logger for provider resolution and events |
| `config_validator` | `ConfigValidator` | - | ConfigValidator for API key retrieval |

**Methods:**

- `select_model(self, node_id: str, node: dict) -> tuple`
  Select model for a node using three-layer priority.

- `resolve_provider_preference(self, provider_preference: list[str]) -> list[str]`
  Resolve provider preference list based on availability checks.

- `provider_is_available(self, provider: str) -> bool`
  Check if a provider appears available based on local tools/endpoints.

- `ollama_available(self) -> bool`
  Check if Ollama is available via CLI or HTTP.

- `get_model(self, provider: str, model_name: str, **kwargs)`
  Get or create model instance with smart selection.

---

#### Module: `hillstar-orchestrator.execution.node_executor`

Node Executor: Execute individual workflow nodes with support for model calls, file operations, and scripting.

##### class NodeExecutor

Execute individual workflow nodes with comprehensive error handling.

**Constructor:**

```python
__init__(self, model_factory: ModelFactory, cost_manager: CostManager, trace_logger: TraceLogger, model_config: dict)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_factory` | `ModelFactory` | - | ModelFactory for model instantiation |
| `cost_manager` | `CostManager` | - | CostManager for cost tracking |
| `trace_logger` | `TraceLogger` | - | TraceLogger for execution logging |
| `model_config` | `dict` | - | Model configuration dict |

**Methods:**

- `execute_node(self, node_id: str, node: dict, inputs: Any) -> dict[(str, Any)]`
  Execute a single node.

---

#### Module: `hillstar-orchestrator.execution.observability`

Comprehensive observability layer for workflow execution with progress tracking, timestamping, PID logging, hashing, and trace generation.

**Constants:**

- `HAS_TQDM` = False

##### class TqdmFileWrapper

Wrapper that captures tqdm output to log files while displaying on terminal.

**Constructor:**

```python
__init__(self, log_file_path: Path, audit_log_file_path: Path)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_file_path` | `Path` | - | Backwards-compat log file location |
| `audit_log_file_path` | `Path` | - | Audit directory log file location |

**Methods:**

- `write(self, text: str)`
  Write text to log files (with ANSI stripped) and original stderr.

- `flush(self)`
  Flush the original stderr.

##### class ExecutionObserver

Real-time monitoring and logging of workflow execution.

**Constructor:**

```python
__init__(self, workflow_id: str, output_dir: str, total_nodes: int, use_tqdm: bool = True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_id` | `str` | - | Workflow identifier |
| `output_dir` | `str` | - | Base output directory |
| `total_nodes` | `int` | - | Total nodes in workflow |
| `use_tqdm` | `bool` | `True` | Use tqdm progress bars |

**Methods:**

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

**Used in:** `hillstar-orchestrator.execution.__init__`

---

#### Module: `hillstar-orchestrator.execution.runner`

Workflow Runner: Main orchestration engine with dependency injection.

##### class WorkflowRunner

Execute research workflows with full auditability and smart model selection.

**Constructor:**

```python
__init__(self, workflow_path: str, output_dir: str = './.hillstar')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_path` | `str` | - | Path to workflow.json file |
| `output_dir` | `str` | `'./.hillstar'` | Directory for traces and checkpoints |

**Methods:**

- `execute(self, resume_from: Optional[str] = None) -> dict[(str, Any)]`
  Execute the workflow, optionally resuming from a checkpoint.

**Used in:** `hillstar-orchestrator.cli`, `hillstar-orchestrator.execution.__init__`

---

#### Module: `hillstar-orchestrator.execution.trace`

Trace Logger: Comprehensive audit trail for workflow execution.

##### class TraceLogger

Log all workflow executions for auditability and reproducibility.

**Constructor:**

```python
__init__(self, output_dir: str)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | `str` | - | Directory to store trace files (will use output_dir/traces/) |

**Methods:**

- `log(self, event: Dict[(str, Any)]) -> None`
  Log a single event.

- `finalize(self) -> str`
  Finalize trace and return file path.

- `get_events(self) -> List[Dict]`
  Get all logged events.

- `get_cost_summary(self) -> Dict[(str, Any)]`
  Extract cost summary from logged events.

**Used in:** `hillstar-orchestrator.execution.__init__`

---

### Compliance & Governance

#### Module: `hillstar-orchestrator.governance (package)`

Governance module: Enforce workflow-driven development by gating git commits behind verified Hillstar workflow executions.

---

#### Module: `hillstar-orchestrator.governance.compliance`

Compliance enforcement module for Hillstar.

##### class ComplianceError

Extends: `Exception`

Raised when compliance violations are detected.

##### class ComplianceEnforcer

Enforce Hillstar's compliance architecture.

**Methods:**

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

##### verify_hillstar_compliance

```python
verify_hillstar_compliance() -> None
```

Verify Hillstar compliance at import time.

**Returns:**

`None`

**Used in:** `hillstar-orchestrator.governance.__init__`

---

#### Module: `hillstar-orchestrator.governance.enforcer`

Core governance enforcement: validate that a Hillstar workflow was executed before allowing a git commit to proceed.

**Constants:**

- `COMMIT_READY_FILE` = 'commit_ready.json'

##### class GovernanceEnforcer

Enforce workflow-driven development before git commits.

**Constructor:**

```python
__init__(self, hillstar_dir: str = '.hillstar', policy: GovernancePolicy | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hillstar_dir` | `str` | `'.hillstar'` | - |
| `policy` | `GovernancePolicy \| None` | `None` | - |

**Methods:**

- `check(self, dev_mode: bool = False) -> tuple[(bool, str)]`
  Check whether the current state is compliant for a git commit.

- `write_marker(self, workflow_id: str, workflow_file: str, summary: str = '') -> None`
  Write commit_ready marker after successful workflow execution.

- `clear_marker(self) -> None`
  Clear the commit_ready marker (e.g. after commit completes).

- `status(self) -> dict`
  Return full status dictionary for display.

**Used in:** `hillstar-orchestrator.governance.__init__`

---

#### Module: `hillstar-orchestrator.governance.hooks`

Git hook management: install, remove, and verify pre-commit hooks that enforce Hillstar workflow execution before allowing commits.

**Constants:**

- `PRE_COMMIT_TEMPLATE` = '#!/usr/bin/env bash\n# Hillstar governance pre-commit hook\n# Auto-installed by: hillstar enforce install\n# DO NOT EDIT — managed by Hillstar governance module\n\nset -euo pipefail\n\n# Check if development mode is active\nDEV_MODE_FLAG=""\nif [[ "${HILLSTAR_DEV_MODE:-0}" == "1" ]]; then\n\tDEV_MODE_FLAG="--dev"\nfi\n\n# Allow bypass with env var\nif [[ "${HILLSTAR_FORCE_COMMIT:-0}" == "1" ]]; then\n\techo "[hillstar] Force commit override active. Skipping governance check."\n\texit 0\nfi\n\n# Check if hillstar is available\nif ! command -v hillstar &> /dev/null; then\n\techo "[hillstar] WARNING: hillstar not found on PATH, skipping governance check."\n\texit 0\nfi\n\n# Run governance check (with --dev flag if HILLSTAR_DEV_MODE=1)\necho "[hillstar] Checking workflow execution compliance..."\nif hillstar enforce check $DEV_MODE_FLAG; then\n\techo "[hillstar] Governance check passed."\n\texit 0\nelse\n\techo ""\n\techo "[hillstar] Commit blocked: no recent Hillstar workflow execution found."\n\techo "[hillstar] Run: hillstar execute <workflow.json>"\n\techo "[hillstar] Or use development mode: HILLSTAR_DEV_MODE=1 git commit ..."\n\texit 1\nfi\n'

##### class HookManager

Manage git hooks for Hillstar governance enforcement.

**Constructor:**

```python
__init__(self, project_dir: str = '.')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_dir` | `str` | `'.'` | - |

**Methods:**

- `is_git_repo(self) -> bool`
  Check if project_dir is a git repository.

- `is_installed(self) -> bool`
  Check if the Hillstar pre-commit hook is installed.

- `install(self, force: bool = False) -> tuple[(bool, str)]`
  Install the pre-commit hook.

- `uninstall(self) -> tuple[(bool, str)]`
  Remove the Hillstar pre-commit hook.

- `status(self) -> dict`
  Return hook installation status.

**Used in:** `hillstar-orchestrator.governance.__init__`

---

#### Module: `hillstar-orchestrator.governance.policy`

Governance policy definitions: what constitutes a valid workflow execution for the purpose of gating git commits.

##### class GovernancePolicy

Policy configuration for workflow enforcement.

**Methods:**

- `load(cls, hillstar_dir: str) -> 'GovernancePolicy'`
  Load policy from .hillstar/governance_policy.json, or return defaults.

- `save(self, hillstar_dir: str) -> None`
  Persist policy to .hillstar/governance_policy.json.

**Used in:** `hillstar-orchestrator.governance.__init__`

---

#### Module: `hillstar-orchestrator.governance.project_init`

Initialize Hillstar project structure with recommended directory layout.

##### initialize_project_structure

```python
initialize_project_structure(project_path: Optional[str] = None) -> dict
```

Initialize recommended directory structure for Hillstar projects.

Creates:

- .hillstar/ with subdirectories (traces, logs, audit, checkpoints, data_stores)
- workflows/ with subdirectories (core, infrastructure)

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_path` | `Optional[str]` | `None` | Project root directory (defaults to current directory) |

**Returns:**

`dict` - Dictionary with created directories and initialization status

---

### MCP Servers

#### Module: `hillstar-orchestrator.mcp-server.anthropic_mcp_server`

MCP Server: Anthropic Claude Models

##### class AnthropicMCPServer

Extends: `BaseMCPServer`

Anthropic Claude models via official SDK.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute task via Anthropic API.

##### main

```python
main()
```

---

#### Module: `hillstar-orchestrator.mcp-server.base_mcp_server`

MCP Server: Base Class for All Providers

##### class BaseMCPServer

Base MCP server - all providers inherit from this.

**Constructor:**

```python
__init__(self, provider_name: str)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider_name` | `str` | - | - |

**Methods:**

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

---

#### Module: `hillstar-orchestrator.mcp-server.claude_ollama_bridge_server`

MCP Server: Fallback to Ollama Cloud Models via claude-ollama CLI

##### class MinimaxMCPServer

MCP Server wrapper for Ollama cloud models via claude-ollama CLI.

**Methods:**

- `initialize(self) -> Dict[(str, Any)]`
  Initialize the MCP server.

- `list_tools(self) -> Dict[(str, Any)]`
  List available tools.

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute a tool (task dispatch to minimax).

- `handle_request(self, request: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Route incoming MCP requests.

##### main

```python
main()
```

Main MCP server loop (stdio protocol).

---

#### Module: `hillstar-orchestrator.mcp-server.devstral_local_mcp_server`

MCP Server: Devstral Local (llama.cpp HTTP Server)

##### class DevstralLocalMCPServer

Extends: `BaseMCPServer`

Devstral Small 2 24B via llama.cpp HTTP server.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute task via devstral_server.sh HTTP API.

##### main

```python
main()
```

---

#### Module: `hillstar-orchestrator.mcp-server.file_operations_mcp_server`

MCP Server: File Operations (write_file, update_file, create_directory)

##### class FileOperationsMCPServer

Extends: `BaseMCPServer`

File operations server - allows agents to write/update files safely.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute file operation.

---

#### Module: `hillstar-orchestrator.mcp-server.google_ai_studio_mcp_server`

MCP Server: Google AI Studio (Gemini Models)

##### class GoogleAIStudioMCPServer

Extends: `BaseMCPServer`

Google Gemini models via official SDK.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute task via Google Gemini API.

##### main

```python
main()
```

---

#### Module: `hillstar-orchestrator.mcp-server.mistral_mcp_server`

MCP Server: Mistral AI Models

##### class MistralMCPServer

Extends: `BaseMCPServer`

Mistral AI models via official SDK.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute task via Mistral API.

##### main

```python
main()
```

---

#### Module: `hillstar-orchestrator.mcp-server.ollama_mcp_server`

MCP Server: Ollama Local Models

##### class OllamaMCPServer

Extends: `BaseMCPServer`

Ollama local models via HTTP API.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute task via Ollama HTTP API.

##### main

```python
main()
```

---

#### Module: `hillstar-orchestrator.mcp-server.openai_mcp_server`

MCP Server: OpenAI GPT Models with Dual Authentication

##### class OpenAIMCPServer

Extends: `BaseMCPServer`

OpenAI GPT models via official SDK or Codex CLI wrapper.

**Methods:**

- `call_tool(self, tool_name: str, arguments: Dict[(str, Any)]) -> Dict[(str, Any)]`
  Execute task via OpenAI API (api_key mode) or codex CLI (subscription mode).

##### main

```python
main()
```

---

#### Module: `hillstar-orchestrator.mcp-server.secure_logger`

Secure logging module for MCP servers.

##### class SecureLogger

Extends: `logging.Logger`

Custom logger that prevents accidental sensitive data logging.

**Constructor:**

```python
__init__(self, name)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | - | - | - |

**Methods:**

- `audit(self, message, *args, **kwargs)`
  Log safe audit information.

- `debug_redacted(self, label, *redacted_values, **kwargs)`
  Log debug info with redacted sensitive values.

- `memory_only(self, label, value)`
  Log to memory ONLY (for debugging during execution).

- `error_safe(self, message, exception = None)`
  Log errors without exposing exception details.

##### setup_secure_logging

```python
setup_secure_logging(log_dir = None, debug = False)
```

Set up secure logging for all MCP servers.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_dir` | - | `None` | Directory for audit logs (default: ~/.hillstar/mcp-logs) |
| `debug` | - | `False` | Enable debug logging (default: False) |

##### get_logger

```python
get_logger(name)
```

Get a secure logger instance.

Usage:
from secure_logger import get_logger
logger = get_logger(**name**)

logger.audit("Task started")
logger.debug_redacted("Response size", len(response), "bytes")
logger.error_safe("API failed", exception)

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | - | - | - |

---

### LLM Model Providers

#### Module: `hillstar-orchestrator.models (package)`

Model Provider Integrations: Support for Anthropic, OpenAI, local models, and more.

---

#### Module: `hillstar-orchestrator.models.anthropic_mcp_model`

Anthropic Claude models via MCP (Model Context Protocol) server.

##### class AnthropicMCPModel

Extends: `MCPModel`

Anthropic Claude models via MCP server.

**Constructor:**

```python
__init__(self, model_name: str, api_key: str | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | - | Claude model identifier |
| `api_key` | `str \| None` | `None` | Optional API key (else uses ANTHROPIC_API_KEY env var) |

**Used in:** `hillstar-orchestrator.models.__init__`

---

#### Module: `hillstar-orchestrator.models.anthropic_model`

Anthropic Claude Model Integration: Call Claude models via API.

##### class AnthropicModel

Interface to Anthropic Claude models.

**Constructor:**

```python
__init__(self, model: str = 'haiku', api_key: str | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `'haiku'` | Model to use. Can be: - Short name: "haiku", "sonnet", "opus" - Full identifier: "claude-haiku-4-5-20251001" |
| `api_key` | `str \| None` | `None` | Explicit API key (else uses ANTHROPIC_API_KEY env var) |

**Methods:**

- `call(self, prompt: str, max_tokens: int = 4096, temperature: float | None = None, system: str | None = None) -> dict[(str, Any)]`
  Call Claude model.

**Used in:** `hillstar-orchestrator.models.__init__`

---

#### Module: `hillstar-orchestrator.models.anthropic_ollama_api_model`

Anthropic models via Ollama's Anthropic-compatible API (Messages API).

##### class AnthropicOllamaAPIModel

Anthropic models via Ollama's Anthropic-compatible API.

**Constructor:**

```python
__init__(self, model_name: str = 'minimax-m2.5:cloud', base_url: str | None = None, api_key: str | None = None, max_retries: int = 2)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | `'minimax-m2.5:cloud'` | Ollama model identifier (local or cloud) |
| `base_url` | `str \| None` | `None` | Ollama endpoint URL (defaults to env var ANTHROPIC_BASE_URL or localhost) |
| `api_key` | `str \| None` | `None` | API key for authentication (defaults to env var ANTHROPIC_AUTH_TOKEN) |
| `max_retries` | `int` | `2` | Number of retries for transient failures |

**Methods:**

- `call(self, prompt: str, **kwargs) -> dict[(str, Any)]`
  Call model via Ollama's Anthropic-compatible API.

**Used in:** `hillstar-orchestrator.models.__init__`

---

#### Module: `hillstar-orchestrator.models.devstral_local_model`

LOCAL DEVSTRAL-SMALL-2 MODEL - OPTIONAL ADVANCED SETUP

##### class DevstralLocalModel

LOCAL Devstral-Small-2 via llama.cpp (OpenAI-compatible API).

**Constructor:**

```python
__init__(self, model_name: str = 'devstral', endpoint: str = 'http://127.0.0.1:8080')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | `'devstral'` | Model identifier (llama.cpp accepts any value) |
| `endpoint` | `str` | `'http://127.0.0.1:8080'` | llama.cpp server endpoint (OpenAI-compatible) |

**Methods:**

- `call(self, prompt: str, max_tokens: int = 2048, temperature: float | None = None, system: str | None = None) -> dict[(str, Any)]`
  Call Devstral via llama.cpp OpenAI-compatible chat completions endpoint.

**Used in:** `hillstar-orchestrator.models.__init__`

---

#### Module: `hillstar-orchestrator.models.mcp_model`

Base class for MCP-based model providers: Handle subprocess lifecycle and JSON-RPC communication.

##### class MCPModel

Base class for MCP-based model providers.

**Constructor:**

```python
__init__(self, provider: str, model_name: str, server_script: str, api_key: str | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `str` | - | Provider name (e.g., "anthropic_mcp") |
| `model_name` | `str` | - | Model identifier (e.g., "claude-opus-4-6") |
| `server_script` | `str` | - | Path to MCP server script (relative to repo root) |
| `api_key` | `str \| None` | `None` | Optional API key (else reads from environment) |

**Methods:**

- `call(self, prompt: str, max_tokens: int = 4096, temperature: float | None = None, system: str | None = None) -> dict[(str, Any)]`
  Execute task via MCP server.

- `__del__(self)`
  Cleanup subprocess on deletion.

**Used in:** `hillstar-orchestrator.models.__init__`, `hillstar-orchestrator.models.anthropic_mcp_model`, `hillstar-orchestrator.models.mistral_mcp_model`, `hillstar-orchestrator.models.ollama_mcp_model`, `hillstar-orchestrator.models.openai_mcp_model`

---

#### Module: `hillstar-orchestrator.models.mistral_api_model`

Mistral AI API integration for orchestration workflows.

##### class MistralAPIModel

Mistral AI API provider with model selector.

**Constructor:**

```python
__init__(self, model: str = 'small', api_key: Optional[str] = None, base_url: str = 'https://api.mistral.ai/v1')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `'small'` | Model to use. Can be: - Short name: "small", "medium", "mini", "code", "devstral" - Full identifier: "mistral-large-2411" |
| `api_key` | `Optional[str]` | `None` | API key (defaults to MISTRAL_API_KEY env var) |
| `base_url` | `str` | `'https://api.mistral.ai/v1'` | API endpoint base URL |

**Methods:**

- `call(self, prompt: str, messages: Optional[List[Dict[(str, str)]]] = None, **kwargs) -> Dict[(str, Any)]`
  Call Mistral API (placeholder - not implemented).

**Used in:** `hillstar-orchestrator.models.__init__`

---

#### Module: `hillstar-orchestrator.models.mistral_mcp_model`

Mistral AI models via MCP (Model Context Protocol) server.

##### class MistralMCPModel

Extends: `MCPModel`

Mistral AI models via MCP server.

**Constructor:**

```python
__init__(self, model_name: str, api_key: str | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | - | Mistral model identifier |
| `api_key` | `str \| None` | `None` | Optional API key (else uses MISTRAL_API_KEY env var) |

---

#### Module: `hillstar-orchestrator.models.ollama_mcp_model`

Ollama (local models) via MCP (Model Context Protocol) server.

##### class OllamaMCPModel

Extends: `MCPModel`

Ollama local models via MCP server.

**Constructor:**

```python
__init__(self, model_name: str)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | - | Ollama model identifier (e.g., "devstral-small-2:24b") |

---

#### Module: `hillstar-orchestrator.models.openai_mcp_model`

OpenAI GPT models via MCP (Model Context Protocol) server.

##### class OpenAIMCPModel

Extends: `MCPModel`

OpenAI GPT models via MCP server with transparent dual authentication.

**Constructor:**

```python
__init__(self, model_name: str, api_key: str | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str` | - | OpenAI model identifier (e.g., "gpt-5.2") |
| `api_key` | `str \| None` | `None` | Optional API key (else reads from OPENAI_API_KEY env var) The MCP server handles authentication automatically: - If OPENAI_CHATGPT_LOGIN_MODE=true: Uses codex exec with subscription tokens - If OPENAI_API_KEY is set: Uses direct OpenAI API with SDK - Falls back in that order No auth resolution is performed here—the MCP server is fully self-contained. |

---

### Utilities

#### Module: `hillstar-orchestrator.utils (package)`

Utilities for Hillstar Orchestrator.

---

#### Module: `hillstar-orchestrator.utils.credential_redactor`

Detect and redact sensitive credentials (API keys, tokens, infrastructure identifiers, PII) from strings, logs, and error messages. Prevents accidental data leakage in output.

##### class CredentialRedactor

Detect and redact sensitive credentials from strings.

**Methods:**

- `redact(text: Optional[str], include_patterns: Optional[list] = None) -> str`
  Redact all detected credentials from text.

- `contains_credentials(text: Optional[str]) -> bool`
  Check if text contains any detected credentials.

- `get_redaction_types(text: str) -> list`
  Identify which credential types are present in text.

**Used in:** `hillstar-orchestrator.utils.__init__`

##### redact

```python
redact(text: Optional[str]) -> str
```

Convenience function to redact credentials from a string.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `Optional[str]` | - | String potentially containing credentials (returns empty string if None) |

**Returns:**

`str` - String with credentials redacted

**Used in:** `hillstar-orchestrator.utils.__init__`

##### contains_credentials

```python
contains_credentials(text: Optional[str]) -> bool
```

Convenience function to check if string contains credentials.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `Optional[str]` | - | String to check (returns False if None) |

**Returns:**

`bool` - True if credentials detected

**Used in:** `hillstar-orchestrator.utils.__init__`

---

#### Module: `hillstar-orchestrator.utils.exceptions`

Custom exceptions for Hillstar Orchestrator.

##### class HillstarException

Extends: `Exception`

Base exception for Hillstar Orchestrator.

##### class BudgetExceededError

Extends: `HillstarException`

Raised when workflow cost exceeds budget limits.

##### class ModelSelectionError

Extends: `HillstarException`

Raised when model selection fails.

##### class ConfigurationError

Extends: `HillstarException`

Raised when workflow configuration is invalid.

##### class ExecutionError

Extends: `HillstarException`

Raised when node execution fails.

---

#### Module: `hillstar-orchestrator.utils.json_output_viewer`

Generic utility to parse, validate, and view JSON output files in full.

##### class JSONOutputViewer

Generic parser and display tool for JSON output files.

**Constructor:**

```python
__init__(self, output_file: Path)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_file` | `Path` | - | - |

**Methods:**

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

##### main

```python
main()
```

CLI entry point.

---

#### Module: `hillstar-orchestrator.utils.report`

Generate pre-execution and post-execution markdown reports for workflows.

##### class ReportGenerator

Generate professional workflow execution reports.

**Constructor:**

```python
__init__(self, workflow_path: str)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_path` | `str` | - | - |

**Methods:**

- `generate_pre_execution_report(self) -> str`
  Generate pre-execution report with estimated costs and metadata.

- `generate_post_execution_report(self, trace_path: str) -> str`
  Generate post-execution report with actual execution metrics.

##### generate_pre_execution_report

```python
generate_pre_execution_report(workflow_path: str) -> str
```

Generate pre-execution report for a workflow.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_path` | `str` | - | Path to workflow JSON file |

**Returns:**

`str` - Markdown string with report

##### generate_post_execution_report

```python
generate_post_execution_report(workflow_path: str, trace_path: str) -> str
```

Generate post-execution report for a workflow.

**Arguments:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workflow_path` | `str` | - | Path to workflow JSON file |
| `trace_path` | `str` | - | Path to trace JSONL file |

**Returns:**

`str` - Markdown string with report including execution metrics

---

### Workflow Discovery & Validation

#### Module: `hillstar-orchestrator.workflows (package)`

Workflows & Templates for Hillstar Orchestrator.

---

#### Module: `hillstar-orchestrator.workflows.auto_discover`

Auto-discovery mechanism to detect Hillstar projects and suggest workflows.

##### class AutoDiscover

Auto-detect Hillstar projects and suggest workflows.

**Methods:**

- `is_hillstar_project(start_dir: str = '.') -> bool`
  Detect if a directory is a Hillstar project.

- `get_project_info(start_dir: str = '.') -> Dict[(str, Any)]`
  Get Hillstar project information.

- `classify_task(task_description: str) -> Dict[(str, float)]`
  Classify task by keywords to infer requirements.

- `get_preset_suggestions(task_scores: Dict[(str, float)]) -> List[Tuple[(str, float)]]`
  Suggest presets based on task classification.

- `suggest_workflows(task_description: str, workflows: List[Dict[(str, Any)]], top_k: int = 3) -> List[Dict[(str, Any)]]`
  Suggest workflows based on task description.

- `get_recommendations(task_description: str, workflows: List[Dict[(str, Any)]]) -> Dict[(str, Any)]`
  Get comprehensive recommendations for a task.

- `format_recommendations(recommendations: Dict[(str, Any)]) -> str`
  Format recommendations as human-readable text.

**Used in:** `hillstar-orchestrator.workflows.__init__`

---

#### Module: `hillstar-orchestrator.workflows.discovery`

Workflow discovery: Find and analyze workflow.json files in project directory.

##### class WorkflowDiscovery

Find and analyze Hillstar workflows in a directory tree.

**Methods:**

- `find_workflows(start_path: str = '.', max_depth: int = 5) -> List[str]`
  Find all workflow.json files in directory tree.

- `get_workflow_info(workflow_path: str) -> Dict[(str, Any)]`
  Extract metadata from a workflow file.

- `get_all_workflow_info(start_path: str = '.', max_depth: int = 5) -> List[Dict[(str, Any)]]`
  Find all workflows and return their metadata.

- `find_in_current_project() -> List[Dict[(str, Any)]]`
  Find all workflows in current project (with .hillstar/ or spec/ indicators).

**Used in:** `hillstar-orchestrator.cli`, `hillstar-orchestrator.workflows.__init__`

---

#### Module: `hillstar-orchestrator.workflows.model_presets`

Model Selection Presets

##### class PresetResolver

Data-driven model resolver that enforces temperature and parameter constraints.

**Constructor:**

```python
__init__(self, preset_name: str, configured_providers: List[str])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `preset_name` | `str` | - | One of cost_saver, balanced, quality_first, premium |
| `configured_providers` | `List[str]` | - | List of provider names in preference order |

**Methods:**

- `resolve(self, complexity: str = 'moderate', use_case: Optional[str] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
  Resolve (preset, complexity) to (provider, model, suggested_parameters).

##### class ModelPresets

Legacy class for backward compatibility.

**Methods:**

- `select(preset_name: str, complexity: str = 'moderate', provider_preference: Optional[List[str]] = None) -> Optional[Tuple[(str, str, Dict[(str, Any)])]]`
  Select model from a preset strategy (legacy).

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

- `get_fallback_chain(preset_name: str, complexity: str, provider_preference: Optional[List[str]] = None) -> List[str]`
  Get provider fallback chain for a preset.

**Used in:** `hillstar-orchestrator.cli`, `hillstar-orchestrator.workflows.__init__`

---

#### Module: `hillstar-orchestrator.workflows.validator`

Workflow validation: Check workflows against schema, registry, and constraints.

##### class WorkflowValidator

Validate Hillstar workflows against schema, registry, and constraints.

**Constructor:**

```python
__init__(self, registry: Optional[ProviderRegistry] = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `registry` | `Optional[ProviderRegistry]` | `None` | - |

**Methods:**

- `load_schema(self) -> dict[(str, Any)]`
  Load the workflow schema (from installed package or dev environment).

- `validate_schema(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
  Validate workflow against JSON schema.

- `validate_model_config(self, model_config: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
  Validate model_config section for coherence.

- `validate_graph_connectivity(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
  Validate workflow graph connectivity (no disconnected components).

- `validate_providers(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
  Validate all referenced providers and models against registry.

- `validate_compliance(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
  Validate compliance requirements for all providers.

- `validate_complete(self, workflow: dict[(str, Any)]) -> Tuple[(bool, list[str])]`
  Run all validations.

- `validate_file(workflow_path: str) -> Tuple[(bool, list[str])]`
  Validate a workflow file.

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

**Used in:** `hillstar-orchestrator.cli`, `hillstar-orchestrator.workflows.__init__`

---

## Class Index

### hillstar-orchestrator.config.config

- [HillstarConfig](#class-hillstarconfig)

### hillstar-orchestrator.config.model_selector

- [ModelSelector](#class-modelselector)

### hillstar-orchestrator.config.provider_registry

- [ProviderRegistry](#class-providerregistry)

### hillstar-orchestrator.config.setup_wizard

- [SetupWizard](#class-setupwizard)

### hillstar-orchestrator.execution.checkpoint

- [CheckpointManager](#class-checkpointmanager)

### hillstar-orchestrator.execution.config_validator

- [ConfigValidator](#class-configvalidator)

### hillstar-orchestrator.execution.cost_manager

- [CostManager](#class-costmanager)

### hillstar-orchestrator.execution.graph

- [WorkflowGraph](#class-workflowgraph)

### hillstar-orchestrator.execution.model_selector

- [ModelFactory](#class-modelfactory)

### hillstar-orchestrator.execution.node_executor

- [NodeExecutor](#class-nodeexecutor)

### hillstar-orchestrator.execution.observability

- [ExecutionObserver](#class-executionobserver)
- [TqdmFileWrapper](#class-tqdmfilewrapper)

### hillstar-orchestrator.execution.runner

- [WorkflowRunner](#class-workflowrunner)

### hillstar-orchestrator.execution.trace

- [TraceLogger](#class-tracelogger)

### hillstar-orchestrator.governance.compliance

- [ComplianceEnforcer](#class-complianceenforcer)
- [ComplianceError](#class-complianceerror)

### hillstar-orchestrator.governance.enforcer

- [GovernanceEnforcer](#class-governanceenforcer)

### hillstar-orchestrator.governance.hooks

- [HookManager](#class-hookmanager)

### hillstar-orchestrator.governance.policy

- [GovernancePolicy](#class-governancepolicy)

### hillstar-orchestrator.mcp-server.anthropic_mcp_server

- [AnthropicMCPServer](#class-anthropicmcpserver)

### hillstar-orchestrator.mcp-server.base_mcp_server

- [BaseMCPServer](#class-basemcpserver)

### hillstar-orchestrator.mcp-server.claude_ollama_bridge_server

- [MinimaxMCPServer](#class-minimaxmcpserver)

### hillstar-orchestrator.mcp-server.devstral_local_mcp_server

- [DevstralLocalMCPServer](#class-devstrallocalmcpserver)

### hillstar-orchestrator.mcp-server.file_operations_mcp_server

- [FileOperationsMCPServer](#class-fileoperationsmcpserver)

### hillstar-orchestrator.mcp-server.google_ai_studio_mcp_server

- [GoogleAIStudioMCPServer](#class-googleaistudiomcpserver)

### hillstar-orchestrator.mcp-server.mistral_mcp_server

- [MistralMCPServer](#class-mistralmcpserver)

### hillstar-orchestrator.mcp-server.ollama_mcp_server

- [OllamaMCPServer](#class-ollamamcpserver)

### hillstar-orchestrator.mcp-server.openai_mcp_server

- [OpenAIMCPServer](#class-openaimcpserver)

### hillstar-orchestrator.mcp-server.secure_logger

- [SecureLogger](#class-securelogger)

### hillstar-orchestrator.models.anthropic_mcp_model

- [AnthropicMCPModel](#class-anthropicmcpmodel)

### hillstar-orchestrator.models.anthropic_model

- [AnthropicModel](#class-anthropicmodel)

### hillstar-orchestrator.models.anthropic_ollama_api_model

- [AnthropicOllamaAPIModel](#class-anthropicollamaapimodel)

### hillstar-orchestrator.models.devstral_local_model

- [DevstralLocalModel](#class-devstrallocalmodel)

### hillstar-orchestrator.models.mcp_model

- [MCPModel](#class-mcpmodel)

### hillstar-orchestrator.models.mistral_api_model

- [MistralAPIModel](#class-mistralapimodel)

### hillstar-orchestrator.models.mistral_mcp_model

- [MistralMCPModel](#class-mistralmcpmodel)

### hillstar-orchestrator.models.ollama_mcp_model

- [OllamaMCPModel](#class-ollamamcpmodel)

### hillstar-orchestrator.models.openai_mcp_model

- [OpenAIMCPModel](#class-openaimcpmodel)

### hillstar-orchestrator.utils.credential_redactor

- [CredentialRedactor](#class-credentialredactor)

### hillstar-orchestrator.utils.exceptions

- [BudgetExceededError](#class-budgetexceedederror)
- [ConfigurationError](#class-configurationerror)
- [ExecutionError](#class-executionerror)
- [HillstarException](#class-hillstarexception)
- [ModelSelectionError](#class-modelselectionerror)

### hillstar-orchestrator.utils.json_output_viewer

- [JSONOutputViewer](#class-jsonoutputviewer)

### hillstar-orchestrator.utils.report

- [ReportGenerator](#class-reportgenerator)

### hillstar-orchestrator.workflows.auto_discover

- [AutoDiscover](#class-autodiscover)

### hillstar-orchestrator.workflows.discovery

- [WorkflowDiscovery](#class-workflowdiscovery)

### hillstar-orchestrator.workflows.model_presets

- [ModelPresets](#class-modelpresets)
- [PresetResolver](#class-presetresolver)

### hillstar-orchestrator.workflows.validator

- [WorkflowValidator](#class-workflowvalidator)

## Function Index

### hillstar-orchestrator.cli

- `cmd_discover()`
- `cmd_enforce()`
- `cmd_execute()`
- `cmd_mode()`
- `cmd_presets()`
- `cmd_validate()`
- `cmd_wizard()`

### hillstar-orchestrator.config.provider_registry

- `get_registry()`
- `reset_registry()`

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

## Module Dependencies

### hillstar-orchestrator.cli

Depends on:

- `.config`
- `.execution`
- `.workflows`

### hillstar-orchestrator.config.\_\_init\_\_

Depends on:

- `.config`
- `.model_selector`
- `.provider_registry`
- `.setup_wizard`

### hillstar-orchestrator.config.config

Depends on:

- `.provider_registry`

### hillstar-orchestrator.execution.\_\_init\_\_

Depends on:

- `.checkpoint`
- `.graph`
- `.observability`
- `.runner`
- `.trace`

### hillstar-orchestrator.governance.\_\_init\_\_

Depends on:

- `.compliance`
- `.enforcer`
- `.hooks`
- `.policy`

### hillstar-orchestrator.models.\_\_init\_\_

Depends on:

- `.anthropic_mcp_model`
- `.anthropic_model`
- `.anthropic_ollama_api_model`
- `.devstral_local_model`
- `.mcp_model`
- `.mistral_api_model`

### hillstar-orchestrator.models.anthropic_mcp_model

Depends on:

- `.mcp_model`

### hillstar-orchestrator.models.mistral_mcp_model

Depends on:

- `.mcp_model`

### hillstar-orchestrator.models.ollama_mcp_model

Depends on:

- `.mcp_model`

### hillstar-orchestrator.models.openai_mcp_model

Depends on:

- `.mcp_model`

### hillstar-orchestrator.utils.\_\_init\_\_

Depends on:

- `.credential_redactor`
- `.exceptions`

### hillstar-orchestrator.workflows.\_\_init\_\_

Depends on:

- `.auto_discover`
- `.discovery`
- `.model_presets`
- `.validator`

---

Generated with AST-based documentation generator.
Last Updated: 2026-02-28
