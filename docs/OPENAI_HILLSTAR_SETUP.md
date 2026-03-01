# OpenAI with Hillstar v1.0.0

Complete guide to setting up OpenAI authentication across both the Hillstar project layer and the Claude infrastructure layer.

## Overview

The OpenAI MCP server supports **dual authentication modes**:

| Mode | Source | Use Case | Setup |
|------|--------|----------|-------|
| **Subscription Mode** | ChatGPT Plus/Pro OAuth tokens | ChatGPT subscribers | Run `codex login` |
| **API Key Mode** | OpenAI API key | Developers, API access | Set `OPENAI_API_KEY` env var |

The server prefers subscription mode if available, falling back to API key mode automatically.

**Scope**: Subscription token support (CODEX_HOME) applies **exclusively to OpenAI**:

- **OpenAI**: Supports CODEX_HOME (subscription tokens) + OPENAI_API_KEY (fallback)
- **Anthropic**: API key only (ANTHROPIC_API_KEY)
- **Mistral**: API key only (MISTRAL_API_KEY)
- **Google**: API key only (GOOGLE_API_KEY)

---

## Quick Start (API Key Mode - Easiest)

### Step 1: Get API Key

1. Visit <https://platform.openai.com/api-keys>
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-`)

### Step 2: Store API Key Securely

**Note**: You can use `.env` files, but we suggest you use your OS keyring for better security (see below).

### **Recommended: OS Keyring (via Setup Wizard)**

Use Hillstar's setup wizard to store credentials securely in your system keyring:

```bash
cd <your-hillstar-repo>
hillstar config
```

#### Automatic Credential Discovery

The setup wizard will **automatically search your system keyring** for existing OpenAI credentials:

1. **Discovery Phase**: Scans system keyring for credentials matching `sk-proj-*` pattern
2. **If credentials found**: Shows a numbered list of discovered credentials
   - Select an existing credential to use it
   - Choose "Enter new key" to add a fresh credential
   - Choose "Skip" to proceed without OpenAI setup
3. **If no credentials found**: Prompts you to paste a new API key (input is masked for security)
4. **Storage**: Key is securely stored in your system keyring

#### Supported Platforms

- **macOS**: Keychain (native)
- **Linux**: Secret Service or pass utility
- **Windows**: Credential Manager (native)

### **Alternative: Environment Variable (Temporary Session)**

If you prefer not to use keyring, set as environment variable:

```bash
export OPENAI_API_KEY=sk-proj-your-key-here
```

### **Legacy: .env File (Least Secure, Use with Caution)**

For development only, you can store in `.env` file:

```bash
echo "OPENAI_API_KEY=sk-proj-your-key-here" >> <your-hillstar-repo>/.env
```

Warning: `.env` files are less secure. Hillstar's setup process recommends using OS keyring instead.

---

## Keyring Auto-Discovery Feature

When you run `hillstar config`, the setup wizard uses **intelligent credential discovery** to find and reuse existing OpenAI keys stored in your system keyring. This feature makes it easier to manage credentials without re-entering them each time.

### How It Works

1. **Automatic Scanning**: When you select OpenAI (or any cloud provider), the wizard scans your system keyring for stored credentials
2. **Pattern Matching**: Credentials are validated to ensure they match the expected format (e.g., `sk-proj-*` for OpenAI API keys)
3. **User Choice**: You're presented with options:
   - **Use existing credential** - Select from found credentials (shown with masked display for security)
   - **Enter new key** - Add a fresh API key
   - **Skip** - Proceed without setting up this provider
4. **Secure Storage**: Your choice is stored securely in your system keyring for future use

### Example Workflow

```bash
$ hillstar config

CloudAI Provider Setup
======================
Found existing OpenAI credentials:
  1. sk-proj-abc123def456... (from keyring)
  2. sk-proj-xyz789uvw101... (from keyring)

Select credential to use (1-2), enter new, or skip [1]: 1
Using credential from system keyring
```

### Benefits

- **Non-destructive**: Existing credentials are discovered, not deleted
- **User-controlled**: You decide which credential to use
- **Secure**: Credentials are masked in output, never printed in full
- **Time-saving**: No need to re-enter keys you've already stored

### Opting Out

If you prefer to skip auto-discovery for a provider, simply select "Skip" when prompted. The wizard will not store credentials for that provider.

---

## Setup Mode A: ChatGPT Subscription (Recommended for Subscribers)

### Prerequisites

- ChatGPT Plus or Pro subscription
- Codex CLI installed (`pip install codex-cli` or similar)

### Project Layer Setup (Hillstar)

#### Step 1: Create CODEX_HOME Directory

```bash
mkdir -p ~/.config/openai/codex-home
chmod 700 ~/.config/openai/codex-home
```

This is the canonical location where Codex stores authentication state.

#### Step 2: Run `codex login`

```bash
codex login
```

This opens a browser for ChatGPT OAuth sign-in. Once authenticated:

- `~/.config/openai/codex-home/auth.json` is created with tokens
- `~/.config/openai/codex-home/config.toml` stores Codex configuration

#### Step 3: Verify Token Extraction

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

```text
Token found: True
Auth mode: chatgpt
```

#### Step 4: Enable Subscription Mode in Hillstar

Set environment variable to enable subscription token mode:

```bash
export OPENAI_CHATGPT_LOGIN_MODE=true
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:

```bash
echo 'export OPENAI_CHATGPT_LOGIN_MODE=true' >> ~/.bashrc
source ~/.bashrc
```

#### Step 5: Start the Hillstar MCP Server

```bash
cd <your-hillstar-repo>/mcp-server
python openai_mcp_server.py
```

Server logs should show:

```text
Using ChatGPT subscription token (codex CLI) authentication
OpenAI MCP server initialized in subscription token mode
```

### Claude Infrastructure Layer Setup (Optional)

If you want Claude Code to use subscription mode, configure the global MCP config:

#### Step 1: Set Canonical Codex Home

Use one canonical Codex state directory in `~/.config/claude/mcp_config.json`:

```bash
export CODEX_HOME=~/.config/openai/codex-home
```

#### Step 2: Configure MCP Servers

In `~/.config/claude/mcp_config.json`, ensure servers that run Codex include:

```json
"env": {
    "CODEX_HOME": "~/.config/openai/codex-home"
}
```

Recommended server layout:

```json
{
  "mcpServers": {
    "codex-subscription": {
      "command": "codex",
      "args": ["mcp-server", "--sandbox", "read-only"],
      "env": {
        "CODEX_HOME": "~/.config/openai/codex-home",
        "AUTH_MODE": "subscription"
      }
    },
    "codex-api": {
      "command": "bash",
      "args": [
        "-lc",
        "set -a; source <your-hillstar-repo>/.env; set +a; export CODEX_HOME=~/.config/openai/codex-home; exec codex mcp-server --sandbox read-only"
      ],
      "env": {
        "AUTH_MODE": "api_key"
      }
    }
  }
}
```

#### Step 3: Set File Permissions

```bash
chmod 600 ~/.config/openai/codex-home/auth.json
```

---

## Switching Between Modes

### From API Key to Subscription

1. Run `codex login` if not already done
2. Set environment variable:

   ```bash
   export OPENAI_CHATGPT_LOGIN_MODE=true
   ```

3. Restart the MCP server

### From Subscription to API Key

1. Unset or disable the subscription mode flag:

   ```bash
   unset OPENAI_CHATGPT_LOGIN_MODE
   ```

   Or set it to false:

   ```bash
   export OPENAI_CHATGPT_LOGIN_MODE=false
   ```

2. Ensure `OPENAI_API_KEY` is set
3. Restart the MCP server

### Fast Switch Checklist

**Subscription mode:**

- `CODEX_HOME` set and auth.json populated (run `codex login`)
- `OPENAI_CHATGPT_LOGIN_MODE=true` exported
- Hillstar MCP server restarted

**API key mode:**

- `OPENAI_API_KEY` present in `.env`
- `OPENAI_CHATGPT_LOGIN_MODE` unset or false
- Hillstar MCP server restarted

---

## Environment Variables Summary

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `OPENAI_CHATGPT_LOGIN_MODE` | Enable subscription token mode | No | `false` |
| `OPENAI_API_KEY` | OpenAI API key (API key mode) | If not subscription | — |
| `CODEX_HOME` | Location of Codex auth directory | No | `~/.config/openai/codex-home` |
| `MODEL_DEFAULT` | Default model if not specified | No | `gpt-5.2` |

---

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

---

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

---

## Testing Connectivity

Run the E2E connectivity test to verify setup:

```bash
cd <your-hillstar-repo>
pytest tests/test_e2e_connectivity.py::TestConnectivityPing::test_openai_subscription_token_connectivity -v
# or for API key mode:
pytest tests/test_e2e_connectivity.py::TestConnectivityPing::test_openai_apikey_connectivity -v
```

---

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

---

## Security Considerations

### API Keys

- Never commit to git (use `.env` and `.gitignore`)
- Rotate regularly at <https://platform.openai.com/api-keys>
- Limit permissions to API-only in OpenAI dashboard

### Subscription Tokens (OAuth)

- Stored securely in `~/.config/openai/codex-home/auth.json`
- Auto-refresh via Codex infrastructure
- More secure than API keys for long-running processes

---

## References

- OpenAI API Documentation: <https://platform.openai.com/docs>
- Codex CLI: <https://github.com/example/codex-cli>
- MCP Server Code: `<your-hillstar-repo>/mcp-server/openai_mcp_server.py`

---

**Last Updated**: 2026-02-28
**Version**: 1.0.0
**Project**: Hillstar v1.0.0 (Production Release)
