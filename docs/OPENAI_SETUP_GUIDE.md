# OpenAI Authentication Setup Guide

This guide covers setting up OpenAI authentication for the MCP server, supporting both ChatGPT subscription tokens and API keys.

## Overview

The OpenAI MCP server supports **dual authentication modes**:

| Mode | Source | Use Case | Setup |
|------|--------|----------|-------|
| **Subscription Mode** | ChatGPT Plus/Pro OAuth tokens | ChatGPT subscribers | Run `codex login` |
| **API Key Mode** | OpenAI API key | Developers, API access | Set `OPENAI_API_KEY` env var |

The server prefers subscription mode if available, falling back to API key mode automatically.

## Quick Start (API Key Mode - Easiest)

1. Get an API key from <https://platform.openai.com/api-keys>
2. Save to `.env`:

 ```bash
 echo "OPENAI_API_KEY=sk-proj-your-key-here" >> <your-hillstar-repo>/.env
 ```

1. Start the server:

 ```bash
 cd <your-hillstar-repo>/mcp-server
 python openai_mcp_server.py
 ```

## Setup Mode A: ChatGPT Subscription (Recommended for Subscribers)

### Prerequisites

- ChatGPT Plus or Pro subscription
- Codex CLI installed (`pip install codex-cli` or similar)
- Claude Code/Codex authentication

### Step 1: Create CODEX_HOME Directory

```bash
mkdir -p ~/.config/openai/codex-home
chmod 700 ~/.config/openai/codex-home
```

### Step 2: Run `codex login`

```bash
codex login
```

This opens a browser for ChatGPT OAuth sign-in. Once authenticated:

- `~/.config/openai/codex-home/auth.json` is created with tokens
- `~/.config/openai/codex-home/config.toml` stores Codex configuration

### Step 3: Verify Token Extraction

Check that the token was saved correctly:

```bash
python3 -c "
import json
from pathlib import Path

auth_file = Path.home() / '.config/openai/codex-home/auth.json'
with open(auth_file) as f:
 data = json.load(f)
 token = data.get('tokens', {}).get('access_token')
 print(f'Token found: {bool(token)}')
 print(f'Auth mode: {data.get(\"auth_mode\")}')"
```

Expected output:

```python
Token found: True
Auth mode: chatgpt
```

### Step 4: Enable Subscription Mode

Set environment variable to enable subscription token mode:

```bash
export OPENAI_CHATGPT_LOGIN_MODE=true
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:

```bash
echo 'export OPENAI_CHATGPT_LOGIN_MODE=true' >> ~/.bashrc
source ~/.bashrc
```

### Step 5: Start the Server

```bash
cd <your-hillstar-repo>/mcp-server
python openai_mcp_server.py
```

Server logs should show:

```text
Using ChatGPT subscription token (codex CLI) authentication
OpenAI MCP server initialized in subscription token mode
```

## Setup Mode B: API Key (Direct OpenAI API)

### Prerequisites

- OpenAI account (free or paid)
- API key from <https://platform.openai.com/api-keys>

### Step 1: Create or Get API Key

1. Visit <https://platform.openai.com/api-keys>
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-`)

**Warning**: Never commit API keys to git. Use `.env` files.

### Step 2: Set Environment Variable

Option A - Temporary (current session only):

```bash
export OPENAI_API_KEY=sk-proj-your-key-here
```

Option B - Persistent (add to `.env`):

```bash
echo "OPENAI_API_KEY=sk-proj-your-key-here" >> <your-hillstar-repo>/.env
```

### Step 3: Start the Server

```bash
cd <your-hillstar-repo>/mcp-server
python openai_mcp_server.py
```

Server logs should show:

```python
OpenAI MCP server initialized in API key mode
```

## Switching Between Modes

### From API Key to Subscription

1. Run `codex login` if not already done
2. Set environment variable:

 ```bash
 export OPENAI_CHATGPT_LOGIN_MODE=true
 ```

1. Restart the MCP server

### From Subscription to API Key

1. Unset or disable the subscription mode flag:

 ```bash
 unset OPENAI_CHATGPT_LOGIN_MODE
 ```

 Or set it to false:

 ```bash
 export OPENAI_CHATGPT_LOGIN_MODE=false
 ```

1. Ensure `OPENAI_API_KEY` is set
2. Restart the MCP server

## Environment Variables Summary

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `OPENAI_CHATGPT_LOGIN_MODE` | Enable subscription token mode | No | `false` |
| `OPENAI_API_KEY` | OpenAI API key (API key mode) | If not subscription | — |
| `CODEX_HOME` | Location of Codex auth directory | No | `~/.config/openai/codex-home` |
| `MODEL_DEFAULT` | Default model if not specified | No | `gpt-5.2` |

## Supported Models

### Standard Models

- `gpt-5.2-pro` - Latest, highest quality
- `gpt-5.2` - Fast flagship (recommended)
- `gpt-5-mini` - Cost-optimized
- `gpt-5-nano` - Minimal, lowest cost

### Reasoning Models

- `o3` - Advanced reasoning
- `o3-mini` - Lightweight reasoning

### Legacy

- `gpt-4o` - Previous generation
- `gpt-4-turbo` - Older

## Troubleshooting

### Error: "OPENAI_API_KEY not set and ChatGPT subscription token unavailable"

**Solution**: Set up one of the authentication modes:

- API Key: `export OPENAI_API_KEY=sk-proj-...`
- Subscription: Run `codex login` and set `export OPENAI_CHATGPT_LOGIN_MODE=true`

### Error: "Subscription token not found in any location"

**Solution**: Run `codex login` first:

```bash
codex login
```

Check token extraction:

```bash
python3 -c "from pathlib import Path; print((Path.home() / '.config/openai/codex-home/auth.json').exists())"
```

### Error: "codex CLI not found"

**Solution**: Install Codex CLI:

```bash
pip install codex-cli
```

Or verify it's in PATH:

```bash
which codex
```

### Codex Exec Takes Too Long

The MCP server allows up to 60 seconds for codex CLI commands. If commands consistently timeout:

- Check network connectivity
- Verify codex CLI is properly installed
- Try running directly: `codex exec --model gpt-5.2 "echo test"`

### Token Expired (Subscription Mode)

Subscription tokens auto-refresh, but if you see authentication errors:

1. Run `codex login` again
2. Restart the MCP server

The new token will be automatically extracted and used.

## Testing Connectivity

Run the E2E connectivity test to verify setup:

```bash
cd <your-hillstar-repo>
pytest tests/test_e2e_connectivity.py::TestConnectivityPing::test_openai_subscription_token_connectivity -v
# or for API key mode:
pytest tests/test_e2e_connectivity.py::TestConnectivityPing::test_openai_apikey_connectivity -v
```

## Integration with Workflows

Once configured, the MCP server will:

1. Automatically detect the authentication mode
2. Select appropriate execution method (codex CLI or direct API)
3. Handle errors and timeouts gracefully

Example workflow node:

```json
{
 "task": "Analyze this data: {{data}}",
 "provider": "openai",
 "model": "gpt-5.2"
}
```

The server handles authentication transparently.

## Security Considerations

### API Keys

- Never commit to git (use `.env` and `.gitignore`)
- Rotate regularly at <https://platform.openai.com/api-keys>
- Limit permissions to API-only in OpenAI dashboard

### Subscription Tokens (OAuth)

- Stored securely in `~/.config/openai/codex-home/auth.json`
- Auto-refresh via Codex infrastructure
- More secure than API keys for long-running processes

## References

- OpenAI API Documentation: <https://platform.openai.com/docs>
- Codex CLI: <https://github.com/example/codex-cli>
- MCP Server Code: `<your-hillstar-repo>/mcp-server/openai_mcp_server.py`

---

**Last Updated**: 2026-02-24
**Version**: 1.0
