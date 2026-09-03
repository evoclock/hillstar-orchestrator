# Hillstar Setup Guide

Complete instructions for configuring each LLM provider.

## Quick Setup

```bash
# Interactive setup wizard (recommended - uses secure keyring storage)
hillstar wizard

# Or set environment variables (CI/CD or temporary use)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-proj-..."
export MISTRAL_API_KEY="..."
```

---

## Cloud Providers

### Anthropic (Claude)

**Get API Key:**

1. Visit <https://console.anthropic.com>
2. Sign up or log in
3. Navigate to API Keys
4. Create new key, copy it

**Configure:**

```bash
# Option 1: Setup wizard (recommended - uses secure keyring storage)
hillstar wizard

# Option 2: Environment variable (for CI/CD or temporary use)
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Verify:**

```bash
hillstar presets  # Should list Claude models
```

**Model Options:**

Any current Claude model identifier — see
https://docs.anthropic.com/en/docs/about-claude/models. No list is kept here.

**Important:** Use `effort` parameter ("low", "medium", "high") for reasoning control, not temperature. Do not adjust temperature with Claude models.

---

### OpenAI (GPT)

**Get API Key:**

1. Visit <https://platform.openai.com/api-keys>
2. Sign up or log in
3. Create new secret key
4. Copy immediately (won't be shown again)

**Configure:**

```bash
# Option 1: Setup wizard (recommended - uses secure keyring storage)
hillstar wizard

# Option 2: Environment variable (for CI/CD or temporary use)
export OPENAI_API_KEY="sk-proj-..."
```

**Model Options:**

Any current OpenAI model identifier — see
https://platform.openai.com/docs/models. No list is kept here.

**Important:** Reasoning model families do not support temperature. Use
`reasoning_effort` ("low", "medium", "high") instead.

**Verify:**

```bash
hillstar presets  # Should list GPT models
```

---

### Mistral

**Get API Key:**

1. Visit <https://console.mistral.ai/api-keys>
2. Create new key
3. Copy it

**Configure:**

```bash
# Option 1: Setup wizard (recommended - uses secure keyring storage)
hillstar wizard

# Option 2: Environment variable (for CI/CD or temporary use)
export MISTRAL_API_KEY="your-api-key"
```

**Model Options:**

No model list is maintained here — see https://docs.mistral.ai/getting-started/models
for the current catalog.

**Parameter Support:** Mistral fully supports temperature and top_p tuning. Recommended: fix temperature, then adjust top_p for exploration.

---

### Google Gemini

**Get API Key:**

1. Visit <https://ai.google.dev>
2. Click "Get API key"
3. Create new key for free tier
4. Copy it

**Configure:**

```bash
# Option 1: Setup wizard (recommended - uses secure keyring storage)
hillstar wizard

# Option 2: Environment variable (for CI/CD or temporary use)
export GOOGLE_API_KEY="AIza..."
```

**Model Options:**

Any current Gemini model identifier — see
https://ai.google.dev/gemini-api/docs/models. No list is kept here.

**Important:** Keep temperature at default (1.0). Changing temperature causes performance degradation on reasoning tasks. Use thinking mode for complex problems.

---

## Local Models

### Ollama (Recommended for local testing)

**Install:**

```bash
# macOS or Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or visit https://ollama.ai for Windows/Docker
```

**Start Ollama Server:**

```bash
# In one terminal
ollama serve

# In another terminal, pull a model
ollama pull mistral
ollama pull neural-chat
```

**Configure Hillstar:**

```bash
# Ollama runs on localhost:11434 by default
# No API key needed

# Verify available models
hillstar presets  # Should show ollama provider
```

Hillstar can call Ollama directly over its HTTP API (the `ollama`
provider) in addition to the MCP path; both use `http://127.0.0.1:11434`
by default and need no API key.

**Available Models (via ollama pull):**

See https://ollama.com/library for the current catalog. Any pulled model
works through the `ollama` provider or the OpenAI-compatible `local` provider.

---

### llama.cpp (For C++ performance)

**Install:**

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make
```

**Run Server:**

```bash
./server -m /path/to/model.gguf -ngl 99
# -ngl 99: Offload layers to GPU (adjust based on your GPU)
```

**Configure Hillstar:**
Edit `~/.hillstar/provider_registry.json`:

```json
{
  "providers": {
    "local": {
      "endpoint": "http://localhost:8000",
      "type": "llamacpp"
    }
  }
}
```

---

### Generic local servers (GPU optional)

Hillstar no longer ships hard-coded local model providers (the old
Devstral/Jan-Code models are removed). Use the generic `local` provider with
any OpenAI-compatible server — vLLM, llama.cpp server, LM Studio, Ollama:

**Setup (vLLM example):**

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model "<your-model>" \
  --port 8080
```

**Configure Hillstar** (workflow `model_config` or provider registry):

```json
{
  "custom_providers": {
    "local": {
      "endpoint": "http://localhost:8080",
      "model_name": "<your-model>"
    }
  }
}
```

Local execution is optional and generally not recommended; hosted providers
(e.g. OpenAI) are simpler and reproducible. See `models/local_model.py`.

---

## Using the Setup Wizard

**Interactive Configuration (Recommended):**

```bash
hillstar wizard
```

This guides you through:

1. Selecting cloud and local providers to configure
2. Storing API keys securely in your OS keyring (macOS Keychain, Linux Secret Service, Windows Credential Manager)
3. Auto-discovering credentials already stored in your keyring
4. Loading keys from `.env` files as an alternative method
5. Verifying provider connectivity

---

## Verify Installation

```bash
# List available providers
hillstar presets

# Test a provider
hillstar enforce check

# Run example workflow
hillstar execute workflow.json
```

---

## Resilience and Retries

Hillstar automatically retries transient provider failures during node
execution. The policy is fixed and needs no configuration:

- Up to 3 retries per node (4 attempts total).
- Backoff between attempts: 30s, then 60s, then 120s.
- Retried on HTTP 500, 502, 503, and 429, and on transient network errors
  (timeouts, connection resets, broken pipes, temporary failures).

Errors that are not transient (for example quota exhaustion, context-length
overflow, or provider overload) are not retried on the same provider;
instead the configured provider fallback chain is tried. When a model is
pinned in `explicit` mode the fallback chain is disabled, so only the
single provider is retried.

Hillstar does not perform cost estimation or budget enforcement; check your
provider's usage dashboard for spend.

---

## Troubleshooting

### **"Connection refused"**

- Local model server not running (Ollama, llama.cpp)
- Check port: `lsof -i :11434` (Ollama default) or `netstat -an | rg 11434`

### **"Authentication failed"**

- API key not set correctly
- Wrong environment variable name
- Key has insufficient permissions

### **"Rate limited"**

- Too many requests to API
- Use workflow presets with lower tiers
- Or switch to local models

---

## Security Notes

- API keys are stored in your OS keyring, never in plaintext config files
- API keys are never embedded in workflows
- Environment variables are supported for CI/CD or temporary use
- Git ignores credential files (.gitignore)
- Hillstar automatically redacts credentials from error messages and logs (24 pattern types)
- Audit logging captures all model calls

---

*Version: 1.2.0 · Last updated: 2026-09-03*
