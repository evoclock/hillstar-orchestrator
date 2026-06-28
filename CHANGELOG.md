# Changelog

All notable changes to Hillstar are documented in this file.

## 1.1.0 (2026-06-28)

### Added

- `agent-scan` CLI command: static security scanning of MCP server configs and agent skill files for hardcoded secrets, shell injection, dangerous launch flags, unencrypted endpoints, and prompt-injection and data-exfiltration patterns. Findings are graded info/low/medium/high/critical; the command exits non-zero on any high or critical finding.
- Ollama HTTP API provider (`ollama`) for calling Ollama directly over its HTTP endpoint in addition to the MCP path.
- Jan-Code 4B local provider (`jan_code`) via llama.cpp (OpenAI-compatible API on port 8081).

### Changed

- Relicensed from Apache-2.0 to AGPLv3 with Section 7(b) attribution terms.
- Documentation: documented the agent-scan command, the new local providers, and the provider retry/backoff policy across the README, User Manual, Setup Guide, and Provider Model Reference.
- The `tests/` package is no longer bundled in the wheel (unnecessary at runtime, and it had carried absolute developer paths into the 1.0.0 artifact).

### Fixed

- `scripts/check_licences.py` now scopes its scan to declared runtime dependencies and normalises non-standard licence strings (SPDX expressions, PEP 639 License-Expression, and classifier fallback).
- README documentation links now use absolute URLs so they resolve on PyPI.
- Removed hardcoded absolute developer paths from the docs generator, the MCP-server test script, and the integration/e2e tests. The docs generator and e2e test now derive the repository root from their own location; the integration tests skip the external corpus unless `HILLSTAR_IT_FIXTURE_ROOT` points to a local checkout.

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
