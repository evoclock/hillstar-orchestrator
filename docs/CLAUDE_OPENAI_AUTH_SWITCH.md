# Claude Handover: OpenAI Auth Mode Switch

This runbook covers OpenAI authentication at two layers:

1. **Global Claude layer** (`~/.config/claude/mcp_config.json`)
   - Switching between `codex-subscription` and `codex-api` MCP server entries
   - Managing Codex infrastructure and CODEX_HOME

2. **Project layer** (Hillstar code) - OpenAI Only
   - Hillstar's OpenAI MCP provider supports dual auth with subscription-first priority
   - Implemented in `models/openai_mcp_model.py` and `utils/openai_auth_resolver.py`
   - Auth resolution: CODEX_HOME/auth.json → OPENAI_API_KEY → error
   - Other providers (Anthropic, Mistral, Google) remain API-key only

## Scope: OpenAI Provider Only

Subscription token support (CODEX_HOME) applies exclusively to OpenAI MCP provider:

- OpenAI: Supports CODEX_HOME (subscription tokens) + OPENAI_API_KEY (fallback)
- Anthropic: API key only (ANTHROPIC_API_KEY)
- Mistral: API key only (MISTRAL_API_KEY)
- Google: API key only (GOOGLE_API_KEY)

## Canonical Codex Home

Use one canonical Codex state directory:

- `CODEX_HOME=/home/jgamboa/.config/openai/codex-home`

Codex auth state lives at:

- `/home/jgamboa/.config/openai/codex-home/auth.json`

## First-time bootstrap

```bash
mkdir -p ~/.config/openai/codex-home
chmod 700 ~/.config/openai/codex-home
```

## Required MCP config

In `~/.config/claude/mcp_config.json`, ensure servers that run Codex include:

```json
"env": {
  "CODEX_HOME": "/home/jgamboa/.config/openai/codex-home"
}
```

Recommended server layout:

- `mcpServers["codex-subscription"]`
- `mcpServers["codex-api"]`
- `mcpServers["codex-wrapper"]`

Minimal example:

```json
{
  "mcpServers": {
    "codex-subscription": {
      "command": "codex",
      "args": ["mcp-server", "--sandbox", "read-only"],
      "env": {
        "CODEX_HOME": "/home/jgamboa/.config/openai/codex-home",
        "AUTH_MODE": "subscription"
      }
    },
    "codex-api": {
      "command": "bash",
      "args": [
        "-lc",
        "set -a; source /home/jgamboa/hillstar-orchestrator/.env; set +a; export CODEX_HOME=/home/jgamboa/.config/openai/codex-home; exec codex mcp-server --sandbox read-only"
      ],
      "env": {
        "AUTH_MODE": "api_key"
      }
    },
    "codex-wrapper": {
      "command": "node",
      "args": ["/home/jgamboa/.config/claude/mcp-servers/codex-wrapper.js"],
      "env": {
        "CODEX_HOME": "/home/jgamboa/.config/openai/codex-home",
        "AUTH_MODE": "subscription"
      }
    }
  }
}
```

## Mode A: ChatGPT subscription (OAuth)

1. Use `codex-subscription` server (no API key required in MCP config).
2. Run `codex login` and choose ChatGPT sign-in.
3. Confirm `auth.json` has:
   - `"auth_mode": "chatgpt"`
   - non-null `tokens.access_token` and `tokens.refresh_token`
4. Codex will create/update:
   - `/home/jgamboa/.config/openai/codex-home/auth.json`
   - `/home/jgamboa/.config/openai/codex-home/config.toml`
5. Restart Claude so MCP servers inherit current auth state.

## Mode B: API key

1. Use `codex-api` server.
2. Ensure `OPENAI_API_KEY` is present in `/home/jgamboa/hillstar-orchestrator/.env`.
3. Restart Claude if `mcp_config.json` changed.
4. Validate Codex runs without ChatGPT login prompts.

## File permissions

```bash
chmod 600 ~/.config/openai/codex-home/auth.json
```

## Fast switch checklist

- Subscription mode:
  - `codex-subscription` selected
  - `CODEX_HOME` set
  - `codex login` completed

- API key mode:
  - `codex-api` selected
  - `OPENAI_API_KEY` present in repo `.env`

## Important boundary

Hillstar providers in this repo remain API-key/credential based by design. This document only covers how Claude launches Codex globally.
