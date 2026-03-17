"""
Script
------
agent_scanner.py

Path
----
workflows/agent_scanner.py

Purpose
-------
Static security scanner for MCP server configurations and agent skill files.
Detects hardcoded secrets, shell injection, prompt injection, data exfiltration,
untrusted endpoints, and dangerous command flags without needing to start servers.

Inputs
------
- MCP config files (JSON): ~/.claude.json, .mcp.json, mcp.json
- Skill files (Markdown): SKILL.md or directories containing them
- Directories to scan recursively

Outputs
-------
List of Finding objects with severity, rule ID, description, file path, and
matching evidence.

Assumptions
-----------
- MCP configs follow the Claude Code / Cursor / Windsurf JSON format
- Skill files are Markdown with optional code blocks
- Scanning is read-only and never executes any server or command

Parameters
----------
- severity_threshold: Minimum severity to report (low, medium, high, critical)
- include_info: Whether to include informational findings

Failure Modes
-------------
- Unparseable JSON: reported as INFO finding, scanning continues
- Unreadable file: reported as INFO finding, scanning continues
- Empty directory: returns empty findings list

Author: Julen Gamboa

Created: 2026-03-17

Last Edited: 2026-03-17 by Julen Gamboa
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


class Severity(IntEnum):
	"""Finding severity levels."""
	INFO = 0
	LOW = 1
	MEDIUM = 2
	HIGH = 3
	CRITICAL = 4


@dataclass
class Finding:
	"""A single security finding."""
	rule_id: str
	severity: Severity
	title: str
	description: str
	file_path: str
	evidence: str = ""
	line_number: int = 0
	server_name: str = ""


@dataclass
class ScanResult:
	"""Aggregated scan results."""
	findings: list[Finding] = field(default_factory=list)
	files_scanned: int = 0
	servers_scanned: int = 0

	@property
	def critical_count(self) -> int:
		return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

	@property
	def high_count(self) -> int:
		return sum(1 for f in self.findings if f.severity == Severity.HIGH)

	@property
	def medium_count(self) -> int:
		return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

	@property
	def low_count(self) -> int:
		return sum(1 for f in self.findings if f.severity == Severity.LOW)


# ---------------------------------------------------------------------------
# Detection rules
# ---------------------------------------------------------------------------

# Patterns that indicate hardcoded secrets in env vars
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
	("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
	("AWS secret key", re.compile(r"(?i)(aws.?secret|secret.?access).{0,20}['\"][A-Za-z0-9/+=]{40}")),
	("Generic API key", re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}")),
	("Anthropic API key", re.compile(r"sk-ant-api\d{2}-[A-Za-z0-9_\-]{20,}")),
	("OpenAI API key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
	("Generic secret", re.compile(r"(?i)(password|passwd|secret|token|credential)\s*[:=]\s*['\"][^'\"]{8,}")),
	("Private key marker", re.compile(r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----")),
	("Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{20,}")),
]

# Env var names that commonly hold secrets
SECRET_ENV_NAMES: set[str] = {
	"AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID",
	"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "MISTRAL_API_KEY",
	"DATABASE_PASSWORD", "DB_PASSWORD", "POSTGRES_PASSWORD",
	"ADMIN_TOKEN", "AUTH_TOKEN", "SECRET_KEY",
	"PRIVATE_KEY", "CLIENT_SECRET", "API_SECRET",
	"GITHUB_TOKEN", "GITLAB_TOKEN", "NPM_TOKEN",
}

# Shell injection indicators in commands/args
SHELL_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
	("Command substitution", re.compile(r"\$\(.*\)")),
	("Backtick execution", re.compile(r"`[^`]+`")),
	("Pipe chain", re.compile(r"\|")),
	("Command chain (&&)", re.compile(r"&&")),
	("Command chain (;)", re.compile(r";\s*\w")),
	("Redirect to file", re.compile(r">\s*/\w")),
	("Curl/wget exfiltration", re.compile(r"(?i)(curl|wget)\s+.*(http|ftp)")),
	("Netcat listener", re.compile(r"(?i)\bnc\b.*-[lp]")),
	("Read sensitive files", re.compile(r"(?i)cat\s+(/etc/passwd|/etc/shadow|~/\.ssh|~/\.env|~/\.aws)")),
]

# Dangerous command-line flags
DANGEROUS_FLAGS: list[str] = [
	"--no-sandbox",
	"--disable-security",
	"--allow-all",
	"--privileged",
	"--no-verify",
	"--insecure",
	"--trust-all",
]

# Prompt injection patterns for skill files
PROMPT_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
	("System prompt override", re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions")),
	("Role hijack", re.compile(r"(?i)you\s+are\s+now\s+(in\s+)?(maintenance|admin|root|debug)\s+mode")),
	("Safety bypass", re.compile(r"(?i)(bypass|disable|override|ignore)\s+(all\s+)?(safety|security)\s+(checks|filters|restrictions)")),
	("Hidden HTML instruction", re.compile(r"<!--.*?(ignore|override|execute|bypass|admin).*?-->", re.DOTALL)),
	("Invisible instruction", re.compile(r"(?i)(silently|secretly|without\s+(showing|telling|informing))")),
]

# Credential/data theft patterns in skills
EXFILTRATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
	("SSH key access", re.compile(r"(?i)(~/\.ssh|\.ssh/id_rsa|\.ssh/id_ed25519|authorized_keys)")),
	("AWS credential access", re.compile(r"(?i)(~/\.aws|\.aws/credentials|\.aws/config)")),
	("Env file access", re.compile(r"(?i)(~/\.env|\.env\b|\.env\.local)")),
	("Shadow file access", re.compile(r"/etc/shadow")),
	("Browser data access", re.compile(r"(?i)(\.chrome|\.firefox|\.mozilla).*(cookie|password|login)")),
	("Remote exfiltration URL", re.compile(r"(?i)(curl|wget|fetch|requests?\.(get|post))\s+.*(https?://(?!localhost|127\.0\.0\.1)[^\s\"']+)")),
	("Data POST to remote", re.compile(r"(?i)curl\s+-X\s+POST\s+https?://(?!localhost|127\.0\.0\.1)")),
]

# Destructive command patterns in skills
DESTRUCTIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
	("Recursive delete", re.compile(r"(?i)rm\s+-rf?\s+/")),
	("Format disk", re.compile(r"(?i)mkfs\.")),
	("Drop database", re.compile(r"(?i)DROP\s+(DATABASE|TABLE|SCHEMA)")),
	("Kill all processes", re.compile(r"(?i)kill\s+-9\s+-1")),
	("Fork bomb", re.compile(r":\(\)\s*\{\s*:\|:&\s*\}")),
]


# ---------------------------------------------------------------------------
# Scanner implementation
# ---------------------------------------------------------------------------

class AgentScanner:
	"""Static security scanner for MCP configs and agent skill files."""

	@staticmethod
	def scan_mcp_config(file_path: Path) -> ScanResult:
		"""Scan an MCP configuration file for security issues.

		Parses the JSON and inspects server definitions for hardcoded
		secrets, shell injection, untrusted endpoints, and dangerous flags.
		"""
		result = ScanResult()
		path_str = str(file_path)

		try:
			raw = file_path.read_text()
		except (OSError, PermissionError) as exc:
			result.findings.append(Finding(
				rule_id="SCAN-001",
				severity=Severity.INFO,
				title="File unreadable",
				description=str(exc),
				file_path=path_str,
			))
			return result

		try:
			data = json.loads(raw)
		except json.JSONDecodeError as exc:
			result.findings.append(Finding(
				rule_id="SCAN-002",
				severity=Severity.INFO,
				title="Invalid JSON",
				description=str(exc),
				file_path=path_str,
			))
			return result

		result.files_scanned = 1

		# Find servers in various config layouts
		servers = AgentScanner._extract_servers(data)

		for name, server_cfg in servers.items():
			result.servers_scanned += 1
			AgentScanner._check_server(name, server_cfg, path_str, result)

		# Also scan the raw text for secrets not in structured fields
		AgentScanner._check_raw_secrets(raw, path_str, result)

		return result

	@staticmethod
	def scan_skill_file(file_path: Path) -> ScanResult:
		"""Scan a skill/prompt markdown file for security issues.

		Checks for prompt injection, credential theft directives,
		data exfiltration, and destructive commands.
		"""
		result = ScanResult()
		path_str = str(file_path)

		try:
			content = file_path.read_text()
		except (OSError, PermissionError) as exc:
			result.findings.append(Finding(
				rule_id="SCAN-001",
				severity=Severity.INFO,
				title="File unreadable",
				description=str(exc),
				file_path=path_str,
			))
			return result

		result.files_scanned = 1

		# Prompt injection
		for label, pattern in PROMPT_INJECTION_PATTERNS:
			for match in pattern.finditer(content):
				line_num = content[:match.start()].count("\n") + 1
				result.findings.append(Finding(
					rule_id="SKILL-001",
					severity=Severity.HIGH,
					title=f"Prompt injection: {label}",
					description=(
						f"Skill contains prompt injection pattern: {label}. "
						"This could override safety guardrails or hijack agent behavior."
					),
					file_path=path_str,
					evidence=match.group().strip()[:200],
					line_number=line_num,
				))

		# Credential/data theft
		for label, pattern in EXFILTRATION_PATTERNS:
			for match in pattern.finditer(content):
				line_num = content[:match.start()].count("\n") + 1
				result.findings.append(Finding(
					rule_id="SKILL-002",
					severity=Severity.CRITICAL,
					title=f"Data exfiltration: {label}",
					description=(
						f"Skill references sensitive data or remote endpoint: {label}. "
						"This could steal credentials or exfiltrate data."
					),
					file_path=path_str,
					evidence=match.group().strip()[:200],
					line_number=line_num,
				))

		# Destructive commands
		for label, pattern in DESTRUCTIVE_PATTERNS:
			for match in pattern.finditer(content):
				line_num = content[:match.start()].count("\n") + 1
				result.findings.append(Finding(
					rule_id="SKILL-003",
					severity=Severity.CRITICAL,
					title=f"Destructive command: {label}",
					description=(
						f"Skill contains destructive command pattern: {label}. "
						"This could cause irreversible damage to the system."
					),
					file_path=path_str,
					evidence=match.group().strip()[:200],
					line_number=line_num,
				))

		# Shell injection in code blocks
		code_blocks = re.findall(r"```(?:bash|sh|shell)?\n(.*?)```", content, re.DOTALL)
		for block in code_blocks:
			for label, pattern in SHELL_INJECTION_PATTERNS:
				for match in pattern.finditer(block):
					block_start = content.find(block)
					line_num = content[:block_start + match.start()].count("\n") + 1
					result.findings.append(Finding(
						rule_id="SKILL-004",
						severity=Severity.HIGH,
						title=f"Shell injection in code block: {label}",
						description=(
							f"Code block contains potentially dangerous pattern: {label}."
						),
						file_path=path_str,
						evidence=match.group().strip()[:200],
						line_number=line_num,
					))

		return result

	@staticmethod
	def scan_path(target: Path) -> ScanResult:
		"""Scan a file or directory, auto-detecting file types.

		For directories, recursively scans for MCP configs and skill files.
		"""
		result = ScanResult()

		if target.is_file():
			if target.suffix == ".json":
				return AgentScanner.scan_mcp_config(target)
			elif target.suffix == ".md":
				return AgentScanner.scan_skill_file(target)
			else:
				result.findings.append(Finding(
					rule_id="SCAN-003",
					severity=Severity.INFO,
					title="Unsupported file type",
					description=f"Cannot scan {target.suffix} files",
					file_path=str(target),
				))
				return result

		if target.is_dir():
			# Scan MCP configs
			for pattern in ("**/mcp.json", "**/.mcp.json", "**/.claude.json"):
				for path in sorted(target.glob(pattern)):
					sub = AgentScanner.scan_mcp_config(path)
					result.findings.extend(sub.findings)
					result.files_scanned += sub.files_scanned
					result.servers_scanned += sub.servers_scanned

			# Scan skill files
			for path in sorted(target.glob("**/*.md")):
				if "skill" in path.name.lower() or "skills" in str(path).lower():
					sub = AgentScanner.scan_skill_file(path)
					result.findings.extend(sub.findings)
					result.files_scanned += sub.files_scanned

		return result

	# -------------------------------------------------------------------
	# Internal helpers
	# -------------------------------------------------------------------

	@staticmethod
	def _extract_servers(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
		"""Extract MCP server definitions from various config formats."""
		servers: dict[str, dict[str, Any]] = {}

		# Top-level mcpServers (standard .mcp.json / .claude.json)
		if "mcpServers" in data and isinstance(data["mcpServers"], dict):
			servers.update(data["mcpServers"])

		# Project-scoped servers in .claude.json
		if "projects" in data and isinstance(data["projects"], dict):
			for _proj_path, proj_cfg in data["projects"].items():
				if "mcpServers" in proj_cfg and isinstance(proj_cfg["mcpServers"], dict):
					servers.update(proj_cfg["mcpServers"])

		return servers

	@staticmethod
	def _check_server(
		name: str,
		cfg: dict[str, Any],
		file_path: str,
		result: ScanResult,
	) -> None:
		"""Run all server-level checks on a single MCP server definition."""

		# --- Check env vars for secrets ---
		env = cfg.get("env", {})
		if isinstance(env, dict):
			for env_key, env_val in env.items():
				# Check env var name
				if env_key.upper() in SECRET_ENV_NAMES:
					val_str = str(env_val)
					# Skip if it's an env var reference
					if val_str.startswith("${") or val_str.startswith("$"):
						continue
					result.findings.append(Finding(
						rule_id="MCP-001",
						severity=Severity.CRITICAL,
						title=f"Hardcoded secret in env: {env_key}",
						description=(
							f"Server '{name}' has sensitive env var '{env_key}' with a "
							"hardcoded value. Use environment variable references instead."
						),
						file_path=file_path,
						evidence=f"{env_key}={val_str[:8]}{'*' * max(0, len(val_str) - 8)}",
						server_name=name,
					))

				# Check env var value against patterns
				for label, pattern in SECRET_PATTERNS:
					if pattern.search(str(env_val)):
						result.findings.append(Finding(
							rule_id="MCP-002",
							severity=Severity.CRITICAL,
							title=f"Secret pattern in env value: {label}",
							description=(
								f"Server '{name}' env var '{env_key}' contains a "
								f"value matching the pattern for {label}."
							),
							file_path=file_path,
							evidence=f"{env_key}=<redacted>",
							server_name=name,
						))

		# --- Check command + args for shell injection ---
		command = cfg.get("command", "")
		args = cfg.get("args", [])
		full_cmd = f"{command} {' '.join(str(a) for a in args)}" if args else command

		if full_cmd:
			for label, pattern in SHELL_INJECTION_PATTERNS:
				if pattern.search(full_cmd):
					result.findings.append(Finding(
						rule_id="MCP-003",
						severity=Severity.HIGH,
						title=f"Shell injection in command: {label}",
						description=(
							f"Server '{name}' command contains pattern: {label}. "
							"An attacker could exploit this for arbitrary command execution."
						),
						file_path=file_path,
						evidence=full_cmd[:200],
						server_name=name,
					))

			# Check for dangerous flags
			for flag in DANGEROUS_FLAGS:
				if flag in full_cmd:
					result.findings.append(Finding(
						rule_id="MCP-004",
						severity=Severity.MEDIUM,
						title=f"Dangerous flag: {flag}",
						description=(
							f"Server '{name}' uses flag '{flag}' which may "
							"disable important security controls."
						),
						file_path=file_path,
						evidence=full_cmd[:200],
						server_name=name,
					))

		# --- Check remote URLs ---
		url = cfg.get("url", "")
		if url:
			AgentScanner._check_url(name, url, file_path, result)

		# Check headers for secrets
		headers = cfg.get("headers", {})
		if isinstance(headers, dict):
			for hdr_key, hdr_val in headers.items():
				for label, pattern in SECRET_PATTERNS:
					if pattern.search(str(hdr_val)):
						result.findings.append(Finding(
							rule_id="MCP-005",
							severity=Severity.HIGH,
							title=f"Secret in header: {label}",
							description=(
								f"Server '{name}' header '{hdr_key}' contains a "
								f"value matching the pattern for {label}."
							),
							file_path=file_path,
							evidence=f"{hdr_key}: <redacted>",
							server_name=name,
						))

	@staticmethod
	def _check_url(
		name: str,
		url: str,
		file_path: str,
		result: ScanResult,
	) -> None:
		"""Check a remote MCP server URL for security issues."""
		from urllib.parse import urlparse

		parsed = urlparse(url)

		# HTTP without TLS
		if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
			result.findings.append(Finding(
				rule_id="MCP-006",
				severity=Severity.MEDIUM,
				title="Unencrypted remote connection",
				description=(
					f"Server '{name}' uses HTTP (not HTTPS) for remote host "
					f"'{parsed.hostname}'. Traffic may be intercepted."
				),
				file_path=file_path,
				evidence=url,
				server_name=name,
			))

		# Non-localhost without HTTPS
		if parsed.hostname and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
			if parsed.scheme != "https":
				result.findings.append(Finding(
					rule_id="MCP-007",
					severity=Severity.HIGH,
					title="Untrusted remote endpoint",
					description=(
						f"Server '{name}' connects to remote host '{parsed.hostname}' "
						"without HTTPS. This could be a malicious server."
					),
					file_path=file_path,
					evidence=url,
					server_name=name,
				))

	@staticmethod
	def _check_raw_secrets(
		raw: str,
		file_path: str,
		result: ScanResult,
	) -> None:
		"""Scan raw file content for secret patterns outside of structured fields."""
		for label, pattern in SECRET_PATTERNS:
			for match in pattern.finditer(raw):
				line_num = raw[:match.start()].count("\n") + 1
				# Avoid duplicate findings from structured checks
				already_found = any(
					f.rule_id == "MCP-002" and f.line_number == line_num
					for f in result.findings
				)
				if not already_found:
					result.findings.append(Finding(
						rule_id="MCP-008",
						severity=Severity.HIGH,
						title=f"Secret in config text: {label}",
						description=(
							f"File contains text matching the pattern for {label} "
							f"at line {line_num}."
						),
						file_path=file_path,
						evidence=f"line {line_num}: <redacted>",
						line_number=line_num,
					))


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_findings(result: ScanResult, *, use_color: bool = True) -> str:
	"""Format scan results as human-readable text."""
	lines: list[str] = []

	if not result.findings:
		lines.append("[OK] No security issues found")
		lines.append(f"     Scanned {result.files_scanned} file(s), {result.servers_scanned} server(s)")
		return "\n".join(lines)

	severity_labels = {
		Severity.CRITICAL: "CRITICAL",
		Severity.HIGH: "HIGH",
		Severity.MEDIUM: "MEDIUM",
		Severity.LOW: "LOW",
		Severity.INFO: "INFO",
	}

	# Group by file
	by_file: dict[str, list[Finding]] = {}
	for f in sorted(result.findings, key=lambda x: (-x.severity, x.file_path)):
		by_file.setdefault(f.file_path, []).append(f)

	for fpath, findings in by_file.items():
		lines.append(f"[SCAN] {fpath}")
		for f in findings:
			sev = severity_labels.get(f.severity, "UNKNOWN")
			server_ctx = f" ({f.server_name})" if f.server_name else ""
			line_ctx = f" line {f.line_number}" if f.line_number else ""
			lines.append(f"  [{sev}] {f.rule_id}: {f.title}{server_ctx}{line_ctx}")
			lines.append(f"          {f.description}")
			if f.evidence:
				lines.append(f"          Evidence: {f.evidence}")
			lines.append("")

	lines.append("---")
	lines.append(
		f"Summary: {len(result.findings)} finding(s) "
		f"[{result.critical_count} CRITICAL, {result.high_count} HIGH, "
		f"{result.medium_count} MEDIUM, {result.low_count} LOW]"
	)
	lines.append(f"Scanned: {result.files_scanned} file(s), {result.servers_scanned} server(s)")

	return "\n".join(lines)
