# Provider Model Reference
tables, or cost guidance. Model identifiers and prices change too fast for a
hand-edited markdown file to stay truthful — a stale catalog is worse than
none. Workflows do not manage costs; there is no pricing-based logic to feed.

**Authoritative sources — always consult the provider's own pages:**

| Provider | Models / pricing |
|---|---|
| OpenAI | https://platform.openai.com/docs/models · https://openai.com/api/pricing |
| Anthropic | https://docs.anthropic.com/en/docs/about-claude/models · https://www.anthropic.com/pricing |
| Google AI Studio | https://ai.google.dev/gemini-api/docs/models · https://ai.google.dev/pricing |
| Mistral | https://docs.mistral.ai/getting-started/models · https://mistral.ai/pricing |
| Ollama | https://ollama.com/library (local models; no API cost) |
| Local / self-hosted | Whatever your server exposes (see `models/local_model.py`) |

## Model selection in Hillstar

- Specify the model per workflow node (`"model": "<provider's identifier>"`)
  or set a default via `MODEL_DEFAULT`.
- No hard-coded model list exists in code or docs; any identifier the
  provider accepts works. Unknown names fall back to conservative defaults.

## Parameter strategy by model class

The one section worth keeping, because it is about interfaces rather than
catalogs:

| Model class | Primary control | Avoid |
|---|---|---|
| Claude (Opus/Sonnet/Haiku) | `thinking` mode + `effort` | Temperature (use default) |
| OpenAI reasoning (GPT-5.x, o-series) | `reasoning_effort` | Temperature (unsupported) |
| OpenAI standard | `temperature` + `top_p` | — |
| Gemini | `thinking` mode | Temperature (causes degradation) |
| Mistral | `temperature` + `top_p` | — |
| Local/self-hosted | `temperature` | — |

## Costs

Hillstar does not price-gate or cost-manage workflow execution. Any cost
estimates previously shown here are historical. If you need cost visibility,
check your provider's usage dashboard.

---

*Version: 1.2.0 · Last updated: 2026-09-03*
