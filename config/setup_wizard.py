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

**CRITICAL SETUP REQUIREMENT:** This wizard sets up API key credentials using the
system keyring for secure storage. API keys are ESSENTIAL for using LLMs in Hillstar.

Guides users through:
1. Cloud provider API key setup (Anthropic, OpenAI, Google, Mistral) - stored in keyring
2. Local provider testing (Ollama, Devstral local)
3. Provider configuration saved to ~/.hillstar/provider_registry.json

Inputs
------
(interactive prompts with secure credential input via getpass)

Outputs
-------
- API keys: Stored securely in system keyring (not in plaintext)
- Provider config: ~/.hillstar/provider_registry.json (metadata, no secrets)

Security
--------
- API keys are NEVER stored in plaintext on disk
- Uses system keyring service (MacOS: Keychain, Linux: pass/Secret Service, Windows: Credential Manager)
- Credentials retrieved at runtime from secure storage

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-23 (added keyring-based credential storage)
"""

import getpass
import json
import keyring
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx

from .provider_registry import ProviderRegistry
from utils.credential_redactor import redact


class SetupWizard:
    """
    Interactive wizard for Hillstar provider configuration with keyring-based credential storage.

    CRITICAL: API keys are stored securely in the system keyring, NOT in plaintext files.
    This is an essential part of Hillstar setup - without API keys, the orchestrator
    cannot execute workflows that require LLM providers.
    """

    # Keyring service name for secure credential storage
    KEYRING_SERVICE = "hillstar-orchestrator"

    # Cloud providers that need API keys (stored securely in keyring)
    CLOUD_PROVIDERS = ["anthropic", "openai", "google_ai_studio", "mistral"]

    # Local providers that need connection testing
    LOCAL_PROVIDERS = ["ollama", "devstral_local", "anthropic_ollama"]

    # Phase 2 providers (skip for now)
    PHASE_2_PROVIDERS = ["google_vertex", "amazon_bedrock", "azure_ai", "cohere", "meta_llama"]

    def __init__(self):
        self.registry = ProviderRegistry()
        self.user_config: dict[str, Any] = {}
        self.tested_providers: dict[str, bool] = {}
        self.configured_credentials: dict[str, str] = {}  # Track which creds were set

    def run(self) -> None:
        """Run the setup wizard."""
        self._print_header()

        # Check existing config
        existing_path = ProviderRegistry.USER_OVERRIDE_PATH
        if existing_path.exists():
            if not self._confirm(f"Existing config found at {existing_path}. Overwrite?"):
                print("\nKeeping existing configuration.")
                return

        # Choose credential storage method
        print("\n" + "=" * 70)
        print("Credential Storage Method")
        print("=" * 70)
        print("\nHow would you like to provide API credentials?\n")
        print("  METHOD 1: Load from .env file")
        print("    - Use this if you already have an .env file with credentials")
        print("    - IMPORTANT: Ensure .env is in .gitignore permanently")
        print("    - You'll specify the path to your .env file")
        print("    - Credentials loaded from .env will be stored in system keyring\n")
        print("  METHOD 2: System Keyring (recommended for new setup)")
        print("    - Enter credentials interactively (masked/secure input)")
        print("    - Stored securely in OS-native credential storage")
        print("    - macOS: Keychain, Linux: Secret Service, Windows: Credential Manager")
        print("    - NOT stored in plaintext files anywhere\n")
        choice = self._input_choice("Choose method (1 or 2): ", ["1", "2"])

        if choice == "1":
            self._load_credentials_from_env()
        else:
            self._configure_cloud_providers_interactive()

        # Setup flow
        self._configure_local_providers()
        self._save_configuration()

    def _print_header(self) -> None:
        """Print welcome message with emphasis on credential setup importance."""
        print("\n" + "=" * 70)
        print("Hillstar Provider Setup Wizard")
        print("=" * 70)
        print("\n" + "!" * 70)
        print("! CRITICAL SETUP REQUIREMENT")
        print("!" * 70)
        print("!\n!  API keys are ESSENTIAL for using LLM providers in Hillstar.")
        print("!  Without API keys configured, workflows cannot execute.\n!")
        print("!  CREDENTIAL STORAGE OPTIONS:")
        print("!  • Point to existing .env file (keep .env in .gitignore)")
        print("!  • Enter interactively via system keyring")
        print("!  (Either way, NOT stored in plaintext files)\n!")
        print("!" * 70)

        print("\nSetup will configure:")
        print("  1. Cloud provider API keys (Anthropic, OpenAI, Google, Mistral)")
        print("     Either from .env file or interactive entry")
        print("  2. Local provider connections (Ollama, Devstral)")
        print("\nCredentials are stored securely in system keyring (NOT plaintext).")
        print("Configuration metadata saved to ~/.hillstar/provider_registry.json\n")

    def _load_credentials_from_env(self) -> None:
        """Load API keys from .env file and store in keyring."""
        print("\n" + "=" * 70)
        print("Load Credentials from .env File")
        print("=" * 70)
        print("\nSpecify the path to your .env file containing API credentials.")
        print("Example: /home/user/.env or /path/to/project/.env\n")

        env_path_input = self._input_string("Enter path to .env file", default=str(Path.home() / ".env"))
        env_path = Path(env_path_input).expanduser()

        if not env_path.exists():
            print(f"\n[ERROR] .env file not found at {env_path}")
            print("Please check the path and try again.")
            if self._confirm("Continue with interactive entry instead?"):
                self._configure_cloud_providers_interactive()
            return

        print(f"\nLoading credentials from: {env_path}")
        print("(credentials will be redacted from output for security)\n")

        # Load .env file
        env_vars = {}
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"[ERROR] Failed to read .env file: {e}")
            return

        # Map environment variables to providers and store in keyring
        env_var_mapping = {
            "anthropic": ["ANTHROPIC_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "google_ai_studio": ["GOOGLE_API_KEY"],
            "mistral": ["MISTRAL_API_KEY"],
        }

        credentials_found = 0
        for provider, env_var_names in env_var_mapping.items():
            for env_var in env_var_names:
                if env_var in env_vars:
                    api_key = env_vars[env_var]
                    provider_config = self.registry.get_provider(provider)
                    display_name = provider_config.get("display_name", provider) if provider_config else provider

                    # Store in keyring
                    try:
                        keyring.set_password(self.KEYRING_SERVICE, provider, api_key)
                        self.configured_credentials[provider] = api_key
                        credentials_found += 1
                        print(f"✓ {display_name}: Stored securely in keyring")
                    except Exception as e:
                        # Redact error message to prevent credential leakage
                        error_msg = redact(str(e))
                        print(f"✗ {display_name}: Failed to store in keyring: {error_msg}")
                    break

        if credentials_found == 0:
            print("[WARN] No recognized API keys found in .env file")
            print("Expected variables: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, MISTRAL_API_KEY")
        else:
            print(f"\n[OK] {credentials_found} credential(s) loaded and secured in system keyring")

    def _configure_cloud_providers_interactive(self) -> None:
        """Configure API keys for cloud providers with interactive prompts."""
        print("\n" + "=" * 70)
        print("Cloud Provider API Keys (Secure Storage)")
        print("=" * 70)
        print("\nEnter API keys for providers you want to use (leave empty to skip).")
        print("Keys will be stored securely in your system keyring.\n")

        for provider in self.CLOUD_PROVIDERS:
            provider_config = self.registry.get_provider(provider)
            if not provider_config:
                continue

            display_name = provider_config.get("display_name", provider)
            env_vars = provider_config.get("env_vars", [])
            api_key_var = env_vars[0] if env_vars else ""

            print(f"--- {display_name} ---")

            # Try to get existing key from keyring
            existing_key = keyring.get_password(self.KEYRING_SERVICE, provider)
            if existing_key:
                print("  [Stored in keyring]")
                if self._confirm("  Update?"):
                    api_key = self._input_api_key(f"  Enter {api_key_var}")
                    if api_key:
                        keyring.set_password(self.KEYRING_SERVICE, provider, api_key)
                        self.configured_credentials[provider] = api_key
                        print("  ✓ Updated in keyring")
                else:
                    self.configured_credentials[provider] = existing_key
            else:
                api_key = self._input_api_key(f"  Enter {api_key_var} (or leave blank to skip)")
                if api_key:
                    keyring.set_password(self.KEYRING_SERVICE, provider, api_key)
                    self.configured_credentials[provider] = api_key
                    print("  ✓ Stored securely in keyring")
                else:
                    print("  Skipping")

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
            # Redact error message to prevent credential leakage
            error_msg = redact(str(e))
            print(f"  Error: {error_msg}")
            self.tested_providers[provider] = False

    def _test_ollama_anthropic(self) -> None:
        """Test Anthropic-compatible Ollama API."""
        print("--- Anthropic via Ollama ---")

        endpoint = os.getenv("ANTHROPIC_BASE_URL", "http://localhost:11434")

        # Get first available model from anthropic_ollama provider
        anthropic_ollama_config = self.registry.get_provider("anthropic_ollama")
        available_models = list(anthropic_ollama_config.get("models", {}).keys()) if anthropic_ollama_config else []
        test_model = available_models[0] if available_models else "minimax-m2.5:cloud"

        try:
            with httpx.Client(timeout=5.0) as client:
                # Test the messages API endpoint
                response = client.post(
                    f"{endpoint}/v1/messages",
                    json={"model": test_model, "max_tokens": 10, "messages": []},
                    headers={"Authorization": f"Bearer {os.getenv('ANTHROPIC_AUTH_TOKEN', 'ollama')}"}
                )
                if response.status_code in [200, 400, 401]:
                    print(f"  Anthropic API endpoint reachable at {endpoint}")
                    if available_models:
                        print(f"  Available models: {', '.join(available_models)}")
                    print("  Configure ANTHROPIC_AUTH_TOKEN and ANTHROPIC_BASE_URL env vars")
                    self.tested_providers["anthropic_ollama"] = True
                else:
                    print(f"  Unexpected response: {response.status_code}")
        except httpx.ConnectError:
            print(f"  Cannot connect to {endpoint}")
            print("  Set ANTHROPIC_BASE_URL env var if using non-default endpoint")
            self.tested_providers["anthropic_ollama"] = False
        except Exception as e:
            # Redact error message to prevent credential leakage
            error_msg = redact(str(e))
            print(f"  Error: {error_msg}")
            self.tested_providers["anthropic_ollama"] = False

    def _save_configuration(self) -> None:
        """Save user configuration to provider_registry.json (without API keys - stored in keyring)."""
        print("\n" + "=" * 70)
        print("Saving Configuration")
        print("=" * 70)

        # Build user override config (NO API KEYS - those are in keyring)
        user_override = {
            "version": self.registry._registry.get("version", "1.0.0"),
            "last_updated": datetime.now().isoformat(),
            "description": "User configuration - merged with provider_registry.default.json. API keys stored securely in system keyring.",
            "user_overrides": {
                "providers": {}
            }
        }

        # Add local provider configs (no secrets)
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
            print("(API keys are stored securely in system keyring, NOT in this file)")
        except Exception as e:
            # Redact error message to prevent credential leakage
            error_msg = redact(str(e))
            print(f"\nFailed to save configuration: {error_msg}")
            return

        # Enhanced summary with configuration status
        print("\n" + "=" * 70)
        print("Configuration Status")
        print("=" * 70)

        # Cloud providers summary
        cloud_configured = list(self.configured_credentials.keys())
        cloud_missing = [p for p in self.CLOUD_PROVIDERS if p not in cloud_configured]
        local_tested = [p for p in self.LOCAL_PROVIDERS if self.tested_providers.get(p)]
        local_missing = [p for p in self.LOCAL_PROVIDERS if p not in local_tested]

        # Configured providers
        if cloud_configured or local_tested:
            print("\n[OK] Configured Providers:")
            if cloud_configured:
                print(f"   Cloud (in keyring): {', '.join(cloud_configured)}")
            if local_tested:
                print(f"   Local: {', '.join(local_tested)}")
        else:
            print("\n[WARN] No providers configured yet")

        # Missing providers
        if cloud_missing or local_missing:
            print("\n[WARN] Not Configured (add later if needed):")
            if cloud_missing:
                print(f"   Cloud: {', '.join(cloud_missing)}")
                print("          Run 'hillstar config' to add API keys")
            if local_missing:
                print(f"   Local: {', '.join(local_missing)}")
                print("          Start services and run 'hillstar config' to test")

        print("\n" + "=" * 70)
        print("IMPORTANT: Credential Security")
        print("=" * 70)
        print("\nYour API keys are stored securely in the system keyring:")
        print("  - macOS: ~/Library/Keychains/")
        print("  - Linux: Secret Service or pass")
        print("  - Windows: Credential Manager")
        print("\nThey are NOT stored in plaintext anywhere on disk.")
        print("The configuration file only stores provider metadata.\n")

        print("Next steps:")
        print("  1. Verify configuration: hillstar providers list")
        print("  2. Run a workflow: hillstar execute example.json")
        print("  3. Add more providers: hillstar config")

    # Input helpers
    def _input_api_key(self, prompt: str) -> str:
        """
        Get API key input from user using secure input (masked).
        Input is NOT echoed to terminal for security.
        """
        while True:
            api_key = getpass.getpass(f"{prompt}: ").strip()
            if api_key:
                return api_key
            # Allow skipping
            return ""

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
