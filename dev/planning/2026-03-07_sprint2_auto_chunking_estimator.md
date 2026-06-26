# Sprint 2: Auto-Chunking Estimator and Rate-Limit Planner

**Status:** Proposed
**Priority:** High (usability-critical for non-technical users)
**Origin:** Manuscript_01 Step 05 — required 6 workflow iterations to get extraction right due to model-specific token limits, rate limits, and chunking requirements

---

## Problem Statement

When a workflow author writes a `model_call` node that processes N items, they currently must manually:

1. Know the model's max output token limit (e.g., Haiku 8,192 vs devstral-2 262,144)
2. Estimate output size per item (~300 tokens for a JSON extraction object)
3. Calculate how many items fit per call
4. Split nodes into chunks if needed
5. Know the provider's rate limit (e.g., Anthropic 50K input tokens/min for Haiku)
6. Add delays or throttling between calls to avoid 429 errors
7. Know whether the input (e.g., a full registry TSV) should be filtered per-node

This is expert-level knowledge. A less technical user writing a workflow would hit opaque failures (truncated output, 429 rate limits, silent provider fallback) without understanding why.

---

## Proposed Solution: `hillstar estimate` and Auto-Chunking

### Phase 1: `hillstar estimate <workflow.json>`

Pre-execution analysis that reports:

```
$ hillstar estimate workflows/core/step_05.json

Workflow: step_05_publication_extraction (49 nodes)
Model: claude-haiku-4-5-20251001 (anthropic)

Node Analysis:
  extract_chesler2_c1:
    Input tokens (est): ~3,200 (filtered registry + passages)
    Output tokens (est): ~6,600 (22 terms x 300 tok/term)
    Model max output: 8,192 -- [OK] fits in single call

  extract_chesler3 (if not chunked):
    Input tokens (est): ~42,000 (full registry + passages)
    Output tokens (est): ~22,200 (74 terms x 300 tok/term)
    Model max output: 8,192 -- [WARN] exceeds by 2.7x, needs 3 chunks

Rate Limit Analysis:
  Provider: anthropic (50,000 input tokens/min)
  Back-to-back calls: extract_c1 (3,200) + extract_c2 (3,200) + extract_c3 (3,000)
    Cumulative: 9,400 tokens in ~5s -- [OK] under 50K/min

  If using full registry (42,000 per call):
    2 calls = 84,000 tokens in ~10s -- [FAIL] exceeds 50K/min
    Recommendation: filter input OR add 60s delay between calls

Estimated cost: $0.12
Estimated duration: 18 minutes (including 15s delays)
```

### Phase 2: Auto-Chunking in `model_call` Nodes

New node-level field `auto_chunk`:

```json
{
  "tool": "model_call",
  "provider": "anthropic",
  "model": "claude-haiku-4-5-20251001",
  "auto_chunk": {
    "enabled": true,
    "items_field": "term_id",
    "max_items_per_call": null,
    "merge_strategy": "concat_json_arrays"
  }
}
```

When `auto_chunk.enabled` is true, the runner:
1. Counts items in the input matching `items_field`
2. Queries the model's max output tokens from the provider registry
3. Estimates output size per item (configurable or auto-detected from first call)
4. Splits into optimal chunk count
5. Executes chunks sequentially with rate-limit-aware delays
6. Merges outputs using `merge_strategy`

### Phase 3: Rate-Limit Aware Scheduling

The DAG scheduler should:
1. Query provider rate limits from the registry (or from 429 response headers)
2. Track cumulative input/output tokens per provider per minute
3. Insert delays automatically when approaching limits
4. Log rate-limit events for post-hoc analysis

---

## Implementation Details

### Token Estimation

For `hillstar estimate`:
- Input tokens: count characters / 4 (rough estimate) or use tiktoken for OpenAI, anthropic tokenizer for Claude
- Output tokens: heuristic based on prompt structure (JSON array → count items, multiply by template size)
- Model limits: already in provider registry (`max_output_tokens`, `context_window`)

### Rate Limit Sources

| Provider | Rate Limit Type | How to Get |
|----------|----------------|------------|
| Anthropic | Input tokens/min, requests/min | API response headers (`x-ratelimit-*`) or docs |
| OpenAI | Tokens/min, requests/min | API response headers |
| Ollama cloud | Varies by model vendor | Model card / empirical |

### Merge Strategies

| Strategy | Behavior |
|----------|----------|
| `concat_json_arrays` | Parse each chunk as JSON array, concatenate |
| `concat_text` | Join chunk outputs with newlines |
| `last_wins` | Use only the final chunk output |
| `custom_script` | Run a user-defined merge script |

---

## Evidence from Manuscript_01

### Failures that this feature would have prevented:

1. **Run 4 (minimax-m2.5):** Output truncated at 8,192 tokens for Chesler3 (74 terms). `hillstar estimate` would have flagged: "Output exceeds max by 2.7x, needs 3 chunks."

2. **Run 5 (devstral-2):** All 260 terms sent in single calls per project. No truncation (262K limit), but model couldn't discriminate across 74 terms at once — blanket labels. Auto-chunking would have split into smaller batches, improving per-term attention.

3. **Run 6 (Haiku v6.0):** 429 rate limit on 3rd consecutive chunk. Input was ~42K tokens per call (full registry). `hillstar estimate` would have flagged: "3 calls x 42K = 126K tokens in ~15s, exceeds 50K/min. Recommendation: filter input."

4. **Run 6 (Haiku v6.0):** Provider fallback silently routed to openai_mcp on 429. Fixed separately (explicit mode disables fallback), but rate-limit-aware scheduling would have prevented the 429 entirely.

### Cost of not having this feature:

- 6 workflow iterations to get Step 05 right
- ~$0.75 in wasted API calls
- ~4 hours of human debugging time
- Required expert knowledge of 3 different model token limits, 2 rate limit policies, and provider routing internals

---

## Dependencies

- Provider registry must include `max_output_tokens` and `rate_limits` per model (partially exists)
- Token counting library (tiktoken for OpenAI, anthropic tokenizer for Claude, character heuristic as fallback)
- DAG scheduler needs per-provider token accounting

## Estimated Effort

- Phase 1 (`hillstar estimate`): 2-3 days
- Phase 2 (auto-chunking): 3-5 days
- Phase 3 (rate-limit scheduling): 3-5 days
- Total: ~2 weeks with testing
