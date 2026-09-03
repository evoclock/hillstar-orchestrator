# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Authentication-mode tests for mcp-server/openai_mcp_server.py.

Covers:
1. Subscription success (no OPENAI_API_KEY required)
2. Missing subscription token without subscription-only mode (default
   fallback behavior preserved)
3. Subscription-only mode: missing token is a hard failure that never
   falls back to an API key, even when OPENAI_API_KEY is set.
"""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp-server" / "openai_mcp_server.py"


def load_server_class():
    mcp_dir = str(SERVER_PATH.parent)
    if mcp_dir not in sys.path:
        sys.path.insert(0, mcp_dir)
    spec = importlib.util.spec_from_file_location("openai_mcp_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["openai_mcp_server"] = module
    spec.loader.exec_module(module)
    return module.OpenAIMCPServer


@pytest.fixture
def server_class():
    return load_server_class()


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """Isolate token lookup from the developer's real ~/.codex."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    return tmp_path


def write_auth(tmp_path, token="jwt-token-abc"):
    auth_file = tmp_path / "auth.json"
    auth_file.write_text(json.dumps({"tokens": {"access_token": token}}))
    return auth_file


def test_subscription_mode_works_without_api_key(server_class, isolated_home, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_CHATGPT_LOGIN_MODE", "true")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    write_auth(tmp_path)

    with patch.object(sys.modules["openai_mcp_server"], "OpenAI", MagicMock()):
        server = server_class()

    assert server.auth_mode == "subscription"
    assert server.subscription_token == "jwt-token-abc"
    assert server.client is None


def test_missing_subscription_falls_back_by_default(server_class, isolated_home, tmp_path, monkeypatch):
    """Default Hillstar behavior is unchanged: fallback to API key is allowed."""
    monkeypatch.setenv("OPENAI_CHATGPT_LOGIN_MODE", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    with patch.dict(sys.modules, {"openai": MagicMock()}):
        server = server_class()

    assert server.auth_mode == "api_key"


def test_subscription_only_rejects_api_key_fallback(server_class, isolated_home, tmp_path, monkeypatch):
    """Subscription-only mode must exit even when OPENAI_API_KEY is set."""
    monkeypatch.setenv("HILLSTAR_OPENAI_SUBSCRIPTION_ONLY", "true")
    monkeypatch.setenv("OPENAI_CHATGPT_LOGIN_MODE", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-never-be-used")

    with pytest.raises(SystemExit) as excinfo:
        server_class()

    assert excinfo.value.code == 1


def test_subscription_only_requires_subscription_flag(server_class, isolated_home, monkeypatch):
    """Subscription-only mode without OPENAI_CHATGPT_LOGIN_MODE also fails hard."""
    monkeypatch.setenv("HILLSTAR_OPENAI_SUBSCRIPTION_ONLY", "true")
    monkeypatch.delenv("OPENAI_CHATGPT_LOGIN_MODE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SystemExit):
        server_class()


def test_default_mode_still_requires_api_key(server_class, isolated_home, monkeypatch):
    """Unchanged default: no subscription, no key, no subscription-only -> exit 1."""
    monkeypatch.delenv("OPENAI_CHATGPT_LOGIN_MODE", raising=False)
    monkeypatch.delenv("HILLSTAR_OPENAI_SUBSCRIPTION_ONLY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SystemExit):
        server_class()
