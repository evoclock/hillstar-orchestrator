# Static Security Scanning for MCP Configurations and Agent Skills

**Julen Gamboa** | MCP Presentation | March 2026

---

## The Problem

AI coding agents (Claude Code, Cursor, Windsurf, Gemini CLI) rely on **MCP server configurations** and **skill files** to extend their capabilities. These files define:

- Which external servers the agent connects to
- What commands it can execute
- What instructions guide its behavior

**But who audits these files for security?**

A malicious or misconfigured MCP server definition can:

- **Exfiltrate credentials** (SSH keys, API tokens, AWS secrets)
- **Execute arbitrary commands** via shell injection
- **Connect to untrusted remote endpoints** without TLS
- **Override safety guardrails** through prompt injection in skills

---

## Existing Tools Fall Short

### snyk-agent-scan v0.4.8 (Snyk, 2025)

Marketed as the solution for AI agent security scanning. In practice:

| Test | snyk-agent-scan | Expected |
|------|----------------|----------|
| Hardcoded AWS key in MCP env | **0 findings** | CRITICAL |
| Shell injection in server command | **0 findings** | HIGH |
| `--no-sandbox` flag | **0 findings** | MEDIUM |
| HTTP to untrusted remote host | **0 findings** | HIGH |
| Prompt injection in skill file | **X005 parse error** | HIGH |
| `curl -X POST` to evil.com in skill | **X005 parse error** | CRITICAL |
| `rm -rf /` in skill | **X005 parse error** | CRITICAL |

**Total: 0 findings on deliberately insecure test fixtures.**

Why? snyk-agent-scan uses **runtime introspection** -- it starts MCP servers and inspects their tool schemas. It performs minimal static analysis of configurations and cannot parse skill files at all.

---

## Our Approach: Static Pattern Analysis

`hillstar agent-scan` uses pure static analysis -- no servers are started, no commands executed.

### Architecture

```
                          +------------------+
  Target path  ---------> |  AgentScanner    |
  (file or dir)           +------------------+
                          |                  |
                    +-----+------+     +-----+------+
                    | MCP Config |     | Skill File |
                    | Scanner    |     | Scanner    |
                    +-----+------+     +-----+------+
                          |                  |
                    +-----+------+     +-----+------+
                    | - Secrets  |     | - Prompt   |
                    | - Shell    |     |   injection|
                    |   injection|     | - Exfiltr. |
                    | - Flags    |     | - Destruct.|
                    | - URLs     |     | - Shell in |
                    | - Headers  |     |   code blks|
                    +-----+------+     +-----+------+
                          |                  |
                          v                  v
                     +---------------------------+
                     |       ScanResult          |
                     | (findings, severities,    |
                     |  file/server counts)       |
                     +---------------------------+
```

### Detection Rules

**MCP Config Scanning (8 rule categories):**

| Rule ID | Category | Severity | What It Catches |
|---------|----------|----------|-----------------|
| MCP-001 | Hardcoded secret env name | CRITICAL | AWS_SECRET_ACCESS_KEY, ANTHROPIC_API_KEY, DATABASE_PASSWORD, etc. (17 known names) |
| MCP-002 | Secret pattern in env value | CRITICAL | AKIA keys, sk-ant- keys, Bearer tokens, private key markers (8 patterns) |
| MCP-003 | Shell injection in command | HIGH | $(), backticks, pipes, &&, curl/wget, cat /etc/passwd (9 patterns) |
| MCP-004 | Dangerous flags | MEDIUM | --no-sandbox, --disable-security, --allow-all, --privileged (7 flags) |
| MCP-005 | Secret in HTTP headers | HIGH | Auth tokens, API keys in request headers |
| MCP-006 | Unencrypted remote connection | MEDIUM | HTTP (not HTTPS) to non-localhost hosts |
| MCP-007 | Untrusted remote endpoint | HIGH | Non-localhost without HTTPS |
| MCP-008 | Secret in raw config text | HIGH | Patterns found outside structured env fields |

**Skill File Scanning (4 rule categories):**

| Rule ID | Category | Severity | What It Catches |
|---------|----------|----------|-----------------|
| SKILL-001 | Prompt injection | HIGH | "ignore previous instructions", role hijack, safety bypass, hidden HTML comments, invisible instructions (5 patterns) |
| SKILL-002 | Data exfiltration | CRITICAL | SSH key access, AWS credentials, .env files, /etc/shadow, remote POST/curl to non-localhost (7 patterns) |
| SKILL-003 | Destructive commands | CRITICAL | rm -rf, mkfs, DROP DATABASE, kill -9 -1, fork bombs (5 patterns) |
| SKILL-004 | Shell injection in code blocks | HIGH | All 9 shell injection patterns applied to fenced code blocks |

---

## Head-to-Head Results

Same test fixtures, same machine, same day:

### Malicious MCP Config (3 servers: shell injection + hardcoded secrets + untrusted SSE)

| | snyk-agent-scan | hillstar agent-scan |
|-|----------------|---------------------|
| CRITICAL | 0 | **6** |
| HIGH | 0 | **7** |
| MEDIUM | 0 | **4** |
| **Total** | **0** | **17** |

### Malicious Skill File (prompt injection + credential theft + rm -rf)

| | snyk-agent-scan | hillstar agent-scan |
|-|----------------|---------------------|
| CRITICAL | X005 error | **11** |
| HIGH | X005 error | **14** |
| **Total** | **parse error** | **25** |

### Combined Directory Scan

| | snyk-agent-scan | hillstar agent-scan |
|-|----------------|---------------------|
| Files scanned | 1 (MCP only) | **2** (MCP + skill) |
| Servers inspected | 3 (runtime) | **3** (static) |
| Total findings | **0** | **42** |

---

## Key Design Decisions

### 1. Static over runtime

Runtime scanning requires starting servers -- which means executing potentially malicious commands. Static analysis catches issues **before** anything runs.

### 2. Config format awareness

Handles both standard `.mcp.json` and Claude Code's `.claude.json` format (with project-scoped `projects.*.mcpServers` nesting).

### 3. Env var reference passthrough

Values like `${ANTHROPIC_API_KEY}` or `$AWS_SECRET_ACCESS_KEY` are environment variable references, not hardcoded secrets. The scanner correctly skips these.

### 4. Localhost exemption

HTTP connections to `localhost`, `127.0.0.1`, and `::1` are not flagged as untrusted. Only remote hosts without HTTPS trigger findings.

### 5. Evidence without exposure

Secrets are partially redacted in findings (`AKIAIOSF************`). Enough to confirm the finding, not enough to leak the value.

---

## CLI Usage

```bash
# Scan a single MCP config
hillstar agent-scan ~/.claude.json

# Scan a skill file
hillstar agent-scan ~/.claude/skills/DANGEROUS_SKILL.md

# Scan a directory recursively (finds mcp.json, .mcp.json, .claude.json, *skill*.md)
hillstar agent-scan /path/to/project/

# Filter by severity
hillstar agent-scan . --severity critical

# Machine-readable JSON output
hillstar agent-scan . --json
```

Exit code: **1** if any HIGH or CRITICAL findings, **0** otherwise.

---

## Test Coverage

51 tests, 95% code coverage on the scanner module:

- 16 MCP config tests (secrets, injection, flags, URLs, clean configs, edge cases)
- 14 skill scanning tests (prompt injection, exfiltration, destructive commands, clean skills)
- 9 directory scanning tests (auto-detection, nested dirs, combined scans)
- 6 output formatting tests (grouping, severity labels, evidence display)
- 3 severity enum tests (ordering, filtering)
- 3 integration tests against real fixtures

---

## Limitations and Future Work

**Current limitations:**

- Regex-based pattern matching: may produce false positives on code documentation or security tutorials
- No data flow analysis (cannot trace a secret through variable assignments)
- Skill scanning limited to Markdown format
- No SARIF output format (yet)

**Planned improvements:**

- SARIF export for CI/CD integration
- Custom rule definitions via YAML config
- Baseline/suppression file (like .snyk but functional)
- Pre-commit hook integration
- Scanning of Python/TypeScript MCP server source code (not just configs)

---

## Summary

| Capability | snyk-agent-scan | hillstar agent-scan |
|------------|----------------|---------------------|
| Static analysis | Minimal | Full |
| Runtime analysis | Yes (starts servers) | No (read-only) |
| MCP config secrets | Not detected | 8 patterns, 17 env names |
| Shell injection | Not detected | 9 patterns |
| Dangerous flags | Not detected | 7 flags |
| Untrusted URLs | Not detected | HTTP + non-localhost |
| Skill prompt injection | Parse error | 5 patterns |
| Skill exfiltration | Parse error | 7 patterns |
| Skill destructive cmds | Parse error | 5 patterns |
| .claude.json support | Unknown | Yes (project-scoped) |
| JSON output | No | Yes |
| Test suite | N/A | 51 tests, 95% coverage |
| Cost | Free (uvx) | Free (open source) |

**42 findings vs 0** on identical test fixtures.

---

*Built as part of Hillstar, an open-source research workflow orchestrator.*

*Repository: github.com/evoclock/hillstar-orchestrator (feature/agent-scan branch)*
