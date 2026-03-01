# Changelog

All notable changes to Hillstar are documented in this file.

## 1.0.0 (2026-03-01) - Production Release

### Added

#### Core Infrastructure

- Modularized execution system (runner, node_executor, model_selector, cost_manager, config_validator)
- DAG-based workflow graph with topological ordering and edge specifications
- Compliance enforcement (ToS acceptance, audit enablement, restricted use acknowledgment)
- Governance system with git hook integration and execution markers
- Checkpoint persistence for workflow recovery

#### Provider System (MCP Abstraction Layer)

- Multi-provider support: Anthropic (Claude), OpenAI (GPT), Mistral, Google AI Studio, Ollama, Devstral Local
- 7 MCP servers: Anthropic, OpenAI, Mistral, Google AI Studio, Ollama, Devstral Local, Minimax
- Provider registry with user-level, project-level, and workflow-level configuration
- Dynamic model discovery and versioning
- Cost estimation per provider/model
- OpenAI dual authentication (API key + ChatGPT subscription token via codex CLI)
- Setup wizard with keyring auto-discovery for secure credential storage

#### Security & Compliance

- In-flight credential redaction (24 pattern types detected)
- Three-tier API key resolution (config > environment > error)
- Secure error messages that don't leak credentials
- Audit logging and trace file generation
- Governance enforcement with commit markers

#### Workflow Features

- Pre- and post-execution workflow reports (Markdown, Mermaid DAG visualization)
- Model selection system with preset complexity levels
- Budget enforcement and cost tracking
- Auto-discovery of workflow files

#### CLI Tools

- `hillstar discover` - find workflows
- `hillstar validate` - schema validation with compliance checking
- `hillstar execute` - workflow execution with audit trails
- `hillstar diagram` - Mermaid DAG visualization
- `hillstar presets` - list available model presets
- `hillstar config` - manage provider credentials (keyring + env + .env)
- `hillstar report` - generate pre/post-execution reports

#### Testing & Quality

- 1,090 tests (100% pass rate)
- 91% code coverage (10,306 statements)
- Credential redaction validation (27 tests)
- MCP error handling (8 tests)
- E2E workflow validation (Haiku synthesis, local execution, multi-provider mixing)
- MCP connectivity validation (7 servers)

#### Documentation

- User_Manual.md: Complete setup, configuration, and usage guide
- ARCHITECTURE.md: System design and modularization
- PROVIDER_MODEL_REFERENCE.md: Provider registry, capabilities, and costs
- MCP_SERVERS.md: MCP server setup and security
- Sphinx API documentation with furo theme
- GitHub Pages deployment via GitHub Actions
- OpenAI dual-auth setup guides (API key + subscription token)
- CITATION.cff for academic citation

### Architecture

- Single-file workflow definitions (JSON schema)
- Provider-agnostic execution (MCP abstraction)
- Governance by default (compliance, audit, reproducibility)
- Plugin-ready architecture

### Dependencies

- Python 3.10+
- Standard library only for core functionality
- Optional: Ollama for local model execution
- Optional: Sphinx + furo for API documentation

---

## 0.1.0 (2026-02-18) - Initial Development Release

### Added

- Workflow discovery, validation, and execution engine
- DAG-based workflow graph support
- Multi-provider support (Anthropic, OpenAI, Mistral, Google AI Studio, Ollama)
- MCP servers for all major providers
- Credential redaction system
- CLI tools (discover, validate, execute, diagram, presets, config, report)
- 68 unit and integration tests (100% pass rate)
- Setup guide with provider configuration instructions
