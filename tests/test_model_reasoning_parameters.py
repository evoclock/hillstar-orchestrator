# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest.mock import patch

import pytest

from models.devstral_local_model import DevstralLocalModel
from models.jan_code_local_model import JanCodeLocalModel
from models.ollama_api_model import OllamaAPIModel


@pytest.mark.parametrize(
    ("module", "model"),
    [
        ("models.jan_code_local_model", JanCodeLocalModel("jan-code")),
        ("models.ollama_api_model", OllamaAPIModel("jan-code")),
        ("models.devstral_local_model", DevstralLocalModel("devstral")),
    ],
)
def test_openai_compatible_adapters_forward_reasoning_controls(module, model):
    with patch(f"{module}.requests.get") as health, patch(f"{module}.requests.post") as post:
        health.return_value.status_code = 200
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"total_tokens": 3},
        }
        result = model.call(
            prompt="test",
            reasoning_effort="high",
            thinking={"type": "enabled"},
            chat_template_kwargs={"enable_thinking": True},
        )

    assert result["output"] == "ok"
    payload = post.call_args.kwargs["json"]
    assert payload["reasoning_effort"] == "high"
    assert payload["thinking"] == {"type": "enabled"}
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}
