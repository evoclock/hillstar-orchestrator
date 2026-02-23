"""
Connectivity Ping Test for MCP Servers

Purpose:
Verify that all required MCP servers are running and responding correctly
before attempting full pipeline execution.

Tests:
- Anthropic API connectivity
- OpenAI API connectivity
- Mistral API connectivity
- Ollama local endpoint
- Devstral local endpoint

Expected:
All servers respond within timeout period. Provides quick validation
that infrastructure is ready for E2E testing.

Author: Testing Suite
Created: 2026-02-22
"""

import os
import time
import pytest
import requests
from typing import Dict, Tuple


class TestConnectivityPing:
    """Ping all required MCP servers to verify they are running."""

    TIMEOUT = 5  # seconds per server
    ENDPOINTS = {
        "anthropic": {
            "type": "api",
            "endpoint": "https://api.anthropic.com/v1/messages",
            "method": "POST",
            "require_auth": True,
            "auth_header": "ANTHROPIC_API_KEY",
        },
        "openai": {
            "type": "api",
            "endpoint": "https://api.openai.com/v1/models",
            "method": "GET",
            "require_auth": True,
            "auth_header": "OPENAI_API_KEY",
        },
        "mistral": {
            "type": "api",
            "endpoint": "https://api.mistral.ai/v1/models",
            "method": "GET",
            "require_auth": True,
            "auth_header": "MISTRAL_API_KEY",
        },
        "ollama": {
            "type": "local",
            "endpoint": "http://localhost:11434/api/tags",
            "method": "GET",
            "require_auth": False,
        },
        "devstral_local": {
            "type": "local",
            "endpoint": "http://localhost:11434/api/tags",
            "method": "GET",
            "require_auth": False,
        },
    }

    def _ping_endpoint(
        self, provider: str, config: Dict
    ) -> Tuple[bool, float, str]:
        """
        Ping a server endpoint and return success status, response time, and message.

        Args:
            provider: Provider name (anthropic, openai, etc.)
            config: Endpoint configuration dictionary

        Returns:
            Tuple of (success: bool, response_time: float, message: str)
        """
        endpoint = config["endpoint"]
        method = config["method"]
        require_auth = config.get("require_auth", False)

        headers = {}
        if require_auth:
            auth_header = config.get("auth_header")
            api_key = os.environ.get(auth_header)
            if not api_key:
                return (
                    False,
                    0,
                    f"Missing {auth_header} environment variable"
                )
            # Different providers use different auth header formats
            if provider == "anthropic":
                headers["x-api-key"] = api_key
                headers["anthropic-version"] = "2023-06-01"
            elif provider in ["openai", "mistral"]:
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                headers["Authorization"] = f"Bearer {api_key}"

        try:
            start_time = time.time()

            if method == "GET":
                response = requests.get(
                    endpoint, headers=headers, timeout=self.TIMEOUT
                )
            elif method == "POST":
                # For POST, send minimal valid request body
                headers["Content-Type"] = "application/json"
                if provider == "anthropic":
                    minimal_payload = {
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                else:
                    minimal_payload = {"model": "test", "messages": []}
                response = requests.post(
                    endpoint, json=minimal_payload, headers=headers, timeout=self.TIMEOUT
                )
            else:
                return False, 0, f"Unsupported HTTP method: {method}"

            response_time = time.time() - start_time

            if response.status_code < 400:
                return True, response_time, "Server responding"
            elif response.status_code == 401:
                return (
                    False,
                    response_time,
                    "Authentication failed (invalid API key)"
                )
            elif response.status_code == 404:
                return (
                    True,
                    response_time,
                    "Endpoint returned 404 (server running, endpoint not found)"
                )
            else:
                return (
                    False,
                    response_time,
                    f"Server returned {response.status_code}"
                )

        except requests.exceptions.Timeout:
            return False, self.TIMEOUT, "Timeout (server not responding)"
        except requests.exceptions.ConnectionError:
            return False, 0, "Connection refused (server not running)"
        except Exception as e:
            return False, 0, f"Error: {str(e)}"

    def test_anthropic_connectivity(self):
        """Verify Anthropic API endpoint is reachable."""
        success, response_time, message = self._ping_endpoint(
            "anthropic", self.ENDPOINTS["anthropic"]
        )

        print(f"\nAnthropicAPI Connectivity: {message} ({response_time:.2f}s)")

        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        assert success, f"Anthropic API unreachable: {message}"
        assert response_time < self.TIMEOUT, "Anthropic API response too slow"

    def test_openai_connectivity(self):
        """Verify OpenAI API endpoint is reachable."""
        success, response_time, message = self._ping_endpoint(
            "openai", self.ENDPOINTS["openai"]
        )

        print(f"\nOpenAI API Connectivity: {message} ({response_time:.2f}s)")

        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        assert success, f"OpenAI API unreachable: {message}"
        assert response_time < self.TIMEOUT, "OpenAI API response too slow"

    def test_mistral_connectivity(self):
        """Verify Mistral API endpoint is reachable."""
        success, response_time, message = self._ping_endpoint(
            "mistral", self.ENDPOINTS["mistral"]
        )

        print(f"\nMistral API Connectivity: {message} ({response_time:.2f}s)")

        if not os.environ.get("MISTRAL_API_KEY"):
            pytest.skip("MISTRAL_API_KEY not set")

        assert success, f"Mistral API unreachable: {message}"
        assert response_time < self.TIMEOUT, "Mistral API response too slow"

    def test_ollama_connectivity(self):
        """Verify Ollama local endpoint is reachable."""
        success, response_time, message = self._ping_endpoint(
            "ollama", self.ENDPOINTS["ollama"]
        )

        print(f"\nOllama Local Connectivity: {message} ({response_time:.2f}s)")

        if not success:
            pytest.skip(
                f"Ollama not available locally: {message}"
            )

        assert success, f"Ollama unreachable: {message}"
        assert response_time < self.TIMEOUT, "Ollama response too slow"

    def test_devstral_local_connectivity(self):
        """Verify Devstral local endpoint is reachable."""
        success, response_time, message = self._ping_endpoint(
            "devstral_local", self.ENDPOINTS["devstral_local"]
        )

        print(f"\nDevstral Local Connectivity: {message} ({response_time:.2f}s)")

        if not success:
            pytest.skip(
                f"Devstral not available locally: {message}"
            )

        assert success, f"Devstral unreachable: {message}"
        assert response_time < self.TIMEOUT, "Devstral response too slow"

    def test_connectivity_summary(self):
        """Print summary of all server connectivity status."""
        print("\n" + "=" * 80)
        print("MCP Server Connectivity Summary")
        print("=" * 80)

        results = {}
        for provider, config in self.ENDPOINTS.items():
            success, response_time, message = self._ping_endpoint(
                provider, config
            )
            results[provider] = {
                "success": success,
                "response_time": response_time,
                "message": message,
            }

            status = "OK" if success else "FAIL"
            print(
                f"{provider:20} [{status:4}] {message:40} ({response_time:.2f}s)"
            )

        print("=" * 80)

        available_count = sum(
            1 for r in results.values() if r["success"]
        )
        print(f"\nServers available: {available_count}/5")

        if available_count == 0:
            pytest.skip(
                "No servers available - skipping E2E tests"
            )
