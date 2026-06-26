# Sprint 2: Validator and Registry Fixes

**Date**: 2026-03-07
**Context**: Found during workflow reassessment for Julen_Gamboa_Manuscript_01
**Related**: `2026-03-07_template_resolution_bug.md` (same sprint, separate note)

---

## Issue 1: `provider_config` schema requirement vs compliance enforcement

**File**: `workflows/validator.py`, line 106
**Status**: LOCAL PATCH APPLIED (2026-03-07) -- needs proper Sprint 2 implementation

### Problem

`validate_schema()` listed `provider_config` as a hard required top-level field.
This blocked all workflows without it, including purely local ones.

### Design Decision

`provider_config` is a compliance attestation layer, NOT a structural requirement.
It should be:
- **Required for cloud providers** (OpenAI, Anthropic, Mistral, Google) -- these
  have real ToS and compliance obligations
- **Optional/ignorable for local providers** (Ollama, llama.cpp, jan_code, devstral)
  -- no ToS, no compliance, data stays local

### Local Patch (2026-03-07)

Changed `required_fields` from `["id", "graph", "provider_config"]` to `["id", "graph"]`.

The compliance logic in `validate_compliance()` already handles the distinction:
- Local providers have `requires_tos_acceptance: false` in registry -> checks pass
- Unknown local providers (jan_code) not in registry -> checks skip
- Cloud providers with `requires_tos_acceptance: true` -> still enforced via
  `provider_config` in the workflow JSON

So removing provider_config from required_fields means:
- Purely local workflows validate without any provider_config
- Workflows using cloud providers still need provider_config with attestation
- No compliance checks are weakened -- cloud provider enforcement is unchanged

### Sprint 2: Proper Implementation

1. **Validation levels**: `hillstar validate` (structure) vs `hillstar validate --strict`
   (structure + full compliance). Default should be structure-only.
2. **Clear messaging**: When a workflow uses a cloud provider without provider_config,
   the error should explain what to add, not just say "missing field".
3. **Local provider auto-detection**: Providers with `auth_type: "none"` or
   `endpoint: localhost` should be auto-classified as local and exempt from compliance.
4. **Tests**: Add test cases for local-only, cloud-only, and mixed workflows.

---

## Issue 2: `jan_code` provider missing from registry

**File**: `config/provider_registry.default.json`
**Status**: NOT YET FIXED -- Sprint 2

### Problem

The `jan_code` provider is used in multiple manuscript workflow nodes (prereq_check,
draft_map, extract_header, schema_check, etc.) but is not in either:
- `config/provider_registry.default.json` (package default)
- `~/.hillstar/provider_registry.json` (user override)

The validator at line 349-358 flags unknown providers:
```python
if provider and provider not in available_providers:
    errors.append(f"Node '{node_id}': Unknown provider '{provider}'...")
```

### What jan_code is

jan-code is a local model served via Jan (https://jan.ai/), which exposes an
OpenAI-compatible API at `http://localhost:1337`. It's a local-first, free model
used for high-volume draft/check tasks.

### Fix

Add `jan_code` to `provider_registry.default.json`:

```json
"jan_code": {
  "display_name": "Jan Code (Local)",
  "type": "local",
  "endpoint": "http://localhost:1337",
  "auth_type": "none",
  "env_vars": [],
  "compliance": {
    "requires_tos_acceptance": false,
    "data_residency": ["local"],
    "restricted_use_cases": [],
    "audit_required": false
  },
  "models": {
    "jan-code": {
      "display_name": "Jan Code",
      "context_window": 32768,
      "max_output_tokens": 8192,
      "cost_per_1k_input": 0.0,
      "cost_per_1k_output": 0.0,
      "supports_streaming": true,
      "supports_function_calling": false
    }
  }
}
```

Also consider adding `minimax-m2.5:cloud` to the `ollama` provider's model list
in the registry, since it's a cloud-routed model that Ollama proxies.

---

## Issue 3: `minimax-m2.5:cloud` not in ollama model registry

**File**: `config/provider_registry.default.json`, ollama provider section
**Status**: NOT YET FIXED -- Sprint 2

### Problem

`minimax-m2.5:cloud` is used in `pre_phase_02_curation_scaffold.json` and
`step_07_cross_project_reconciliation.json` under the `ollama` provider. The
validator flags it as unknown because it's not in the ollama models list.

This is a cloud-routed model that Ollama proxies -- it works at execution time
but the static registry doesn't know about it.

### Fix

Add to ollama's models in registry, or create a mechanism for dynamic model
discovery (e.g., `ollama list` at validation time).

---

## Issue 4: No mechanism to register custom providers/models at setup time

**Status**: NOT YET IMPLEMENTED -- Sprint 2

### Problem

When a user installs hillstar and runs `hillstar wizard` (or similar setup), there
is no step to discover or register local models that aren't in the default registry.
This means any user with custom local models (like jan-code, or a cloud-routed Ollama
model like minimax-m2.5:cloud) will hit validation failures until they manually edit
`provider_registry.default.json` or `~/.hillstar/provider_registry.json`.

This is poor UX and will be a recurring friction point.

### Required Implementation

`hillstar wizard` or a new `hillstar registry` command should:

1. **Auto-discover local models** -- query running servers:
   - `ollama list` for Ollama models (including cloud-routed ones)
   - Probe `localhost:8081` for llama.cpp (jan-code)
   - Probe `localhost:8080` for other local servers (devstral)
2. **Prompt user to register** -- for each discovered model not already in registry,
   ask if they want to add it
3. **Append to user registry** -- write to `~/.hillstar/provider_registry.json`
   (user override), not the package default. This way the default stays clean and
   user customizations survive package updates.
4. **Validate workflow providers** -- after setup, `hillstar validate` should check
   that all providers referenced in a workflow are registered and reachable.

### UX Flow

```
$ hillstar registry discover

[SEARCH] Scanning local model servers...

  [OK] Ollama (localhost:11434): 12 models found
       New models not in registry:
         - minimax-m2.5:cloud
         - deepseek-r1:cloud

  [OK] llama.cpp (localhost:8081): jan-code responding
       Not in registry: jan_code / jan-code

  [SKIP] devstral_local (localhost:8080): not responding

Add discovered models to ~/.hillstar/provider_registry.json? [Y/n]
```

---

## Summary

| Issue | File | Patched? | Sprint 2 work |
|-------|------|----------|---------------|
| provider_config required | validator.py:106 | YES (local) | Validation levels, messaging, tests |
| jan_code missing | provider_registry.default.json | YES (local) | Auto-discovery in wizard/registry command |
| minimax-m2.5:cloud unknown | provider_registry.default.json | YES (local) | Auto-discovery in wizard/registry command |
| Registry discovery UX | N/A | No | New `hillstar registry discover` command |
| Template resolution bug | graph.py:162-163 | YES (hotfix) | See separate note; remaining: unit tests, dual node_outputs cleanup |
