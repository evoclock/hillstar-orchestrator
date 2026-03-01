# Hillstar Architecture

## Design Philosophy

Hillstar follows an explicit-over-implicit design philosophy:

- No unrestricted API access
- No magic or hidden behavior
- All decisions are auditable
- Data flows explicitly between stages
- One action per node
- Clear governance at every step

This ensures that in regulated or high-stakes environments, teams can prove exactly what happened, when, and why.

---

## System Architecture

### High-Level Flow

```bash
User: Defines workflow.json
 |
 v
WorkflowRunner
 |
 +---> Load workflow from JSON
 +---> Validate schema and compliance
 +---> Initialize execution environment
 |
 v
WorkflowGraph
 |
 +---> Build DAG from workflow
 +---> Topological sort (execution order)
 +---> Track dependencies
 |
 v
NodeExecutor (for each node in order)
 |
 +---> Determine operation type
 +---> Dispatch to appropriate handler
 +---> Track inputs/outputs
 +---> Record cost
 |
 v
Results and Audit Trail
 |
 +---> Final workflow outputs
 +---> Complete trace log
 +---> Cost breakdown
 +---> Compliance report
```

### Module Breakdown

#### execution/runner.py (Orchestration)
Responsible for:

- Loading and parsing workflow definitions
- Initializing graph, trace logger, and checkpoints
- Instantiating model selector, cost manager, and config validator
- Orchestrating the execution loop
- Writing final results and metadata

Key Methods:

- __init__: Setup environment and load workflow
- execute: Main orchestration loop
- _get_execution_result: Format final output
- _write_step_metadata: Log step details

#### execution/graph.py (DAG Management)
Responsible for:

- Building directed acyclic graph from workflow
- Topological sorting for execution order
- Dependency tracking and validation
- Managing node connections

Key Concepts:

- Node: Single action (model_call, file_read, etc.)
- Edge: Data flow from one node's output to another's input
- Topological Order: Ensures dependencies resolved before execution

#### execution/node_executor.py (Node Dispatch)
Responsible for:

- Executing individual nodes
- Managing provider chains and fallbacks
- Handling different operation types
- Cost tracking for each node
- Error detection and retry logic

Operation Types:

- model_call: LLM inference
- file_read: Read file content
- file_write: Write file
- script_run: Execute shell command
- git_commit: Create git commit

Key Methods:

- execute_node: Main dispatcher
- _execute_model_call: LLM invocation with retries
- _execute_file_read/write: File I/O
- _execute_script_run: Command execution
- _execute_git_commit: Git operations
- _get_provider_chain: Fallback strategy

#### execution/model_selector.py (Provider Selection)
Responsible for:

- Selecting models based on preference
- Resolving provider preferences
- Checking provider availability
- Caching model instances
- Detecting Ollama availability

Key Methods:

- select_model: Model selection logic
- resolve_provider_preference: Provider preference resolution
- provider_is_available: Check provider readiness
- ollama_available: Detect local Ollama
- get_model: Factory with caching

#### execution/cost_manager.py (Cost Tracking)
Responsible for:

- Estimating costs before/after calls
- Tracking cumulative costs
- Per-node cost recording
- Budget enforcement

Key Methods:

- estimate_cost: Calculate cost for model call
- check_budget: Enforce budget limits
- record_cost: Track per-node costs

#### execution/config_validator.py (Configuration)
Responsible for:

- Loading environment files
- Validating model configuration
- Resolving API keys (config > env > error)
- Provider-specific validation

Key Methods:

- load_env_file: Load .env file
- validate_model_config: Validate configuration structure
- get_api_key_for_provider: Three-tier key resolution

#### execution/checkpoint.py (State Management)
Responsible for:

- Saving workflow state at checkpoints
- Resuming from checkpoints
- Recording progress
- State persistence

#### execution/observability.py (Logging and Tracing)
Responsible for:

- Structured logging
- Trace collection
- Audit trail creation
- Performance metrics

#### execution/trace.py (Trace Data)
Responsible for:

- Trace data structures
- Trace collection and aggregation
- Trace output formatting

---

## Data Flow

### Workflow Execution Flow

```bash
Input Workflow (JSON)
 |
 v
Schema Validation
 |
 v
Compliance Check
 |
 v
Build Execution Graph
 |
 v
For each node (topological order):
 |
 +---> Execute node
 +---> Record outputs
 +---> Track costs
 +---> Log to trace
 +---> Check compliance gates
 |
 v
Aggregate Results
 |
 +---> Final outputs
 +---> Cost summary
 +---> Trace log
 +---> Compliance report
```

### Node Execution Flow

```bash
Node Definition (from workflow)
 |
 v
Get Node Type
 |
 +---> model_call -> _execute_model_call
 +---> file_read -> _execute_file_read
 +---> file_write -> _execute_file_write
 +---> script_run -> _execute_script_run
 +---> git_commit -> _execute_git_commit
 |
 v
Execute Operation
 |
 v
Handle Errors
 |
 +---> Retry if transient (rate limit, timeout)
 +---> Fallback to next provider
 +---> Fail if fatal (auth, config)
 |
 v
Record Results
 |
 +---> Store output
 +---> Log cost
 +---> Add to trace
 +---> Check compliance
```

### Provider Selection Flow

```bash
Request Model
 |
 v
Check Cache
 |
 +---> Found -> Return cached instance
 |
 +---> Not found -> Select model
 |
 v
 Check Preferred Provider
 |
 +---> Available -> Use it
 |
 +---> Unavailable -> Try fallback providers
 |
 v
 Try next in chain
 |
 +---> Found available -> Use it
 |
 +---> None available -> Error
 |
 v
Create/Cache Model Instance
 |
 v
Return Model
```

---

## Security Architecture

### Credential Security

```bash
Credential Management
 |
 +---> Three-tier resolution:
 | 1. Check config file
 | 2. Check environment variables
 | 3. Return error
 |
 +---> In-flight redaction:
 | Pattern detection -> [REDACTED:type] replacement
 |
 +---> Error handling:
 | Detect credentials in errors -> Redact before logging
```

### Compliance Architecture

```bash
Workflow Execution
 |
 +---> At submission:
 | Check provider_config exists
 | Check tos_accepted = true
 | Check audit_enabled = true
 |
 +---> During execution:
 | Log all decisions
 | Track costs in real-time
 | Enforce budget limits
 |
 +---> At completion:
 | Generate compliance report
 | Verify all gates passed
 | Create audit trail
```

---

### Modularization Approach

Each module:

- Single responsibility
- Explicit dependencies (passed via constructor)
- No global state
- Testable in isolation
- Clear interface

#### Module Dependencies

```bash
runner.py (Orchestrator)
 |
 +---> graph.py (DAG management)
 +---> model_selector.py (Model factory)
 | |
 | +---> config_validator.py (Config validation)
 |
 +---> node_executor.py (Node dispatch)
 | |
 | +---> model_selector.py (Get model)
 | +---> cost_manager.py (Track cost)
 |
 +---> cost_manager.py (Budget tracking)
 +---> config_validator.py (Config validation)
 +---> checkpoint.py (State persistence)
 +---> observability.py (Logging/tracing)
 +---> trace.py (Trace data structures)
```

### Dependency Injection Pattern

All modules receive dependencies via constructor:

```python
class NodeExecutor:
 def __init__(self, model_factory, cost_manager, trace_logger, model_config):
 self.model_factory = model_factory
 self.cost_manager = cost_manager
 self.trace_logger = trace_logger
 self.model_config = model_config
```

Benefits:

- No hidden dependencies
- Easy to mock for testing
- Clear what each module needs
- No tight coupling

---

## Configuration Architecture

### Provider Registry

Located: config/provider_registry.default.json

Structure:

```json
{
 "provider_name": {
 "models": {
 "model_id": {
 "display_name": "Human readable name",
 "input_cost_per_token": 0.01,
 "output_cost_per_token": 0.03,
 "context_window": 200000
 }
 }
 }
}
```

Used by:

- model_selector.py: Find available models
- cost_manager.py: Calculate costs
- validator.py: Validate model references

### Workflow Configuration

Defined in: spec/workflow-schema.json

Key sections:

- metadata: Workflow info
- provider_config: Required provider and compliance settings
- nodes: Array of execution nodes with inputs/outputs
- edges: Data dependencies between nodes

---

## MCP Server Architecture

### Purpose

MCP (Model Context Protocol) servers allow:

- Subprocess-based model execution
- Provider isolation
- Security sandboxing
- Independent versioning

### Structure

Each MCP server:

1. Spawns as subprocess
2. Listens on stdio
3. Implements JSON-RPC protocol
4. Handles model initialization
5. Executes model calls
6. Returns responses

Used by:

- models/mcp_model.py: Subprocess lifecycle
- Specific model implementations: models/anthropic_mcp_model.py, models/openai_mcp_model.py, etc.

---

## Error Handling Strategy

### Transient Errors (Retry)

- Rate limits (429)
- Service unavailable (503)
- Timeouts
- Temporary network issues

Strategy: Retry with exponential backoff

### Fallback Errors (Try next provider)

- Provider specific rate limits
- Quota exceeded

Strategy: Try next provider in chain

### Fatal Errors (Fail immediately)

- Authentication failures
- Configuration errors
- Invalid input
- Model not found

Strategy: Return error, log for investigation

---

## Testing Architecture

### Unit Testing Strategy

- Mock external dependencies
- Test business logic in isolation
- Focus on critical paths

### Integration Testing Strategy

- Test workflows with realistic configurations
- Use test API keys (if available)
- Verify provider fallback chains

### E2E Testing Strategy

- Full workflow execution
- Multiple providers
- Real cost calculation
- Compliance validation

See coverage.md for test coverage details.

---

## Deployment Considerations

### Local Deployment

- Single machine execution
- Local Ollama support
- Development/testing

### Environment Variables

- ANTHROPIC_API_KEY
- OPENAI_API_KEY
- MISTRAL_API_KEY
- etc.

### Credential Security

- Never commit credentials
- Load from environment only
- Redact in logs and errors

---

## Key Design Decisions

1. Explicit data flow: No implicit global state
2. Modular execution: Each operation type is isolated
3. Provider agnostic: Same workflow across providers
4. Audit-first: Log everything, optimize later
5. Fail secure: Conservative on credentials and compliance
6. No magic: Every behavior is intentional and documented

---

__Document Status:__ Sprint 1 Release
__Last Updated:__ 2026-02-28
__Version:__ 1.0.0
