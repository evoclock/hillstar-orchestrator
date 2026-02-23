# MCP Topology and Scope

This repository is not the source of your global Claude MCP launcher config.

If you see two different sets of MCP servers, it is usually because of global user config (for example `~/.config/claude/mcp_config.json`) plus this repo's own in-project MCP provider scripts.

## Global MCP Layer (outside this repo)

- Owner: Your local Claude/Codex desktop setup.
- Typical config location: `~/.config/claude/mcp_config.json`.
- Purpose: Defines which MCP servers Claude launches in your user environment.
- Example servers: `codex-subscription`, `codex-api`, `codex-wrapper`, personal utility servers.

## Project MCP Layer (inside this repo)

- Owner: Hillstar project code.
- Location: `mcp-server/`.
- Purpose: Provider bridge scripts used by Hillstar runtime and model wrappers.
- Referenced by:
  - `models/mcp_model.py`
  - `models/openai_mcp_model.py`
  - `config/provider_registry.default.json`

## Why confusion happens

- Both layers use "MCP server" terminology.
- They are configured in different places and have different lifecycles.
- Changing one layer does not automatically change the other.

## Operational rule

- To change what Claude launches: edit global config (`~/.config/claude/mcp_config.json`).
- To change Hillstar provider behavior: edit in-repo files under `mcp-server/` and provider registry config.
- For OpenAI auth mode switching in Claude, prefer selecting the appropriate server entry (`codex-subscription` vs `codex-api`) rather than repeatedly editing env blocks.
