# Hillstar Setup Guide

Complete instructions for configuring each LLM provider.

## Quick Setup

```bash
# Interactive setup wizard (recommended for first-time users)
hillstar wizard

# Manual setup - set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export MISTRAL_API_KEY="..."
```

---

## Cloud Providers

### Anthropic (Claude)

**Get API Key:**
1. Visit https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys
4. Create new key, copy it

**Configure:**
```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: Setup wizard
hillstar wizard

# Option 3: Manual config file
mkdir -p ~/.hillstar
cat > ~/.hillstar/provider_registry.json << 'EOF'
{
  "providers": {
    "anthropic": {
      "api_key": "sk-ant-..."
    }
  }
}
EOF
```

**Verify:**
```bash
hillstar presets  # Should list Claude models
```

**Model Options:**
- `claude-opus-4-6` (best quality, most expensive)
- `claude-sonnet-4-5` (balanced)
- `claude-haiku-4-5` (fastest, cheapest)

**Important:** Cannot use `temperature` and `top_p` simultaneously. Use temperature only for deterministic outputs.

---

### OpenAI (GPT)

**Get API Key:**
1. Visit https://platform.openai.com/api-keys
2. Sign up or log in
3. Create new secret key
4. Copy immediately (won't be shown again)

**Configure:**
```bash
export OPENAI_API_KEY="sk-..."
```

**Model Options:**
- `gpt-5.2-pro` (best quality)
- `gpt-5.2` (balanced)
- `gpt-4o` (multimodal)
- `o3` / `o3-mini` (reasoning models - no temperature support)

**Important:** GPT-5 series do not support temperature parameter. Use `reasoning_effort` for o-series models instead.

**Verify:**
```bash
hillstar presets  # Should list GPT models
```

---

### Mistral

**Get API Key:**
1. Visit https://console.mistral.ai/api-keys
2. Create new key
3. Copy it

**Configure:**
```bash
export MISTRAL_API_KEY="..."
```

**Model Options:**
- `mistral-large-2411` (best quality)
- `mistral-medium-latest` (balanced)
- `codestral-2508` (coding-focused)

---

### Google Gemini

**Get API Key:**
1. Visit https://ai.google.dev
2. Click "Get API key"
3. Create new key for free tier
4. Copy it

**Configure:**
```bash
export GOOGLE_API_KEY="AIza..."
```

**Model Options:**
- `gemini-3-pro` (best quality)
- `gemini-3-flash` (fast)
- `gemini-1.5-pro` (legacy, still works)

**Important:** Gemini 3 models - keep temperature at default (1.0). Changing temperature causes performance degradation on reasoning tasks.

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

**Available Models (via ollama pull):**
- `mistral` - Fast, general purpose
- `neural-chat` - Conversational
- `devstral-2:123b-cloud` - Coding-focused (if available)
- `glm-4.7:cloud` - Multilingual

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

### Devstral Local (GPU Required)

**Requirements:**
- NVIDIA GPU with 16GB+ VRAM (for 24B model)
- CUDA toolkit installed

**Setup:**
```bash
# Using vLLM
pip install vllm

# Download model from HuggingFace
# Run locally on port 8080
python -m vllm.entrypoints.openai.api_server \
  --model "Devstral-small-2-24b-GGUF" \
  --port 8080
```

**Configure Hillstar:**
```bash
export DEVSTRAL_ENDPOINT="http://localhost:8080"
```

---

## Using the Setup Wizard

**Interactive Configuration (Recommended):**
```bash
hillstar wizard
```

This guides you through:
1. Testing each provider's connectivity
2. Saving valid credentials
3. Setting provider preferences
4. Verifying setup

---

## Verify Installation

```bash
# List available providers
hillstar presets

# Test a provider
hillstar enforce check

# Run example workflow
hillstar execute python/hillstar/tests/e2e/workflow.json
```

---

## Cost Estimation

Before running expensive models:

```bash
# Estimate cost in workflow.json
# Hillstar tracks:
# - Input tokens × input_price
# - Output tokens × output_price
# - Per-provider pricing from registry

# View estimated costs in trace output
rg "cost" .hillstar/
```

---

## Troubleshooting

**"Connection refused"**
- Local model server not running (Ollama, llama.cpp)
- Check port: `lsof -i :11434` (Ollama default) or `netstat -an | rg 11434`

**"Authentication failed"**
- API key not set correctly
- Wrong environment variable name
- Key has insufficient permissions

**"Rate limited"**
- Too many requests to API
- Use workflow presets with lower tiers
- Or switch to local models

---

## Security Notes

- ✅ API keys never embedded in workflows
- ✅ Store in environment variables or `~/.hillstar/provider_registry.json`
- ✅ Git ignores credential files (.gitignore)
- ✅ Hillstar redacts credentials from error messages
- ✅ Audit logging captures all model calls

