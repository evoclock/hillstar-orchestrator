# Hillstar Quick Reference

## Quick Links

- **Setup Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md) - Configure providers (Anthropic, OpenAI, Mistral, Google, local models)
- **Troubleshooting:** See README Troubleshooting for common issues
- **Full User Manual:** [User_Manual.md](User_Manual.md)
- **How-To Guide:** [how-to-workflow-data-flow.md](how-to-workflow-data-flow.md)
- **Provider Models:** [PROVIDER_MODEL_REFERENCE.md](PROVIDER_MODEL_REFERENCE.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)

## Installation

```bash
pip install hillstar-orchestrator
```

## Basic Imports

```python
# Configuration
from hillstar.config import HillstarConfig, SetupWizard, ModelSelector, ProviderRegistry

# Execution
from hillstar.execution import WorkflowRunner, WorkflowGraph, TraceLogger, CheckpointManager

# Governance
from hillstar.governance import GovernanceEnforcer, HookManager, GovernancePolicy

# Models
from hillstar.models import AnthropicModel, OpenAIModel, MistralModel, OllamaModel

# Utilities
from hillstar.utils import CredentialRedactor, HillstarException

# Workflows
from hillstar.workflows import WorkflowDiscovery, WorkflowValidator, ModelPresets
```

## Common Operations

### Load Configuration

```python
config = HillstarConfig.load_user_overrides()
```

### Run a Workflow

```python
runner = WorkflowRunner(
 workflow_path='workflows/my_workflow.json',
 output_dir='output/'
)
results = runner.execute()
```

### Validate a Workflow

```python
from hillstar.workflows import WorkflowValidator

validator = WorkflowValidator()
is_valid = validator.validate('workflows/my_workflow.json')
```

### Create a Model Instance

```python
runner = WorkflowRunner('workflow.json', 'output/')
model = runner.get_model('anthropic', 'claude-opus-4-6')
result = model.call("Your prompt here")
```

### Trace Execution

```python
from hillstar.execution import TraceLogger

trace = TraceLogger()
trace.log_event("task_started", {"task": "my_task"})
trace.save('trace.jsonl')
```

## CLI Commands

```bash
# Discover workflows
hillstar discover [PATH]

# Validate a workflow
hillstar validate WORKFLOW_PATH

# Execute a workflow
hillstar execute WORKFLOW_PATH [OUTPUT_DIR]

# Show available model presets
hillstar presets

# Run setup wizard (stores credentials in OS keyring)
hillstar wizard

# Set development mode
hillstar mode dev|normal

# Governance enforcement
hillstar enforce check|status

# Show version
hillstar --version
```

## Module Categories

| Module | Purpose |
|--------|---------|
| **config** | Configuration, provider registry, setup wizard |
| **execution** | Workflow runner, DAG execution engine |
| **governance** | Policy enforcement, compliance, hooks |
| **models** | LLM provider adapters (Anthropic, OpenAI, Mistral, Ollama, MCP) |
| **utils** | Credential redaction, exceptions, tracing |
| **workflows** | Workflow validation, discovery, presets |

## Key Classes

### WorkflowRunner

```python
runner = WorkflowRunner(workflow_path, output_dir)
results = runner.execute()
runner.get_model(provider, model_name)
runner.validate_workflow()
```

### HillstarConfig

```python
config = HillstarConfig.load_user_overrides()
config.get_provider(name)
config.validate()
```

### TraceLogger

```python
trace = TraceLogger()
trace.log_event(event_type, data)
trace.log_node_start(node_id)
trace.log_node_end(node_id, result)
trace.save(path)
```

### CheckpointManager

```python
checkpoint = CheckpointManager(output_dir)
checkpoint.save(node_id, state)
checkpoint.load(node_id)
checkpoint.has_checkpoint(node_id)
```

### WorkflowGraph

```python
graph = WorkflowGraph(workflow_dict)
graph.topological_sort()
graph.get_dependencies(node_id)
graph.is_dag()
```

## Provider Configuration

### Supported Providers

Cloud:

- **anthropic** - Claude models (Opus, Sonnet, Haiku)
- **openai** - GPT and o-series models
- **mistral** - Mistral, Codestral, Devstral models
- **google_ai_studio** - Gemini models

Local:

- **ollama** - Local models via Ollama
- **devstral_local** - Local Devstral (GPU required)

MCP (subprocess-based):

- **anthropic_mcp** - Claude via MCP server
- **openai_mcp** - GPT via MCP server
- **mistral_mcp** - Mistral via MCP server
- **ollama_mcp** - Ollama via MCP server

### Set API Key

```bash
# Recommended: Setup wizard (stores in OS keyring)
hillstar wizard

# Alternative: Environment variable (CI/CD or temporary use)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-proj-..."
export MISTRAL_API_KEY="..."
export GOOGLE_API_KEY="AIza..."
```

## Workflow JSON Format

```json
{
 "name": "My Workflow",
 "description": "Workflow description",
 "version": "1.0",
 "nodes": [
  {
   "id": "node_1",
   "type": "model",
   "provider": "anthropic",
   "model": "claude-opus-4-6",
   "prompt": "Your prompt template"
  }
 ],
 "edges": [
  {"from": "node_1", "to": "node_2"}
 ],
 "provider_config": {
  "compliance": {
   "tos_accepted": true,
   "audit_enabled": true
  }
 }
}
```

## Error Handling

```python
from hillstar.utils import HillstarException, CredentialRedactor

try:
 runner = WorkflowRunner('workflow.json', 'output/')
 results = runner.execute()
except HillstarException as e:
 # Handle Hillstar-specific errors
 print(f"Workflow error: {e}")
```

## Logging and Debugging

```python
# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Redact sensitive data from logs
from hillstar.utils import CredentialRedactor
redactor = CredentialRedactor()
safe_message = redactor.redact(message)
```

## Generate Documentation

```bash
# Generate user manual from source
python docs/doc_generator.py
```

## Performance Tips

1. **Reuse Models**: Create model instance once, call multiple times
2. **Use Checkpoints**: Enable checkpoints for long workflows
3. **Batch Operations**: Group multiple tasks in nodes
4. **Select Right Model**: Use smaller models when possible
5. **Cache Results**: Use trace/checkpoint system

## Useful Resources

| Resource | Location |
|----------|----------|
| Full User Manual | `docs/User_Manual.md` |
| How-To Guides | `docs/how-to-workflow-data-flow.md` |
| MCP Servers | `mcp-server/*.py` |
| Provider Registry | `config/provider_registry.default.json` |
| Model Reference | `docs/PROVIDER_MODEL_REFERENCE.md` |
| Workflow Schema | `spec/workflow-schema.json` |

## Compliance and Governance

```python
from hillstar.governance import GovernanceEnforcer

enforcer = GovernanceEnforcer()
policy = enforcer.load_policy('policies/default.json')
enforcer.enforce(workflow, policy)
```

## Architecture Diagram

```bash
+-------------------------------------+
|           Hillstar CLI              |
+--------+----------------------------+
         |
+--------+----------------------------+
|         WorkflowRunner              |
+---------+---------------------------+
| - Executes DAG workflows            |
| - Manages checkpoint/replay         |
| - Tracks execution trace            |
+--------+----------------------------+
         |
    +----+----+--------------+
    |         |              |
+-------+ +--------+ +--------------+
| Models| |Workflow| | Governance   |
+-------+ | Engine | +--------------+
| - LLM | | - Graph| | - Policy     |
|   API | | - Trace| | - Compliance |
| - MCP | | - Cache| | - Audit Hooks|
+--------+ +--------+ +--------------+
```

## Getting Help

```bash
# Show help for any command
hillstar --help
hillstar execute --help

# Check configuration
hillstar enforce status
```

## Common Issues

| Issue | Solution |
|-------|----------|
| API key not found | Set env var or run `hillstar wizard` |
| Invalid workflow | Run `hillstar validate WORKFLOW_PATH` |
| Module not found | Install with `pip install hillstar-orchestrator` |
| Ollama not connecting | Ensure `ollama serve` is running on port 11434 |

## Version Info

```bash
hillstar --version
python -c "import hillstar; print(hillstar.__version__)"
```

---

**Last Updated:** 2026-03-01
**Version:** 1.0.0
**Status:** Production Ready

For complete documentation, see [User_Manual.md](User_Manual.md)
