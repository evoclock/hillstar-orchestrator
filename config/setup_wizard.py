"""
Script
------
setup_wizard.py

Path
----
python/hillstar/config/setup_wizard.py

Purpose
-------
Interactive setup wizard for Hillstar provider configuration.

Guides users through:
1. Cloud provider API key setup (Anthropic, OpenAI, Google, Mistral)
2. Local provider testing (Ollama, Devstral local)
3. Validated config saved to ~/.hillstar/provider_registry.json

Inputs
------
(interactive prompts)

Outputs
-------
~/.hillstar/provider_registry.json with user configuration merged over defaults

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-14
"""

import json
import os
import sys
from typing import Any, Optional

import httpx

from .provider_registry import ProviderRegistry


class SetupWizard:
    """Interactive wizard for Hillstar provider configuration."""

    # Cloud providers that need API keys
    CLOUD_PROVIDERS = ["anthropic", "openai", "google_ai_studio", "mistral"]

    # Local providers that need connection testing
    LOCAL_PROVIDERS = ["ollama", "devstral_local", "anthropic_ollama"]

    # Phase 2 providers (skip for now)
    PHASE_2_PROVIDERS = ["google_vertex", "amazon_bedrock", "azure_ai", "cohere", "meta_llama"]

    def __init__(self):
        self.registry = ProviderRegistry()
        self.user_config: dict[str, Any] = {}
        self.tested_providers: dict[str, bool] = {}

    def run(self) -> None:
        """Run the setup wizard."""
        self._print_header()

        # Check existing config
        existing_path = ProviderRegistry.USER_OVERRIDE_PATH
        if existing_path.exists():
            if not self._confirm(f"Existing config found at {existing_path}. Overwrite?"):
                print("\nKeeping existing configuration.")
                return

        # Setup flow
        self._configure_cloud_providers()
        self._configure_local_providers()
        self._save_configuration()

    def _print_header(self) -> None:
        """Print welcome message."""
        print("\n" + "=" * 70)
        print("Hillstar Provider Setup Wizard")
        print("=" * 70)
        print("\nConfigure API keys and test local providers")
        print("Config will be saved to ~/.hillstar/provider_registry.json\n")

    def _configure_cloud_providers(self) -> None:
        """Configure API keys for cloud providers."""
        print("\n" + "=" * 70)
        print("Cloud Provider API Keys")
        print("=" * 70)
        print("\nEnter API keys for providers you want to use (leave empty to skip):\n")

        for provider in self.CLOUD_PROVIDERS:
            provider_config = self.registry.get_provider(provider)
            if not provider_config:
                continue

            display_name = provider_config.get("display_name", provider)
            env_vars = provider_config.get("env_vars", [])
            api_key_var = env_vars[0] if env_vars else ""

            print(f"--- {display_name} ---")

            # Check if already set in environment
            current = os.getenv(api_key_var, "")
            if current:
                print(f"  {api_key_var}: Already set (length: {len(current)})")
                if self._confirm("  Update?"):
                    new_key = self._input_string(f"  Enter {api_key_var}: ", default="")
                    if new_key:
                        self.user_config[provider] = {"api_key": new_key}
                else:
                    self.user_config[provider] = {"api_key": current}
            else:
                api_key = self._input_string(f"  Enter {api_key_var} (or press Enter to skip): ", default="")
                if api_key:
                    self.user_config[provider] = {"api_key": api_key}
                else:
                    print("  Skipping (no API key)")

    def _configure_local_providers(self) -> None:
        """Test and configure local providers."""
        print("\n" + "=" * 70)
        print("Local Provider Testing")
        print("=" * 70)
        print("\nTesting local providers...\n")

        # Test Ollama
        if self.registry.get_provider("ollama"):
            self._test_provider("ollama", "http://localhost:11434", "Ollama")

        # Test Devstral local (llama.cpp server)
        if self.registry.get_provider("devstral_local"):
            self._test_provider("devstral_local", "http://localhost:8080", "Devstral Local (llama.cpp)")

        # Test Anthropic via Ollama
        if self.registry.get_provider("anthropic_ollama"):
            self._test_ollama_anthropic()

    def _test_provider(self, provider: str, endpoint: str, display_name: str) -> None:
        """Test connection to a local provider."""
        print(f"--- {display_name} @ {endpoint} ---")

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{endpoint}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", m.get("model", "unknown")) for m in data.get("models", [])]
                    print(f"  Connected! Available models: {', '.join(models[:5])}")
                    if len(models) > 5:
                        print(f"  ... and {len(models) - 5} more")
                    self.tested_providers[provider] = True
                    self.user_config[provider] = {"endpoint": endpoint, "tested": True}
                else:
                    print(f"  Connection failed: HTTP {response.status_code}")
                    self.tested_providers[provider] = False
        except httpx.ConnectError:
            print(f"  Cannot connect to {endpoint}")
            print(f"  Make sure {display_name} is running")
            self.tested_providers[provider] = False
        except Exception as e:
            print(f"  Error: {e}")
            self.tested_providers[provider] = False

    def _test_ollama_anthropic(self) -> None:
        """Test Anthropic-compatible Ollama API."""
        print("--- Anthropic via Ollama ---")

        endpoint = os.getenv("ANTHROPIC_BASE_URL", "http://localhost:11434")
        try:
            with httpx.Client(timeout=5.0) as client:
                # Test the messages API endpoint
                response = client.post(
                    f"{endpoint}/v1/messages",
                    json={"model": "minimax-m2.1:cloud", "max_tokens": 10, "messages": []},
                    headers={"Authorization": f"Bearer {os.getenv('ANTHROPIC_AUTH_TOKEN', 'ollama')}"}
                )
                if response.status_code in [200, 400, 401]:
                    print(f"  Anthropic API endpoint reachable at {endpoint}")
                    print("  Configure ANTHROPIC_AUTH_TOKEN and ANTHROPIC_BASE_URL env vars")
                    self.tested_providers["anthropic_ollama"] = True
                else:
                    print(f"  Unexpected response: {response.status_code}")
        except httpx.ConnectError:
            print(f"  Cannot connect to {endpoint}")
            print("  Set ANTHROPIC_BASE_URL env var if using non-default endpoint")
            self.tested_providers["anthropic_ollama"] = False
        except Exception as e:
            print(f"  Error: {e}")
            self.tested_providers["anthropic_ollama"] = False

    def _save_configuration(self) -> None:
        """Save user configuration to provider_registry.json."""
        print("\n" + "=" * 70)
        print("Saving Configuration")
        print("=" * 70)

        # Build user override config
        user_override = {
            "version": self.registry._registry.get("version", "1.0.0"),
            "last_updated": "2026-02-14",
            "description": "User configuration - merged with provider_registry.default.json",
            "user_overrides": {
                "providers": {}
            }
        }

        # Add cloud provider API keys
        for provider in self.CLOUD_PROVIDERS:
            if provider in self.user_config and "api_key" in self.user_config[provider]:
                user_override["user_overrides"]["providers"][provider] = {
                    "api_key": self.user_config[provider]["api_key"]
                }

        # Add local provider configs
        for provider in self.LOCAL_PROVIDERS:
            if provider in self.user_config:
                user_override["user_overrides"]["providers"][provider] = self.user_config[provider]

        # Save
        try:
            config_path = ProviderRegistry.USER_OVERRIDE_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(user_override, f, indent=2)
            print(f"\nConfiguration saved to {config_path}")
        except Exception as e:
            print(f"\nFailed to save configuration: {e}")
            return

        # Enhanced summary with configuration status
        print("\n" + "=" * 70)
        print("Configuration Status")
        print("=" * 70)

        # Cloud providers summary
        cloud_configured = [p for p in self.CLOUD_PROVIDERS if p in self.user_config and "api_key" in self.user_config[p]]
        cloud_missing = [p for p in self.CLOUD_PROVIDERS if p not in cloud_configured]
        local_tested = [p for p in self.LOCAL_PROVIDERS if self.tested_providers.get(p)]
        local_missing = [p for p in self.LOCAL_PROVIDERS if p not in local_tested]

        # Configured providers
        if cloud_configured or local_tested:
            print("\n[OK] Configured Providers:")
            if cloud_configured:
                print(f"   Cloud: {', '.join(cloud_configured)}")
            if local_tested:
                print(f"   Local: {', '.join(local_tested)}")
        else:
            print("\n[WARN]  No providers configured yet")

        # Missing providers
        if cloud_missing or local_missing:
            print("\n[WARN]  Not Configured (add later if needed):")
            if cloud_missing:
                print(f"   Cloud: {', '.join(cloud_missing)}")
                print("          Run 'hillstar config' to add API keys")
            if local_missing:
                print(f"   Local: {', '.join(local_missing)}")
                print("          Start services and run 'hillstar config' to test")

        print("\nNext steps:")
        print("  1. Verify configuration: hillstar providers list")
        print("  2. Run a workflow: hillstar execute example.json")
        print("  3. Add more providers: hillstar config")

    # Input helpers
    def _input_string(self, prompt: str, default: Optional[str] = None) -> str:
        """Get string input from user."""
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    return default
            else:
                user_input = input(f"{prompt}").strip()
                if user_input:
                    return user_input
            print("  Please enter a value.")

    def _input_choice(self, prompt: str, choices: list[str]) -> str:
        """Get single choice from user."""
        while True:
            choice = input(prompt).strip()
            if choice in choices:
                return choice
            print(f"  Invalid choice. Please choose from: {', '.join(choices)}")

    def _confirm(self, prompt: str) -> bool:
        """Get yes/no confirmation from user."""
        while True:
            choice = input(f"{prompt} (yes/no): ").strip().lower()
            if choice in ["yes", "y"]:
                return True
            elif choice in ["no", "n"]:
                return False
            print("  Please enter 'yes' or 'no'.")


def main():
    """Entry point for setup wizard."""
    wizard = SetupWizard()
    try:
        wizard.run()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
