# Provider Model Reference

**Last Updated:** 2026-02-21 (Schema updated to include cached input & cache storage columns)
**Source:** Official provider documentation and pricing pages
**Purpose:** Comprehensive model catalog with pricing (including caching), capabilities, and parameter support for informed model selection and preset design

**Update Frequency:** This document is updated manually for major releases, deprecations, and EOL announcements only. For real-time pricing and model availability, the orchestrator uses provider SDKs (see Phase 2a implementation). **We recommend using SDK-based cost estimation in production** rather than relying on this markdown for dynamic pricing.

---

## Parameter Strategy by Model Class

**Critical Decision:** Different model families require different tuning approaches.

| Model Class | Primary Control | Avoid | Recommendation |
|-------------|-----------------|-------|-----------------|
| **Claude (Opus/Sonnet/Haiku)** | `thinking` mode + `effort` parameter | Temperature (use default) | Extended/adaptive thinking controls reasoning depth |
| **OpenAI Reasoning** (GPT-5.x, o3/o4-mini) | `reasoning_effort` parameter | Temperature (not supported) | Effort parameter allocates internal reasoning tokens |
| **OpenAI Standard** (GPT-4.1) | `temperature` + `top_p` | — | Full parameter support for exploration tasks |
| **Gemini** (3.x, 2.5) | `thinking` mode | Temperature (causes degradation) | Changing temperature causes looping, keep at default |
| **Mistral** (all models) | `temperature` + `top_p` | — | **Fix one, adjust the other** for exploration |
| **Local Models** (self-hosted) | `temperature` | — | Device-specific recommendations (see section) |
| **Implementation** (development) | `temperature` + `top_p` | — | Testing/dev models allow full tuning |

---

## OpenAI Models

### Agentic & Reasoning Models (use `reasoning_effort`)

| Model | Use Case | Input Cost/1M | Cached Input/1M | Output Cost/1M | Context | Parameter Support | Notes |
|-------|----------|---|---|---|---------|-------------------|-------|
| **GPT-5.2** | Coding, agentic tasks, agents | $1.75 | $0.175 | $14 | 400k | `reasoning_effort`, **NO temperature** | Primary coding model |
| **GPT-5.1** | Coding, agentic tasks (previous gen) | $1.25 | $0.125 | $10 | 400k | `reasoning_effort`, **NO temperature** | Legacy, can be used instead of GPT-5.2 |
| **o3** | Deep complex reasoning, math, research | $10 | $2.50 | $40 | 200k | `reasoning_effort`, **NO temperature** | Advanced reasoning model |
| **o4-mini** | Faster reasoning, complex tasks | $2 | $0.50 | $8 | 200k | `reasoning_effort`, **NO temperature** | Faster alternative to o3 |

### Standard Models (use `temperature` + `top_p`)

| Model | Use Case | Input Cost/1M | Cached Input/1M | Output Cost/1M | Context | Parameter Support | Notes |
|-------|----------|---|---|---|---------|-------------------|-------|
| **GPT-4.1** | Instruction following, tool use, knowledge tasks | $2 | $0.50 | $8 | 1M | `temperature`, `top_p` | Broad capabilities, temperature tunable |
| **GPT-5-mini** | Well-defined small tasks, quick inference | $0.25 | $0.025 | $2 | 400k | `reasoning_effort`, **NO temperature** | Lightweight reasoning |
| **GPT-5-nano** | Summarization, classification, fast tasks | $0.05 | $0.005 | $0.40 | 400k | `reasoning_effort`, **NO temperature** | Ultra-lightweight |

### Parameter Guidance

- **Reasoning Models:** Use `reasoning_effort` ("low", "medium", "high") to control token allocation. **Do NOT adjust temperature** (not supported).
- **Standard Models:** Temperature fully tunable. Recommended: 0.7 for balanced tasks, 0.3-0.5 for deterministic code analysis.
- **Cost Calculation:** Average of input + output pricing for effective cost per token.

---

## Anthropic Models

### Current Generation (Feb 2026)

| Model | Release | EOL | Input Cost/1M | Cache Writes (5m)/1M | Cache Writes (1h)/1M | Cache Hits/1M | Output Cost/1M | Thinking Mode | Use `effort` | Best For |
|-------|---------|-----|---|---|---|---|---|---|---|----------|
| **claude-opus-4-6** | Active | Feb 5, 2027 | $5 | $6.25 | $10 | $0.50 | $25 | Adaptive thinking | ✓ Yes | **Building agents, coding, best performance** |
| **claude-sonnet-4-6** | Active | Feb 17, 2027 | $3 | $3.75 | $6 | $0.30 | $15 | Extended thinking | ✓ Yes | **Balance of speed & intelligence, agentic tasks** |
| **claude-haiku-4-5-20251001** | Active | Oct 15, 2026 | $1 | $1.25 | $2 | $0.10 | $5 | Extended thinking | ✓ Yes | **Fastest with near-frontier intelligence** |

### Previous Generations (Sunset Timeline)

| Model | Release | EOL | Input Cost/1M | Cache Writes (5m)/1M | Cache Writes (1h)/1M | Cache Hits/1M | Output Cost/1M | Notes |
|-------|---------|-----|---|---|---|---|---|---------|
| claude-opus-4-5-20251101 | Active | Nov 24, 2026 | $5 | $6.25 | $10 | $0.50 | $25 | Older Opus, migrate to 4.6 |
| claude-opus-4-1-20250805 | Active | Aug 5, 2026 | $15 | $18.75 | $30 | $1.50 | $75 | **DEPRECATED: Use 4.6 instead ($50/MTok savings)** |
| claude-sonnet-4-5-20250929 | Active | Sep 29, 2026 | $3 | $3.75 | $6 | $0.30 | $15 | Migrate to 4.6 before EOL |
| claude-haiku-3-20240307 | EOL | Mar 7, 2025 | $0.25 | $0.30 | $0.50 | $0.03 | $1.25 | **URGENT: Migrate to 4.5** |

### Thinking Modes & Effort Parameter

### **Opus 4.6: Adaptive Thinking + Effort**

Automatically allocates thinking tokens based on complexity and effort level. No manual budget needed.

```bash
curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: $ANTHROPIC_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "model": "claude-opus-4-6",
    "max_tokens": 16000,
    "thinking": {
      "type": "adaptive",
      "effort": "high"  # low, medium, high
    },
    "messages": [{"role": "user", "content": "Analyze this codebase..."}]
  }'
```

### **Sonnet 4.6 & Haiku 4.5: Extended Thinking + Effort**

Manual thinking budget with effort-based allocation.

```bash
curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: $ANTHROPIC_API_KEY" \
  --header "content-type: application/json" \
  --data '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {
      "type": "enabled",
      "budget_tokens": 10000  # Allocate thinking tokens
    },
    "messages": [{"role": "user", "content": "..."}]
  }'
```

Parameter Guidance

- **Temperature:** Available but defaulted to 0.00000073 (deterministic). **Do NOT adjust** — use `thinking`/`effort` instead for reasoning control.
- **Top P:** Conflicts with temperature. **Do NOT use with temperature.**
- **Thinking Tokens:** Separate billing from output tokens. See [Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- **Best Practice:** Control complexity with `effort` parameter, not temperature.
- **List Models** API available to retrieve which models are available for use ([List Models API](https://platform.claude.com/docs/en/api/models/list))

---

## Mistral Models

### Cloud API Models (use `temperature` + `top_p`)

**Note**: Mistral does not offer prompt caching. All costs are per-token without cache discounts.

| Model | Use Case | Input Cost/1M | Output Cost/1M | Context | Parameter Support | Notes |
|-------|----------|---|---|---------|-------------------|-------|
| **Magistral Medium 1.2** | Multimodal reasoning, agentic tasks | $2 | $5 | 131k | `temperature`, `top_p` | Reasoning-focused |
| **Mistral Large 3** | General purpose MoE, agentic | $0.5 | $1.5 | 131k | `temperature`, `top_p` | Cost-effective for tasks |
| **Devstral 2** | Coding agent, tool use, codebase exploration | $0.5 | $2 | 131k | `temperature`, `top_p` | **Best for software engineering** |
| **Mistral Medium 3.1** | Multimodal, general tasks | $0.5 | $2 | 131k | `temperature`, `top_p` | Balanced performer |
| **Magistral Small 1.2** | Small multimodal reasoning | $0.5 | $1.5 | 131k | `temperature`, `top_p` | Lightweight reasoning |
| **Codestral** | Code completion, code generation | $0.3 | $0.9 | 131k | `temperature`, `top_p` | Low-latency, high-frequency |
| **Mistral Small 3.2** | Fast tasks, smaller scale | $0.1 | $0.3 | 131k | `temperature`, `top_p` | Lightweight general purpose |
| **Ministral 3 14B** | Small tasks, local alternative | $0.05 | $0.2 | 32k | `temperature`, `top_p` | Edge/local deployment option |

### Parameter Tuning Guidance

**Recommended Approach:**

1. **Start with Temperature** (not Top P)
   - 0.3-0.5: Deterministic code analysis, specific factual tasks
   - 0.7: Balanced exploration and quality
   - 1.0+: Creative tasks, multiple interpretations
2. **Adjust Top P** while keeping Temperature fixed
   - 0.5: Recommended default (filters unlikely tokens)
   - 0.3-0.5: More deterministic
   - 0.7-0.9: More exploratory
3. **Application Order:** Temperature applied first, then Top P filters based on that distribution

**Key Insight:** Unlike other providers, Mistral fully supports temperature/top_p tuning. Use this for exploration and multi-hypothesis tasks.

---

## Google Gemini Models

**Caching Note**: Google offers explicit caching for text, image, and video content. Cached input costs less than regular input. Cache storage charged per hour.

### Frontier Models (Gemini 3.x - use `thinking` mode)

| Model | Use Case | Input Cost/1M | Cached Input/1M | Cache Storage/1M/hr | Output Cost/1M | Context | Thinking Support | Notes |
|-------|----------|---|---|---|---|---------|-------------------|-------|
| **gemini-3.1-pro-preview** | Multimodal, agentic AI (best in class) | $2/≤200k, $4/>200k |$0.40 | $4.50 | $12/≤200k, $18/>200k | 1M | ✓ Yes | Best overall, context-aware pricing |
| **gemini-3-flash-preview** | Price-performance multimodal, agentic | $0.50 | $0.05 | $1 | $3 | 1M | ✓ Yes |  |

### Advanced Reasoning Models (Gemini 2.5 - use `thinking` mode)

| Model | Use Case | Input Cost/1M | Cached Input/1M | Cache Storage/1M/hr | Output Cost/1M | Context | Notes |
|-------|----------|---|---|---|---|---------|---------|
| **gemini-2.5-pro** | SOTA thinking for code, math, STEM, codebases, documents | $1.25/≤200k, $2.50/>200k | $0.25 | $4.50 | $10/≤200k, $15/>200k | 1M | Long context reasoning |
| **gemini-2.5-flash** | Best price-performance multimodal | $0.30 | $0.03 | $1 | $2.50 | 1M | Fast multimodal inference |
| **gemini-2.5-flash-lite** | Cost-efficient multimodal | $0.03 | $0.01 | $1 | $0.12 | 1M | Ultra-lightweight |
| **gemini-2.5-computer-user** | Agentic browser automation, UI testing, visual reasoning | $1.25/≤200k, $2.50/>200k | — | — | $10/≤200k, $15/>200k | 1M | Direct interface interaction |

### Specialized Models

| Model | Use Case | Input Cost/1M | Cost/1M | Notes |
|-------|----------|--|-------|-------|
| **deep-research-pro-preview** | Multistep investigation, complex synthesis (Gemini 3 Pro powered) | $4 | $18 (>200k) / $12 (≤200k) | Agentic research |
| **gemini-robotics-er-1.5** | Robotic understanding, physical interaction | $0.30 | $2.50 | Specialized domain |
| **gemini-embedding-001** | Vector embeddings, semantic search, RAG | - | $0.15 | Non-chat, for retrieval |

### Legacy Models (Gemini 2.0)

| Model | Use Case | Input Cost/1M | Cached Input/1M | Cache Storage/1M/hr | Output Cost/1M | Notes |
|-------|----------|---|---|---|---|-------|
| **gemini-2.0-flash** | Balanced multimodal | $0.10 | $0.025 | $1 | $0.40 | Previous gen |
| **gemini-2.0-flash-lite** | Smallest, cost-effective | $0.075 | — | — | $0.30 | **Most budget-friendly** |

Parameter Guidance

- **Temperature:** **Do NOT adjust.** Default (1.0) required. Changing temperature "causes looping or degraded performance on reasoning tasks."
- **Thinking Mode:** Use thinking mode for complex reasoning tasks. Registry recommends keeping temperature at default.
- **Context-Aware Pricing:** Gemini 3 Pro charges different rates for ≤200k vs >200k context. Calculate costs carefully.

---

## Ollama Cloud Models (Free Tier with Limits)

**Note:** List intentionally curated to exclude prevalence of Chinese open models due to institutional restrictions and policy concerns.

| Model | Use Case | Base Cost | Context | Notes |
|-------|----------|-----------|---------|-------|
| **gpt-oss:20b-cloud** | Reasoning, agentic tasks, developer use | $0 (free tier) | 8k | Fine-tunable, open-weight |
| **gpt-oss:120b-cloud** | Advanced reasoning, agentic development | $0 (free tier) | 8k | Larger open-weight model |
| **gemini-3-flash-preview:cloud** | Speed + frontier intelligence | $0 (free tier) | 1M | Google models via Ollama |
| **devstral-2:123b-cloud** | Coding, codebase exploration, software engineering agents | $0 (free tier) | 131k | **Excellent for codebase analysis** |

### Pricing Model

- **Free Tier:** Limited tokens per month + rate limits
- **Paid Tiers:** Higher limits, higher tokens
- All models support reasoning effort tuning where available

---

## Local Models (Self-Hosted)

### Small/Edge Models (temperature tunable)

| Model | Size | VRAM | Context | Use Case | Temperature Guidance | Notes |
|-------|------|------|---------|----------|----------------------|-------|
| **nemotron-mini** | 2.7B | 2.7GB | 4k | RAG, Q&A | Standard (0.7) | Flexible, standard temp |
| **mistral-nemo:12b** | 12B | 12GB | 128k | General purpose, reasoning chains | **≤0.3 recommended** | Long context capability |

### Medium/Coding Models (temperature tunable)

| Model | Size | VRAM | Context | Use Case | Temperature Guidance | Notes |
|-------|------|------|---------|----------|----------------------|-------|
| **gpt-oss:20b** | 20B | 16GB | 8k | Reasoning, agentic tasks | Standard (0.5-0.7) | Reasoning effort tuning |
| **magistral:24b** | 24B | 16GB | 131k | General purpose, long reasoning chains | Standard (0.7) | Flexible |
| **devstral-small-2:24b** | 24B | 16GB | 32k | **Codebase exploration, tool use, file editing** | **≤0.15 CRITICAL** | Coding-focused, determinism important |

### Quantization Notes

- **Q4_K_M:** 4-bit quantization, recommended for quality/performance balance
- **Q4_0:** 4-bit unsigned, slightly faster but lower quality
- VRAM estimates based on Q4_K_M quantization

---

## Model Selection Decision Tree

### For Coding & Software Engineering Tasks

```markdown
Task: Analyze codebase, edit files, tool use, agents
├─ Cloud available? YES
│  ├─ High Budget (best performance)
│  │  ├─ Anthropic: Opus 4.6 (adaptive thinking, effort=high)
│  │  ├─ OpenAI: GPT-5.2 (reasoning_effort=high)
│  │  ├─ Google: Gemini 2.5-pro (thinking mode, 1M context)
│  │  └─ Mistral: Magistral Medium 1.2 (temperature 0.2, tool use)
│  ├─ Medium Budget (good balance)
│  │  ├─ Anthropic: Sonnet 4.6 (extended thinking, effort=medium)
│  │  ├─ OpenAI: GPT-5.1 or GPT-5.2 (reasoning_effort=medium)
│  │  ├─ Google: Gemini 3-pro (thinking mode)
│  │  └─ Mistral: Devstral 2 (temperature 0.2, coding agent)
│  └─ Low Budget (cost-effective)
│     ├─ Anthropic: Haiku 4.5 (extended thinking, effort=low)
│     ├─ OpenAI: GPT-5-mini (reasoning_effort=low)
│     ├─ Google: Gemini 3-flash ($0.25/1M, thinking mode)
│     └─ Mistral: Mistral Large 3 ($1.5/1M, temperature 0.2)
└─ Local only? YES
   ├─ 16GB+ VRAM: devstral-small-2:24b (Mistral, temp ≤0.15) OR gpt-oss:20b (reasoning effort)
   └─ 12GB VRAM: mistral-nemo:12b (temp ≤0.3) OR magistral:24b (general)
```

### For General Purpose / Agentic Tasks

```markdown
Task: Multi-step workflows, tool calling, agent orchestration
├─ High Performance Needed
│  ├─ Anthropic: Opus 4.6 + adaptive thinking (effort=high)
│  ├─ OpenAI: GPT-5.2 + reasoning_effort (high)
│  ├─ Google: Gemini 3-pro (thinking mode)
│  └─ Mistral: Magistral Medium 1.2 (temperature 0.3)
├─ Balanced (speed + quality)
│  ├─ Anthropic: Sonnet 4.6 + extended thinking (effort=medium)
│  ├─ OpenAI: GPT-5.1 + reasoning_effort (medium)
│  ├─ Google: Gemini 3-flash (faster, still capable)
│  └─ Mistral: Devstral 2 (temperature 0.3, tool use)
├─ Cost-Sensitive
│  ├─ Anthropic: Haiku 4.5 (thinking mode, effort=low)
│  ├─ OpenAI: GPT-5-mini + reasoning_effort (low)
│  ├─ Google: Gemini 3-flash-lite ($0.125/1M)
│  └─ Mistral: Mistral Small 3.2 ($0.3/1M, temperature 0.2)
├─ Temperature Tuning Required (exploration, hypothesis generation)
│  ├─ Mistral: Mistral Large 3 or Medium 3.1 (temperature 0.5-0.7)
│  ├─ Local: magistral:24b or gpt-oss:20b (temperature 0.5)
│  └─ Note: Frontier models use thinking/effort, not temperature
└─ Local Deployment
   ├─ Ollama Cloud: devstral-2:123b-cloud OR gemini-3-flash-preview:cloud
   └─ Self-hosted: gpt-oss:20b OR magistral:24b
```

### For Analysis & Research (Long Context)

```markdown
Task: Document analysis, synthesis, literature review, long context
├─ Massive Context (1M tokens)
│  ├─ Google: Gemini 2.5-pro (thinking mode, $10-15/1M)
│  ├─ Google: Gemini 3-pro (thinking mode, $12-18/1M)
│  └─ Google: Gemini 2.5-flash-lite ($0.40/1M, lightweight)
├─ Large Context (200k tokens)
│  ├─ Anthropic: Opus 4.6 + adaptive thinking (effort=high)
│  ├─ OpenAI: GPT-5.2 + reasoning_effort (context limited to 400k)
│  └─ Mistral: Mistral Large 3 (131k context, temperature 0.3)
├─ Distributed Analysis (multiple docs)
│  ├─ Anthropic: Sonnet 4.6 (cost-effective at 200k context)
│  ├─ Mistral: Devstral 2 (coding + analysis, 131k)
│  └─ Local: magistral:24b (131k context, temperature 0.5)
└─ Interactive Exploration
   ├─ Mistral: Devstral 2 or Medium 3.1 (temperature tunable)
   └─ Local: devstral-small-2:24b (temperature 0.2)
```

---

## Preset Design Guidelines

Based on parameter support matrix:

**For Claude/OpenAI Reasoning/Gemini Models:**

- **Simple tasks:** Use default thinking/effort settings
- **Moderate tasks:** Increase `effort` parameter (low → medium)
- **Complex tasks:** Set `effort` to high
- **Never adjust temperature** — let thinking/effort control complexity

**For Mistral Models:**

- **Simple tasks:** Temperature 0.3, Top P 0.5
- **Moderate tasks:** Temperature 0.7, Top P 0.7
- **Complex tasks:** Temperature 0.9, Top P 0.8
- **Exploration:** Temperature 1.0-1.2, Top P 0.8

**For Local Models:**

- **Simple/deterministic:** Temperature 0.1-0.3
- **Moderate:** Temperature 0.5-0.7
- **Exploration:** Temperature 0.7-1.0
- **Device-specific:** See model table for overrides (devstral-small-2 at ≤0.15)

---

## Prompt Caching: Provider Comparison

**Provider Support Summary**:

- **OpenAI**: Explicit caching (batch API + prompt caching with 10% discount on input)
- **Anthropic**: Explicit caching (cache writes for 5m/1h duration + cache hits at ~10% of input cost)
- **Google**: Explicit caching (cached input discount + cache storage cost per hour for text/image/video)
- **Mistral**: No caching support
- **Ollama**: No caching support

OpenAI, Anthropic, and Google all offer explicit caching pricing with different models. If your workflow requires control over caching and cost tracking, carefully evaluate which provider offers better economics.

### OpenAI: Input Discount Model (10% of regular cost)

Example: GPT-5.2 analyzing same 200k token codebase across 5 agent steps

```bash
Without caching (5 requests × 201k tokens):
  Cost = 5 × (201k / 1M) × $25 = $25.13

With 5m caching (write once, hit 4 times):
  Write: (200k / 1M) × $25 + (1k / 1M) × $25 = $5.025
  Hits: 4 × [(200k / 1M) × $2.50 + (1k / 1M) × $25] = $2.10
  Total = $7.125

Savings: 72% reduction
```

### Anthropic: Write + Hit Model (Requires Multiple Reuses)

Example: Claude Opus 4.6 with same scenario, 1h cache duration

```bash
Without caching (5 requests × 201k tokens):
  Cost = 5 × (201k / 1M) × $5 = $5.025

With 1h caching (write once, hit 4 times):
  Write: (200k / 1M) × $10 + (1k / 1M) × $5 = $2.005
  Hits: 4 × [(200k / 1M) × $0.50 + (1k / 1M) × $5] = $0.42
  Total = $2.425

Savings: 52% reduction
```

### When to Use Each

**OpenAI caching:** Multi-step agentic workflows where same large context is reused. Favorable breakeven on second request.

**Anthropic caching:** Long sessions (1h) with 20+ cache hits where the write cost is amortized across many requests. Evaluate ROI carefully.

**Skip caching:** Single-run workflows, testing, or when context < 50k tokens.

---

## Important Pricing Considerations

1. **Context-Aware Pricing:** Gemini models charge differently for >200k tokens
2. **Thinking Token Costs:** Claude and Gemini charge separately for thinking/reasoning tokens (in addition to output tokens)
3. **Input vs Output:** Most providers charge differently for input vs output. Calculate effective cost as: `(input_cost + output_cost) / 2`
4. **Rate Limits:** Free tier (Ollama) has monthly token limits and rate limiting
5. **Institutional Policies:** Some institutions restrict specific model origins. Check before deployment.

See official pricing pages:

- [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [OpenAI Pricing](https://openai.com/api/pricing)
- [Mistral Pricing](https://mistral.ai/pricing)
- [Google AI Studio Pricing](https://ai.google.dev/pricing)

---

## Parameter Support Matrix (Quick Reference)

| Provider | Model Family | Temperature | Top P | Thinking/Effort | Recommended Tuning |
|----------|---|---|---|---|---|
| **Anthropic** | All (Opus/Sonnet/Haiku) | ✗ Default only | ✗ Conflicts | ✓ Use `effort` parameter | Use thinking + effort |
| **OpenAI** | Reasoning (5.x, o3) | ✗ Not supported | ✗ | ✓ Use `reasoning_effort` | Use reasoning_effort |
| | Standard (4.1) | ✓ Tunable | ✓ Tunable | — | Use temperature + top_p |
| **Gemini** | All (3.x, 2.5) | ✗ Default only | ✗ | ✓ Use thinking mode | Use thinking mode only |
| **Mistral** | All models | ✓ Tunable | ✓ Tunable | — | Use temperature + top_p (fix one, adjust other) |
| **Ollama** | Cloud models | ✓ Varies | ✓ Varies | ✓ Where available | Check model-specific |
| **Local** | Self-hosted | ✓ Tunable | ✓ Tunable | — | Use temperature (check device limits) |

---

## Model Deprecation & Migration Path

| Old Model | New Model | Reason | Action Required |
|-----------|-----------|--------|-----------------|
| claude-opus-4-1-20250805 | claude-opus-4-6 | $75→$25/MTok, better performance | **Migrate immediately** |
| claude-sonnet-4-5-20250929 | claude-sonnet-4-6 | Same price, better performance, adaptive thinking | Migrate before Sep 29 |
| claude-haiku-3-20240307 | claude-haiku-4-5-20251001 | EOL Mar 7, 2025 | **URGENT: Migrate** |
| GPT-5.1 | GPT-5.2 | Same reasoning support, better outputs | Recommend migration |
| Gemini 1.5 | Gemini 2.5 / 3.x | Better performance, cheaper | Recommend migration |

---

## Implementation Notes for Presets

1. **Frontier Models (Claude, OpenAI reasoning, Gemini):** Presets control complexity via `thinking`/`effort`, NOT temperature.
2. **Mistral Models:** Presets vary temperature/top_p by complexity tier.
3. **Local Models:** Presets respect device-specific temperature limits.
4. **Configuration:** Users can override preset parameters at workflow level.
5. **Cost Estimation:** Use average of input + output pricing, accounting for thinking token overhead.

---

*Reference compiled 2026-02-19 from official provider documentation.*
*Update frequency: Monthly (or when major model releases occur)*
*Next review: March 2026 (or when Gemini 3.5 is released)*
