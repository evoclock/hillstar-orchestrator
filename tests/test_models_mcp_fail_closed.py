# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-only

"""Fail-closed regression tests for empty/malformed MCP responses.

models/mcp_model.py must not turn an empty or malformed MCP tools/call
result into a successful "No output" output value. Each bad shape must
return a typed error result with output=None.
"""

from models.mcp_model import MCPModel


def make_model():
    return MCPModel(
        provider="ollama_mcp",
        model_name="devstral-2",
        server_script="mcp-server/ollama_mcp_server.py",
        api_key=None,
    )


def call_with_result(model, result):
    model._ensure_process = lambda: None
    model._send_request = lambda request: {"result": result}
    return model.call("prompt", max_tokens=32)


def test_missing_content_fails_closed():
    model = make_model()
    result = call_with_result(model, {})

    assert result["output"] is None
    assert result["error_type"] == "empty_mcp_response"
    assert result["provider"] == "ollama_mcp"


def test_empty_content_list_fails_closed():
    model = make_model()
    result = call_with_result(model, {"content": []})

    assert result["output"] is None
    assert result["error_type"] == "empty_mcp_response"


def test_malformed_content_entry_fails_closed():
    model = make_model()
    result = call_with_result(model, {"content": [{"no_text_field": True}]})

    assert result["output"] is None
    assert result["error_type"] == "empty_mcp_response"


def test_whitespace_text_fails_closed():
    model = make_model()
    result = call_with_result(model, {"content": [{"text": "   \n  "}]})

    assert result["output"] is None
    assert result["error_type"] == "empty_mcp_response"


def test_valid_content_still_succeeds():
    model = make_model()
    result = call_with_result(model, {"content": [{"text": "real answer"}]})

    assert result["output"] == "real answer"
    assert "error" not in result or result.get("error") is None
    assert result["provider"] == "ollama_mcp"
