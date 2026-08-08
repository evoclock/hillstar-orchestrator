# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Regression tests for empty OpenAI-compatible chat responses."""

from unittest.mock import MagicMock, patch

import pytest

from models.jan_code_local_model import JanCodeLocalModel
from models.ollama_api_model import OllamaAPIModel


@pytest.fixture(params=[
    (JanCodeLocalModel, "models.jan_code_local_model", "jan_code_local"),
    (OllamaAPIModel, "models.ollama_api_model", "ollama"),
])
def model_case(request):
    return request.param


def response_with_content(content):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "choices": [{"message": {"content": content}}],
        "usage": {"total_tokens": 12},
    }
    return response


def test_null_content_is_a_typed_provider_error(model_case):
    model_class, module_name, provider = model_case
    model = model_class(endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch(f"{module_name}.requests.post", return_value=response_with_content(None)):
            result = model.call("prompt", max_tokens=64)

    assert result["output"] is None
    assert result["error"] == "model response contained no text content"
    assert result["provider"] == provider


def test_empty_content_is_not_reported_as_success(model_case):
    model_class, module_name, _provider = model_case
    model = model_class(endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch(f"{module_name}.requests.post", return_value=response_with_content("   ")):
            result = model.call("prompt", max_tokens=64)

    assert result["output"] is None
    assert result["error"] == "model response contained no text content"


def test_text_content_remains_normalized(model_case):
    model_class, module_name, provider = model_case
    model = model_class(endpoint="http://127.0.0.1:1")

    with patch.object(model, "_check_server", return_value=True):
        with patch(f"{module_name}.requests.post", return_value=response_with_content("  answer  ")):
            result = model.call("prompt", max_tokens=64)

    assert result["output"] == "answer"
    assert result["tokens_used"] == 12
    assert result["provider"] == provider
