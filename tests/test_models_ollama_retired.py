# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-only

"""Regression tests for Ollama HTTP 410 retired-model handling.

Covers the typed `model_retired` result introduced in
models/ollama_api_model.py: an HTTP 410 Gone response must become a typed
error result rather than a generic exception, while all other HTTP errors
keep the pre-existing behavior (generic error dict from the outer handler).
"""

from unittest.mock import MagicMock, patch

from models.ollama_api_model import OllamaAPIModel


def status_response(status_code):
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status.side_effect = __import__("requests").exceptions.HTTPError(
        f"{status_code} error"
    )
    return response


def test_http_410_returns_typed_model_retired_result():
    model = OllamaAPIModel(model_name="minimax-m2.5:cloud", endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch("models.ollama_api_model.requests.post", return_value=status_response(410)):
            result = model.call("prompt", max_tokens=64)

    assert result["output"] is None
    assert result["error_type"] == "model_retired"
    assert result["status_code"] == 410
    assert result["model"] == "minimax-m2.5:cloud"
    assert result["provider"] == "ollama"
    assert "410" in result["error"]
    assert "model_retired" != result.get("error")  # error is a message string


def test_http_410_error_message_names_the_model():
    model = OllamaAPIModel(model_name="devstral-2:123b-cloud", endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch("models.ollama_api_model.requests.post", return_value=status_response(410)):
            result = model.call("prompt")

    assert "devstral-2:123b-cloud" in result["error"]


def test_other_http_errors_are_not_reported_as_model_retired():
    model = OllamaAPIModel(model_name="minimax-m2.5:cloud", endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch("models.ollama_api_model.requests.post", return_value=status_response(404)):
            result = model.call("prompt")

    assert result["output"] is None
    assert result.get("error_type") != "model_retired"
    assert result.get("status_code") != 410
    assert result["provider"] == "ollama"


def test_success_still_returns_output_after_410_guard():
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": "hello"}}],
        "usage": {"total_tokens": 7},
    }
    model = OllamaAPIModel(model_name="minimax-m2.5:cloud", endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch("models.ollama_api_model.requests.post", return_value=response):
            result = model.call("prompt")

    assert result["output"] == "hello"
    assert result["tokens_used"] == 7
    assert result["provider"] == "ollama"
