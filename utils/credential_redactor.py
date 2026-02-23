"""
Script
------
credential_redactor.py

Path
----
python/hillstar/utils/credential_redactor.py

Purpose
-------
Detect and redact sensitive credentials (API keys, tokens, infrastructure identifiers, PII)
from strings, logs, and error messages. Prevents accidental data leakage in output.

Implements comprehensive credential detection covering: API keys, OAuth tokens, AWS credentials,
infrastructure identifiers, and PII based on industry standard patterns.

Inputs
------
String containing potential credentials

Outputs
-------
String with credentials redacted as [REDACTED:TYPE]

Assumptions
-----------
- Credentials follow common patterns (API key formats, token types, etc.)
- All potentially sensitive data should be redacted
- Redaction preserves string structure for error clarity

Failure Modes
-------------
None - always returns a valid string (worst case: no redactions made)

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-17

Last Edited
-----------
2026-02-17
"""

import re
from typing import Optional


class CredentialRedactor:
    """Detect and redact sensitive credentials from strings."""

    # Patterns for credential types (Warp's list + custom patterns for Hillstar)
    PATTERNS = {
        # Warp Secret Redaction List
        # Network & Infrastructure
        "ipv4_address": r"\b((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}\b",
        "ipv6_address": r"\b((([0-9A-Fa-f]{1,4}:){1,6}:)|(([0-9A-Fa-f]{1,4}:){7}))([0-9A-Fa-f]{1,4})\b",
        "mac_address": r"\b((([a-zA-z0-9]{2}[-:]){5}([a-zA-z0-9]{2}))|(([a-zA-z0-9]{2}:){5}([a-zA-z0-9]{2})))\b",

        # PII
        "phone_number": r"\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b",

        # Cloud Credentials
        "aws_access_id": r"\b(AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{12,}\b",

        # Tokens & Keys (Warp list + fixes for real key formats)
        "anthropic_key": r"sk-ant-[a-zA-Z0-9\-_]{6,}",
        "openai_key": r"sk-[a-zA-Z0-9\-_]{10,}",
        "fireworks_key": r"fw_[a-zA-Z0-9]{10,}",
        "google_key": r"AIza[0-9A-Za-z\-_]{10,}",
        "google_oauth_id": r"\b[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com\b",
        "github_pat_classic": r"\bghp_[A-Za-z0-9_]{36}\b",
        "github_pat_fine_grained": r"\bgithub_pat_[A-Za-z0-9_]{82}\b",
        "github_oauth_token": r"\bgho_[A-Za-z0-9_]{36}\b",
        "github_user_to_server": r"\bghu_[A-Za-z0-9_]{36}\b",
        "github_server_to_server": r"\bghs_[A-Za-z0-9_]{36}\b",
        "stripe_key": r"\b(?:r|s)k_(test|live)_[0-9a-zA-Z]{24}\b",
        "firebase_domain": r"\b([a-z0-9-]){1,30}(\.firebaseapp\.com)\b",
        "json_web_token": r"\b(ey[a-zA-z0-9_\-=]{10,}\.){2}[a-zA-z0-9_\-=]{10,}\b",
        "slack_app_token": r"\bxapp-[0-9]+-[A-Za-z0-9_]+-[0-9]+-[a-f0-9]+\b",

        # Custom patterns for Hillstar
        "bearer_token": r"Bearer\s+[a-zA-Z0-9\-\._~\+\/=]{6,}",
        "api_key_generic": r"(?:api[_-]?key|api[_-]?token)\s*[=:]\s*['\"]?([a-zA-Z0-9\-_\.]+)['\"]?",
        "authorization": r"(?:Authorization|X-API-Key)\s*[=:]\s*['\"]?([a-zA-Z0-9\-_\.]+)['\"]?",
        "credentials_json": r'"(?:api_key|apiKey|access_token|accessToken|password|secret)"\s*:\s*"([^"]+)"',
        "url_password": r"(?:https?://)[^:]+:([a-zA-Z0-9\-_\.]+)@",
        "env_var_value": r"(?:ANTHROPIC_API_KEY|OPENAI_API_KEY|MISTRAL_API_KEY|GOOGLE_API_KEY)\s*=\s*([a-zA-Z0-9\-_\.]+)",
    }

    @staticmethod
    def redact(text: Optional[str], include_patterns: Optional[list] = None) -> str:
        """
        Redact all detected credentials from text.

        Args:
            text: String potentially containing credentials (returns empty string if None)
            include_patterns: List of pattern names to apply (default: all)

        Returns:
            String with credentials redacted as [REDACTED:TYPE]

        Examples:
            >>> redactor = CredentialRedactor()
            >>> redactor.redact("My key is sk-ant-abc123def456")
            'My key is [REDACTED:anthropic_key]'

            >>> redactor.redact('api_key = "secret-value"')
            'api_key = [REDACTED:api_key_generic]'
        """
        if text is None:
            return ""
        if not text:
            return text

        patterns = include_patterns or list(CredentialRedactor.PATTERNS.keys())
        result = str(text)

        for pattern_name in patterns:
            if pattern_name not in CredentialRedactor.PATTERNS:
                continue

            pattern = CredentialRedactor.PATTERNS[pattern_name]
            matches = re.finditer(pattern, result, re.IGNORECASE)

            for match in reversed(list(matches)):
                # Replace the entire match with redaction marker
                start, end = match.span()
                result = result[:start] + f"[REDACTED:{pattern_name}]" + result[end:]

        return result

    @staticmethod
    def contains_credentials(text: Optional[str]) -> bool:
        """
        Check if text contains any detected credentials.

        Args:
            text: String to check (returns False if None)

        Returns:
            True if any credentials detected, False otherwise
        """
        if not text:
            return False

        for pattern in CredentialRedactor.PATTERNS.values():
            if re.search(pattern, str(text), re.IGNORECASE):
                return True

        return False

    @staticmethod
    def get_redaction_types(text: str) -> list:
        """
        Identify which credential types are present in text.

        Args:
            text: String to analyze

        Returns:
            List of pattern names detected

        Example:
            >>> redactor.get_redaction_types("key=sk-ant-123")
            ['anthropic_key', 'api_key_generic']
        """
        if not text:
            return []

        detected = []
        for pattern_name, pattern in CredentialRedactor.PATTERNS.items():
            if re.search(pattern, str(text), re.IGNORECASE):
                detected.append(pattern_name)

        return detected


# Convenience function for one-off redaction
def redact(text: Optional[str]) -> str:
    """Convenience function to redact credentials from a string.

    Args:
        text: String potentially containing credentials (returns empty string if None)

    Returns:
        String with credentials redacted
    """
    return CredentialRedactor.redact(text)


def contains_credentials(text: Optional[str]) -> bool:
    """Convenience function to check if string contains credentials.

    Args:
        text: String to check (returns False if None)

    Returns:
        True if credentials detected
    """
    return CredentialRedactor.contains_credentials(text)
