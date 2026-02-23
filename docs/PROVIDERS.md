# Provider Registry and Capabilities

This document describes all supported LLM providers, their models, capabilities, and costs.

---

## Provider Summary

| Provider | Models | Type | Cost | Setup |
|----------|--------|------|------|-------|
| Anthropic | Claude family | API | Paid | API key |
| OpenAI | GPT family | API | Paid | API key |
| Mistral | Mistral family | API | Paid | API key |
| Google AI Studio | Gemini family | API | Free tier | API key |
| Ollama | Local models | Local | Free | Local binary |
| Devstral Local | Devstral 24B | Local | Free | Local deployment |

---

## Anthropic

### Overview
Claude models from Anthropic. Best for complex reasoning, code generation, and analysis.

### Available Models

Claude Opus 4.6:
- Role: Best overall performance, reasoning, and knowledge
- Context Window: 200,000 tokens
- Cost: $5/MTok input, $25/MTok output
- Use Case: Complex analysis, research, decision-making

Claude Sonnet 4.6:
- Role: Balanced speed and intelligence
- Context Window: 200,000 tokens
- Cost: $3/MTok input, $15/MTok output
- Use Case: General purpose workflows, faster turnaround

Claude Haiku 4.5:
- Role: Fast and cost-effective
- Context Window: 100,000 tokens
- Cost: $1/MTok input, $5/MTok output
- Use Case: Simple tasks, high throughput, cost-sensitive

### Setup

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Configuration

```json
{
  "anthropic": {
    "api_key": "sk-ant-...",
    "models": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
  }
}
```

### Usage Example

```json
{
  "type": "model_call",
  "provider": "anthropic",
  "model": "claude-opus-4-6",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

---

## OpenAI

### Overview
GPT models from OpenAI. Strong in general-purpose tasks and instruction following.

### Available Models

GPT-5.2-Pro:
- Role: Frontier model, newest capabilities
- Context Window: 200,000 tokens
- Cost: $40/MTok input, $160/MTok output
- Use Case: Cutting-edge applications

GPT-5.2:
- Role: Latest, good balance
- Context Window: 200,000 tokens
- Cost: $2.50/MTok input, $10/MTok output
- Use Case: General purpose, recommended

GPT-5.1:
- Role: Stable, widely used
- Context Window: 200,000 tokens
- Cost: $2/MTok input, $10/MTok output
- Use Case: Production workflows

GPT-5-Mini:
- Role: Fast, efficient
- Context Window: 200,000 tokens
- Cost: $0.15/MTok input, $0.60/MTok output
- Use Case: High volume, latency-sensitive

GPT-5-Nano:
- Role: Smallest, fastest
- Context Window: 200,000 tokens
- Cost: $0.03/MTok input, $0.12/MTok output
- Use Case: Simple classification, extraction

O3 / O3-Mini:
- Role: Reasoning models
- Context Window: Varies
- Cost: Higher than standard models
- Use Case: Complex problem solving, math, logic

### Setup

```bash
export OPENAI_API_KEY="sk-proj-..."
```

### Configuration

```json
{
  "openai": {
    "api_key": "sk-proj-...",
    "models": ["gpt-5.2-pro", "gpt-5.2", "gpt-5-mini", "o3"]
  }
}
```

### Usage Example

```json
{
  "type": "model_call",
  "provider": "openai",
  "model": "gpt-5.2",
  "parameters": {
    "temperature": 0.5,
    "max_tokens": 1000
  }
}
```

---

## Mistral

### Overview
Mistral models. Strong reasoning, multilingual support, efficient.

### Available Models

Mistral Large 2411:
- Role: Frontier reasoning model
- Context Window: 128,000 tokens
- Cost: $2/MTok input, $6/MTok output
- Use Case: Complex reasoning, code

Mistral Medium 3.1:
- Role: Balanced performance
- Context Window: 128,000 tokens
- Cost: $0.27/MTok input, $0.81/MTok output
- Use Case: General purpose

Ministral 8B / 3B:
- Role: Small, fast, efficient
- Context Window: 128,000 tokens
- Cost: $0.14/MTok input, $0.42/MTok output
- Use Case: Edge deployment, latency-critical

Codestral:
- Role: Code generation specialist
- Context Window: 80,000 tokens
- Cost: Varies
- Use Case: Code generation, analysis

Devstral 2:
- Role: Developer-focused reasoning
- Context Window: 128,000 tokens
- Cost: $0.20/MTok input, $0.60/MTok output
- Use Case: Development workflows, debugging

### Setup

```bash
export MISTRAL_API_KEY="..."
```

### Configuration

```json
{
  "mistral": {
    "api_key": "...",
    "models": ["mistral-large-2411", "mistral-medium-3.1", "devstral-2"]
  }
}
```

---

## Google AI Studio

### Overview
Gemini models from Google. Free tier available, good for prototyping.

### Available Models

Gemini 3-Pro:
- Role: Latest reasoning model
- Context Window: 1,000,000 tokens
- Cost: Free tier + paid options
- Use Case: Research, large document analysis

Gemini 3-Flash:
- Role: Fast, efficient reasoning
- Context Window: 1,000,000 tokens
- Cost: Free tier + paid options
- Use Case: Interactive applications

Gemini 3-Flash-Lite:
- Role: Lightweight, very fast
- Context Window: Large
- Cost: Free tier
- Use Case: Quick prototyping

Gemini 1.5-Pro/Flash:
- Role: Previous generation (still available)
- Context Window: 1,000,000 tokens
- Cost: Previous tier pricing
- Use Case: Legacy workflows

### Setup

```bash
export GOOGLE_API_KEY="..."
```

### Configuration

```json
{
  "google_ai_studio": {
    "api_key": "...",
    "models": ["gemini-3-pro", "gemini-3-flash"]
  }
}
```

---

## Ollama (Local)

### Overview
Run open-source models locally on your machine. No API key required.

### Supported Models

Devstral 2 (123B):
- Context: 16K tokens
- Memory: ~80GB VRAM
- Speed: 2-4 tokens/sec (GPU)
- Cost: Free (your compute)
- Use Case: Local reasoning, privacy-sensitive

Minimax M2.1 (Cloud proxy):
- Context: Large
- Memory: Varies
- Speed: API-limited
- Cost: Free (proxy)
- Use Case: Testing with local endpoints

GLM 4.7 (Cloud proxy):
- Context: Large
- Cost: Free (proxy)
- Use Case: Chinese language, local testing

Mistral, Neural Chat, Codeup:
- Various open-source models
- Community maintained
- Free to use locally
- Use Case: Research, prototyping

### Setup

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model
ollama pull devstral-2:latest
```

### Configuration

```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "models": ["devstral-2", "mistral", "neural-chat"]
  }
}
```

### Usage Example

```json
{
  "type": "model_call",
  "provider": "ollama",
  "model": "devstral-2",
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9
  }
}
```

### Benefits
- Privacy: Data never leaves your machine
- Cost: Zero API costs
- Control: Full control over model execution
- Testing: Fast local development

### Limitations
- Requires GPU for reasonable speed
- Large models need 40GB+ VRAM
- CPU-only is very slow
- No commercial support

---

## Devstral Local

### Overview
Devstral 24B model optimized for local deployment. Smaller than 123B version, faster inference.

### Model Details

Devstral 24B:
- Context: 16K tokens
- Memory: ~20GB VRAM
- Speed: 5-10 tokens/sec (GPU)
- Cost: Free
- Use Case: Developer workflows, local IDE integration

### Setup

```bash
# Using Ollama
ollama pull devstral:latest

# Or custom deployment via MCP server
# See MCP_SERVERS.md for details
```

### Configuration

```json
{
  "devstral_local": {
    "base_url": "http://localhost:8000",
    "models": ["devstral-24b"]
  }
}
```

---

## Cost Estimation

### Example Costs (2026-02-22)

Simple Classification (100 input, 50 output tokens):
- Claude Haiku: $0.14
- Claude Sonnet: $0.42
- Claude Opus: $2.10
- GPT-5-Nano: $0.006
- Mistral Medium: $0.04
- Gemini 3-Flash: Free tier
- Ollama/Local: Free

Complex Analysis (5000 input, 2000 output tokens):
- Claude Haiku: $7.00
- Claude Sonnet: $21.00
- Claude Opus: $105.00
- GPT-5.2: $12.50
- Mistral Large: $16.00
- Gemini 3-Pro: Free tier + overages
- Ollama/Local: Free

### Cost Optimization Strategies

1. Use smaller models for simple tasks
2. Use local models (Ollama) for sensitive data
3. Implement cost budgets and warnings
4. Use batch operations when possible
5. Monitor costs per workflow step
6. Consider provider fallback chains based on cost

---

## Provider Selection Strategy

### Recommended Fallback Chains

For Complex Reasoning:
1. Claude Opus 4.6 (best reasoning)
2. Claude Sonnet 4.5 (fallback)
3. GPT-5.2 (alternative)
4. Mistral Large (cost option)

For Code Generation:
1. Claude Opus 4.6 (strong code)
2. Codestral (code specialist)
3. GPT-5.2 (alternative)
4. Mistral Large (open alternative)

For Cost-Conscious:
1. GPT-5-Nano (cheapest)
2. Claude Haiku (good balance)
3. Mistral Medium (alternative)
4. Ollama/Local (free)

For Privacy-Sensitive:
1. Ollama/Local (private)
2. Devstral 24B (private)
3. No API calls
4. Full control over data

### Automatic Provider Detection

Hillstar detects:
- Ollama availability (via local port check)
- API key presence (config or environment)
- Provider capabilities (model list)
- Cost constraints (budget limits)

Configuration:

```json
{
  "provider_preference": "anthropic",
  "fallback_providers": ["openai", "mistral", "ollama"],
  "cost_budget": 10.00
}
```

---

## API Key Management

### Three-Tier Resolution

1. Configuration file (provider_config.json)
2. Environment variables
3. Error (no key found)

### Environment Variables

```bash
ANTHROPIC_API_KEY="sk-ant-..."
OPENAI_API_KEY="sk-proj-..."
MISTRAL_API_KEY="..."
GOOGLE_API_KEY="..."
OLLAMA_BASE_URL="http://localhost:11434"
```

### Never

- Commit API keys to version control
- Log API keys in output
- Share API keys in workflows
- Hard-code credentials in code

---

## Testing Providers

### Test Workflow with Each Provider

```json
{
  "metadata": {
    "name": "Test Provider",
    "description": "Verify provider connectivity"
  },
  "provider_config": {
    "provider": "anthropic",
    "tos_accepted": true,
    "audit_enabled": true
  },
  "nodes": [
    {
      "id": "test",
      "type": "model_call",
      "provider": "anthropic",
      "model": "claude-haiku-4-5",
      "input": {
        "prompt": "Say hello"
      }
    }
  ]
}
```

Run:
```bash
hillstar run test-provider.json
```

---

## FAQ

Q: Which provider should I use?
A: Start with Claude Opus for complex tasks, GPT-5-Nano for simple tasks, Ollama for privacy-sensitive data.

Q: Can I use multiple providers in one workflow?
A: Yes. Each node can specify a different provider.

Q: How do I handle provider outages?
A: Configure fallback chains. Hillstar tries next provider if one fails.

Q: Is my data secure with these providers?
A: Check each provider's privacy policy. For maximum security, use Ollama locally.

Q: Can I use Ollama offline?
A: Yes. Models must be pre-downloaded, then Ollama works without internet.

Q: How much does Ollama cost?
A: Free to use. Only costs are your compute (electricity, hardware).

---

**Document Status:** Sprint 1 Release
**Last Updated:** 2026-02-22
**Version:** 1.0.0-sprint1

See MCP_SERVERS.md for technical details on how providers are implemented.
