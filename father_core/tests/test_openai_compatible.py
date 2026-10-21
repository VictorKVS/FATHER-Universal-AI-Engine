from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from father_core.adapters.base import ModelAdapterError
from father_core.adapters.openai_compatible import OpenAICompatibleAdapter
from father_core.contracts import ModelRequest
from father_core.zoo import Zoo


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class OpenAICompatibleAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model_spec = Zoo(REPO_ROOT).model(
            "FATHER-LLM-OPENAI-COMPAT-001"
        )
        self.request = ModelRequest(
            run_id="RUN-TEST",
            model_id="FATHER-LLM-OPENAI-COMPAT-001",
            messages=[
                {"role": "system", "content": "Return result only."},
                {"role": "user", "content": "hello"},
            ],
            parameters={"temperature": 0.2},
        )

    def test_adapter_normalizes_chat_completion(self) -> None:
        secret = "provider-secret"
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(
                {
                    "id": "resp-1",
                    "choices": [
                        {
                            "message": {"content": "model answer"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 4,
                        "completion_tokens": 2,
                    },
                }
            )

        with (
            patch.dict(
                os.environ,
                {
                    "FATHER_LLM_BASE_URL": "http://127.0.0.1:11434/v1",
                    "FATHER_LLM_MODEL": "local-model",
                    "FATHER_LLM_API_KEY": secret,
                },
                clear=False,
            ),
            patch(
                "father_core.adapters.openai_compatible.urlopen",
                side_effect=fake_urlopen,
            ),
        ):
            response = OpenAICompatibleAdapter().generate(
                self.request,
                self.model_spec,
            )

        self.assertEqual(response.content, "model answer")
        self.assertEqual(
            response.metadata["provider_model"],
            "local-model",
        )
        body = json.loads(captured["request"].data.decode("utf-8"))
        self.assertEqual(body["model"], "local-model")
        self.assertEqual(body["messages"][-1]["content"], "hello")
        self.assertEqual(captured["timeout"], 60.0)
        self.assertNotIn(
            secret,
            json.dumps(response.to_dict()),
        )

    def test_missing_endpoint_configuration_fails_closed(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FATHER_LLM_BASE_URL": "",
                "FATHER_LLM_MODEL": "",
                "FATHER_LLM_API_KEY": "",
            },
            clear=False,
        ):
            with self.assertRaises(ModelAdapterError):
                OpenAICompatibleAdapter().generate(
                    self.request,
                    self.model_spec,
                )


if __name__ == "__main__":
    unittest.main()
