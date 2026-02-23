# How-To: Workflow Data Flow and Template References

## Overview

Hillstar workflows support **sequential data flow** between nodes. Output from one node can be automatically passed to the next node using template references.

## Template Reference Syntax

Use double-brace syntax to reference outputs from previous nodes:

```
{{ node_id.output }}
```

This will be replaced with the actual output from that node during execution.

## Example: Sequential Haiku Pipeline

This example shows a 5-node pipeline where each node processes the output of the previous node:

### Node 1: Haiku Generation
```json
{
  "haiku_generation": {
    "tool": "model_call",
    "provider": "anthropic",
    "model": "claude-haiku-4-5",
    "parameters": {
      "prompt": "Write 3 haikus about harmony, vigilance, and efficiency using nature metaphors.",
      "max_tokens": 300
    }
  }
}
```

**Output:** 3 haikus (as text)

### Node 2: Summarization (References Node 1)
```json
{
  "nano_summary": {
    "tool": "model_call",
    "provider": "openai",
    "model": "gpt-5-nano",
    "parameters": {
      "prompt": "You will receive 3 haikus:\n\n{{ haiku_generation.output }}\n\nSummarize their central themes in exactly 2 sentences.",
      "max_tokens": 100
    }
  }
}
```

**Input:** References `{{ haiku_generation.output }}`
**Output:** 2-sentence summary

### Node 3: Condensation (References Node 2)
```json
{
  "mistral_condense": {
    "tool": "model_call",
    "provider": "mistral",
    "model": "ministral-3b",
    "parameters": {
      "prompt": "Here is a summary:\n\n{{ nano_summary.output }}\n\nCondense this into a single paragraph (max 5 sentences).",
      "max_tokens": 150
    }
  }
}
```

**Input:** References `{{ nano_summary.output }}`
**Output:** 1-paragraph condensed summary

### Node 4: Entity Extraction (References Node 3)
```json
{
  "entity_extraction": {
    "tool": "model_call",
    "provider": "devstral_local",
    "model": "devstral-small-2-24b",
    "parameters": {
      "prompt": "Here is condensed text:\n\n{{ mistral_condense.output }}\n\nExtract all key concepts and list them as bullet points.",
      "max_tokens": 200
    }
  }
}
```

**Input:** References `{{ mistral_condense.output }}`
**Output:** Bullet-point list of concepts

### Node 5: Final Synthesis (References Node 4)
```json
{
  "final_synthesis": {
    "tool": "model_call",
    "provider": "anthropic_ollama",
    "model": "minimax-m2.1:cloud",
    "parameters": {
      "prompt": "Here are key concepts:\n\n{{ entity_extraction.output }}\n\nWrite a synthesis paragraph explaining how these concepts relate to workflow orchestration.",
      "max_tokens": 250
    }
  }
}
```

**Input:** References `{{ entity_extraction.output }}`
**Output:** Synthesis paragraph

## How It Works

1. **Execution Order:** Hillstar determines execution order using topological sort based on edges defined in the workflow graph.

2. **Template Resolution:** Before executing each node, Hillstar:
   - Reads the node's parameters (including prompts)
   - Finds all `{{ node_id.output }}` references
   - Replaces them with actual output from the referenced node
   - Passes the resolved parameters to the model

3. **Output Storage:** Each node's output is stored in the execution graph and available for subsequent nodes.

4. **Error Handling:** If a referenced node hasn't executed yet or failed, you'll get an error indicating the missing or failed dependency.

## Requirements

### 1. Define Edges
Your workflow must define edges showing the data flow direction:

```json
{
  "graph": {
    "edges": [
      {"from": "haiku_generation", "to": "nano_summary"},
      {"from": "nano_summary", "to": "mistral_condense"},
      {"from": "mistral_condense", "to": "entity_extraction"},
      {"from": "entity_extraction", "to": "final_synthesis"}
    ]
  }
}
```

Edges ensure:
- Proper execution order (topological sort)
- Validation that referenced nodes exist
- Dependency tracking for checkpoints and resumption

### 2. Valid Node References
Only reference nodes that exist in your workflow's nodes definition.

```json
// ✓ Valid - both nodes exist
"prompt": "Process this: {{ previous_node.output }}"

// ✗ Invalid - "nonexistent_node" doesn't exist
"prompt": "Process this: {{ nonexistent_node.output }}"
```

### 3. Reference Locations
Template references work in:
- **Prompts** (most common): `parameters.prompt`
- **Other string fields**: Any string field in node configuration

Template references do NOT work in:
- Non-string fields (numbers, booleans)
- Arrays (use JSON structure for complex data)

## Common Patterns

### Pattern 1: Simple Sequential Pipeline
Each node's prompt references the previous node's output:

```
Node A → Node B (uses A.output) → Node C (uses B.output) → Node D (uses C.output)
```

### Pattern 2: Multi-Step Processing
Transform data through multiple specialized models:

```
1. Generate (raw content)
2. Summarize (digest)
3. Extract (key points)
4. Synthesize (final insight)
```

### Pattern 3: Parallel + Sequential
Some nodes run independently, later node uses outputs of multiple nodes:

```json
{
  "nodes": {
    "node_a": { "tool": "model_call", ... },
    "node_b": { "tool": "model_call", ... },
    "node_c": {
      "parameters": {
        "prompt": "A says: {{ node_a.output }}\n\nB says: {{ node_b.output }}\n\nCombine these perspectives."
      }
    }
  },
  "edges": [
    {"from": "node_a", "to": "node_c"},
    {"from": "node_b", "to": "node_c"}
  ]
}
```

## Limitations

### 1. No Circular References
The workflow is a DAG (Directed Acyclic Graph). You cannot create cycles:

```json
// ✗ Invalid - circular dependency
{
  "edges": [
    {"from": "A", "to": "B"},
    {"from": "B", "to": "A"}
  ]
}
```

### 2. Output Type
Currently, outputs are treated as strings/text. For complex structured data, you should return it as formatted text (JSON, CSV, etc.) that the next node can parse.

### 3. No Conditional Logic
All referenced nodes must execute. There's no conditional branching (Node C runs if A succeeds, else run D).

## Debugging Template References

### View Prompts with Substitutions
Use `hillstar execute-node` to test a single node's prompt:

```bash
hillstar execute-node workflow.json node_name --inputs '{}'
```

### Check Workflow Validation
Validate your workflow before execution:

```bash
hillstar validate workflow.json
```

This will catch:
- Invalid node references
- Circular dependencies
- Missing nodes in edges

### View Execution Trace
After execution, check the trace file to see:
- What prompts were actually sent (with substitutions resolved)
- What outputs were returned
- Any substitution errors

```bash
cat .hillstar/trace_*.jsonl | jq '.'
```

## Full Working Example

See `python/hillstar/tests/e2e/workflow.json` for a complete 5-node orchestration pipeline with all template references.

To run the E2E test:

```bash
python python/hillstar/tests/e2e/test_e2e_execution.py
```

This executes the workflow twice:
1. **Baseline** - original workflow
2. **Loon-compressed** - same workflow compressed and expanded

Compare outputs in `test_e2e_output/comparison_report.txt`.
