# Hillstar Quick Reference

## Quick Links

- **Setup Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md) - Configure providers (Anthropic, OpenAI, Mistral, local models)
- **Troubleshooting:** See README § Troubleshooting for common issues
- **Full User Manual:** [User_Manual.md](User_Manual.md) (4,700+ lines)
- **How-To Guide:** [how-to-workflow-data-flow.md](how-to-workflow-data-flow.md)
- **Source Code:** [hillstar/utils/doc_generator.py](../python/hillstar/utils/doc_generator.py)

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
from hillstar.utils import DAGVisualizer, CredentialRedactor, HillstarException

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

# Run setup wizard
hillstar wizard

# Set development mode
hillstar mode dev|normal

# Governance enforcement
hillstar enforce check|status

# Reduce workflow to Loon format
hillstar loon reduce WORKFLOW

# Expand Loon back to standard
hillstar loon expand LOON

# Execute a single node
hillstar execute-node WORKFLOW NODE

# Show version
hillstar --version
```

## Module Categories

| Module | Purpose |
|--------|---------|
| **config** | Configuration, provider registry, setup |
| **execution** | Workflow runner, execution engine |
| **governance** | Policy enforcement, compliance |
| **models** | LLM provider adapters |
| **utils** | Utilities, helpers, visualization |
| **workflows** | Workflow validation, discovery |

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

- **anthropic** - Claude models
- **openai** - GPT models
- **mistral** - Mistral models
- **ollama** - Local models
- **devstral_local** - Local Devstral
- **google_ai_studio** - Google models
- **azure_ai** - Azure models
- **amazon_bedrock** - AWS Bedrock
- **cohere** - Cohere models
- **meta_llama** - Meta Llama models

### Set API Key

```bash
# Via environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Via configuration file
echo '{"providers": {"anthropic": {"api_key": "sk-ant-..."}}}' > ~/.hillstar/provider_registry.json
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

## Logging & Debugging

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
# Generate user manual
python python/generate-docs.py

# With statistics
python python/generate-docs.py --verbose --stats

# Custom output
python python/generate-docs.py --output custom_docs/Manual.md
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
| Source Code | `python/hillstar/` |
| Package Setup | `python/setup.py` |
| Example Workflows | `dev/examples/` |
| Configuration | `~/.hillstar/` |

## Compliance & Governance

```python
from hillstar.governance import GovernanceEnforcer

enforcer = GovernanceEnforcer()
policy = enforcer.load_policy('policies/default.json')
enforcer.enforce(workflow, policy)
```

## Architecture Diagram

```bash
┌─────────────────────────────────────┐
│         Hillstar CLI                │
└────────┬────────────────────────────┘
         │
┌────────▼────────────────────────────┐
│      WorkflowRunner                 │
├─────────────────────────────────────┤
│  - Executes DAG workflows           │
│  - Manages checkpoint/replay        │
│  - Tracks execution trace           │
└────────┬────────────────────────────┘
         │
    ┌────┴───┬───────────────────┐
    │        │                   │
┌───▼──┐ ┌───▼────┐ ┌────────────▼──┐
│Models│ │Workflow│ │Governance     │
├──────┤ │Engine  │ ├───────────────┤
│      │ │        │ │- Policy       │
│- LLM │ │- Graph │ │- Compliance   │
│ API  │ │- Trace │ │- Audit Hooks  │
│      │ │- Cache │ │               │
└──────┘ └────────┘ └───────────────┘
```

## Getting Help

```bash
# Show help for any command
hillstar --help
hillstar execute --help

# Run diagnostic
python -m hillstar.tests.e2e.troubleshoot.*

# Check configuration
hillstar enforce status

# View logs
tail -f ~/.hillstar/logs/*.log
```

## Common Issues

| Issue | Solution |
|-------|----------|
| API key not found | Set env var or run `hillstar wizard` |
| Invalid workflow | Run `hillstar validate WORKFLOW_PATH` |
| Module not found | Install with `pip install hillstar-orchestrator` |
| Permission denied | Check file permissions in `~/.hillstar/` |

## Version Info

```bash
hillstar --version
python -c "import hillstar; print(hillstar.__version__)"
```

---

**Last Updated:** 2026-02-17
**Version:** 1.0
**Status:** Production Ready

For complete documentation, see [User_Manual.md](User_Manual.md)
