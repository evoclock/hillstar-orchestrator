# Template Resolution Bug in graph.py

**Date**: 2026-03-07
**Severity**: Critical (affects all workflows using `{{ node.output }}` templates)
**File**: `execution/graph.py`, lines 150-176
**Status**: FIXED (2026-03-07)

---

## Problem

The `_resolve_references` method in `WorkflowGraph` has a subtle bug in how it resolves `{{ node_id.output }}` template patterns.

### Data Flow

1. When a node executes, `graph.py:190` stores the **full executor result dict** in `self.node_outputs[node_id]`:
   ```python
   result = executor_fn(node_id, node, inputs)
   self.node_outputs[node_id] = result  # e.g. {"output": "extracted text...", "status": "ok", "tokens": 1234}
   ```

2. Separately, `node_executor.py:383` stores just the text content in **its own** `self.node_outputs`:
   ```python
   self.node_outputs[node_id] = result.get("output", "")  # Just the text
   ```

3. When `_resolve_references` resolves `{{ node_id.output }}`, it reads from the **graph's** `node_outputs` (the full dict):
   ```python
   output = self.node_outputs[node_id]  # Full dict: {"output": "text", "status": "ok"}
   if key == "output":
       return str(output) if output is not None else ""
       # Returns: "{'output': 'text', 'status': 'ok'}" -- stringified dict!
   ```

### Expected Behavior

`{{ node_id.output }}` should resolve to the text content of the node's output, not a stringified Python dict.

### Actual Behavior

It returns `str(full_result_dict)`, which looks like:
```
{'output': 'The extracted text content...', 'status': 'ok', 'tokens_used': 1234}
```

This gets injected into downstream prompt strings, polluting them with metadata.

---

## Impact Assessment (Revised)

Original assessment was that this only affects template-based substitution, not edge-based data flow.
This was **incorrect** -- all manuscript workflows use `{{ node.output }}` template strings in their
`input` fields (e.g., `"Schema: {{ load_schema_template.output }}"`). The bug would have caused
all downstream model calls to receive corrupted prompts containing Python dict string representations
instead of actual content. Severity upgraded to **Critical**.

---

## Proposed Fix

In `graph.py`, line 162-163, change:

```python
# BEFORE (buggy)
if key == "output":
    return str(output) if output is not None else ""

# AFTER (fixed)
if key == "output":
    if isinstance(output, dict):
        return str(output.get("output", "")) if output else ""
    return str(output) if output is not None else ""
```

This extracts the `"output"` field from the result dict when the stored value is a dict, which is the common case from `executor_fn`.

The `elif isinstance(output, dict)` branch at line 164 already handles arbitrary keys like `{{ node_id.status }}` or `{{ node_id.tokens }}` correctly -- it's only the `key == "output"` branch that needs the dict-aware extraction.

---

## Testing

Add a test that:
1. Stores a result dict `{"output": "hello world", "status": "ok"}` in `graph.node_outputs["test_node"]`
2. Calls `_resolve_references("Previous output: {{ test_node.output }}")`
3. Asserts the result is `"Previous output: hello world"`, not `"Previous output: {'output': 'hello world', 'status': 'ok'}"`

---

## Fix Applied (2026-03-07)

```python
# graph.py _resolve_references, line 162-165
if key == "output":
    # Extract the "output" field if result is a dict
    if isinstance(output, dict) and "output" in output:
        return str(output["output"]) if output["output"] is not None else ""
    return str(output) if output is not None else ""
```

Verified with unit test:
- Dict result `{"output": "SCHEMA CONTENT", "file_path": "/path"}` → resolves to `"SCHEMA CONTENT"`
- Plain string result `"plain text"` → resolves to `"plain text"`
- Reinstalled package and confirmed fix live in installed version

## Sprint Assignment

Moved from Sprint 2 to Sprint 1 hotfix. Remaining Sprint 2 work:
- Add formal unit tests to test suite
- Address the dual `node_outputs` design smell (graph vs node_executor stores)
