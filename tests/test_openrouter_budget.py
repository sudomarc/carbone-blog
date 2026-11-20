from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import generate


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class OpenRouterBudgetTests(unittest.TestCase):
    def test_retries_below_provider_budget(self) -> None:
        responses = [
            FakeResponse(402, {"error": {"message": "You requested 4096 tokens, but can only afford 771."}}),
            FakeResponse(200, {"choices": [{"message": {"content": "generated article"}}]}),
        ]
        with patch.dict(os.environ, {"OPENROUTER_MAX_TOKENS": "4096"}):
            with patch("generate.requests.post", side_effect=responses) as post:
                result = generate.openrouter_call("test-key", "test-model", "test prompt")

        self.assertEqual(result, "generated article")
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args_list[0].kwargs["json"]["max_tokens"], 4096)
        self.assertEqual(post.call_args_list[1].kwargs["json"]["max_tokens"], 755)

    def test_fails_clearly_when_credit_budget_is_too_low(self) -> None:
        response = FakeResponse(402, {"error": {"message": "You can only afford 600 tokens."}})
        with patch.dict(os.environ, {"OPENROUTER_MAX_TOKENS": "760"}):
            with patch("generate.requests.post", return_value=response) as post:
                with self.assertRaisesRegex(RuntimeError, "credits are insufficient"):
                    generate.openrouter_call("test-key", "test-model", "test prompt")

        post.assert_called_once()

    def test_provider_error_does_not_leak_key_or_url(self) -> None:
        secret = "test-secret-key"
        response = FakeResponse(
            500,
            {"error": {"message": f"Request failed at https://openrouter.ai/workspaces/default/keys/test-id using {secret}"}},
        )
        with patch.dict(os.environ, {"OPENROUTER_MAX_TOKENS": "760"}):
            with patch("generate.requests.post", return_value=response):
                with self.assertRaises(RuntimeError) as raised:
                    generate.openrouter_call(secret, "test-model", "test prompt")

        message = str(raised.exception)
        self.assertNotIn(secret, message)
        self.assertNotIn("https://openrouter.ai/", message)
        self.assertIn("[provider URL redacted]", message)


if __name__ == "__main__":
    unittest.main()
