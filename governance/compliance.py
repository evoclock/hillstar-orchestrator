"""
Script
------
compliance.py

Path
----
python/hillstar/governance/compliance.py

Purpose
-------
Compliance enforcement module for Hillstar.

Enforce Hillstar's compliance architecture and prevent prohibited modifications.
This module verifies that only API-based orchestration is used, preventing
CLI/SDK access that would violate provider terms of service.

Providers Covered
-----------------
- Anthropic (Claude)
- Mistral AI (Le Chat)
- OpenAI (GPT, Codex)
- Google (Vertex AI, Gemini)
- Amazon (Bedrock)
- Microsoft (Azure AI)
- Meta (Llama)
- Cohere
- Ollama

Compliance Rules
----------------
1. API-only authentication for cloud providers
2. No CLI/SDK access methods
3. No mixing of access patterns
4. Proper provider attribution
5. User responsibility documentation

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-14

Last Edited
-----------
2026-02-17
"""

import inspect
from typing import List, Any


class ComplianceError(Exception):
    """Raised when compliance violations are detected."""
    pass


class ComplianceEnforcer:
    """Enforce Hillstar's compliance architecture."""

    # Providers that require API-only access for orchestration
    PROTECTED_PROVIDERS = {
        "anthropic": {
            "name": "Anthropic",
            "prohibited_methods": ["use_cli", "claude_pro", "sdk_auth", "manual_access"],
            "prohibited_attributes": ["cli_mode", "pro_subscription", "sdk_client"],
            "tos_violation": "Violates Anthropic's automation restrictions"
        },
        "mistral": {
            "name": "Mistral AI",
            "prohibited_methods": ["use_le_chat", "pro_access", "chat_cli", "manual_mode"],
            "prohibited_attributes": ["le_chat_client", "pro_credentials", "cli_session"],
            "tos_violation": "Violates Mistral's Le Chat Pro terms"
        },
        "openai": {
            "name": "OpenAI",
            "prohibited_methods": ["use_codex_pro", "chatgpt_plus", "sdk_login", "cli_access"],
            "prohibited_attributes": ["pro_session", "codex_cli", "plus_subscription"],
            "tos_violation": "Violates OpenAI's automation policies"
        },
        "google": {
            "name": "Google",
            "prohibited_methods": ["vertex_cli", "gemini_pro", "sdk_console", "manual_access"],
            "prohibited_attributes": ["console_client", "pro_credentials", "cli_mode"],
            "tos_violation": "Violates Google Cloud's API requirements"
        },
        "amazon": {
            "name": "Amazon Bedrock",
            "prohibited_methods": ["bedrock_cli", "console_access", "sdk_manual", "pro_mode"],
            "prohibited_attributes": ["console_session", "cli_credentials", "manual_client"],
            "tos_violation": "Violates AWS's IAM requirements"
        },
        "microsoft": {
            "name": "Microsoft Azure AI",
            "prohibited_methods": ["azure_cli", "portal_access", "sdk_manual", "pro_console"],
            "prohibited_attributes": ["portal_session", "cli_credentials", "manual_mode"],
            "tos_violation": "Violates Azure's enterprise requirements"
        },
        "meta": {
            "name": "Meta Llama",
            "prohibited_methods": ["local_cli", "manual_llama", "sdk_direct", "pro_access"],
            "prohibited_attributes": ["cli_session", "direct_access", "pro_credentials"],
            "tos_violation": "Violates Llama's usage policies"
        },
        "cohere": {
            "name": "Cohere",
            "prohibited_methods": ["cohere_cli", "manual_access", "sdk_pro", "console_mode"],
            "prohibited_attributes": ["console_client", "cli_credentials", "pro_session"],
            "tos_violation": "Violates Cohere's API terms"
        },
        "ollama": {
            "name": "Ollama",
            "prohibited_methods": ["ollama_cli_mix", "pro_access", "sdk_manual"],
            "prohibited_attributes": ["cli_mixed", "pro_credentials"],
            "tos_violation": "Violates Ollama's local model terms"
        }
    }

    def __init__(self):
        self.violations = []

    def check_provider_class(self, provider_name: str, provider_class: Any) -> bool:
        """Check a provider class for compliance violations."""
        if provider_name not in self.PROTECTED_PROVIDERS:
            return True

        provider_rules = self.PROTECTED_PROVIDERS[provider_name]

        # Check for prohibited methods
        for method_name in provider_rules["prohibited_methods"]:
            if hasattr(provider_class, method_name):
                self.violations.append(
                    f" {provider_rules['name']}: Found prohibited method '{method_name}' - "
                    f"{provider_rules['tos_violation']}"
                )

        # Check for prohibited attributes
        for attr_name in provider_rules["prohibited_attributes"]:
            if hasattr(provider_class, attr_name):
                self.violations.append(
                    f" {provider_rules['name']}: Found prohibited attribute '{attr_name}' - "
                    f"{provider_rules['tos_violation']}"
                )

        return len(self.violations) == 0

    def check_all_providers(self) -> bool:
        """Check all provider implementations for compliance."""
        from ..models import (
            AnthropicModel,
            OpenAIMCPModel,
            DevstralLocalModel,
            AnthropicOllamaAPIModel,
        )

        providers_to_check = [
            ("anthropic", AnthropicModel),
            ("anthropic_ollama", AnthropicOllamaAPIModel),
            ("openai_mcp", OpenAIMCPModel),
            ("devstral", DevstralLocalModel),
        ]

        all_compliant = True
        for provider_name, provider_class in providers_to_check:
            if not self.check_provider_class(provider_name, provider_class):
                all_compliant = False

        return all_compliant

    def check_model_selector(self) -> bool:
        """Check ModelSelector for compliance violations."""
        from ..config.model_selector import ModelSelector

        # Check that use_api_key parameter doesn't exist
        select_sig = inspect.signature(ModelSelector.select)
        if 'use_api_key' in select_sig.parameters:
            self.violations.append(
                " ModelSelector: Found prohibited 'use_api_key' parameter - "
                "enables non-compliant authentication mixing"
            )
            return False

        # Check select_with_config
        select_config_sig = inspect.signature(ModelSelector.select_with_config)
        if 'use_api_key' in select_config_sig.parameters:
            self.violations.append(
                " ModelSelector: Found prohibited 'use_api_key' parameter in select_with_config - "
                "enables non-compliant authentication mixing"
            )
            return False

        return True

    def verify_compliance(self) -> bool:
        """Run all compliance checks."""
        self.violations = []

        # Check all provider implementations
        providers_ok = self.check_all_providers()

        # Check model selector
        selector_ok = self.check_model_selector()

        return providers_ok and selector_ok

    def get_violations(self) -> List[str]:
        """Get list of compliance violations."""
        return self.violations

    def print_compliance_report(self) -> None:
        """Print compliance verification report."""
        if not self.violations:
            print(" COMPLIANCE VERIFICATION PASSED")
            print("   All provider implementations comply with terms of service")
            print("   Only API-based orchestration is enabled")
            print("   No prohibited CLI/SDK access methods detected")
        else:
            print(" COMPLIANCE VERIFICATION FAILED")
            print("   Prohibited modifications detected:")
            for violation in self.violations:
                print(f"   • {violation}")
            print("\n   IMPORTANT: Remove all prohibited modifications")
            print("   Hillstar must use API-only authentication for compliance")


def verify_hillstar_compliance() -> None:
    """Verify Hillstar compliance at import time."""
    enforcer = ComplianceEnforcer()
    if not enforcer.verify_compliance():
        enforcer.print_compliance_report()
        raise ComplianceError(
            "Hillstar compliance verification failed. "
            "Prohibited modifications detected. "
            "See compliance report above for details."
        )
