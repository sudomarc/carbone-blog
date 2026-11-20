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


class NvidiaNimTests(unittest.TestCase):
    def test_uses_nvidia_openai_compatible_endpoint(self) -> None:
        with patch.object(generate, "NVIDIA_BASE_URL", "https://nim.example/v1"):
            with patch.dict(os.environ, {"NVIDIA_MAX_TOKENS": "1800"}):
                with patch(
                    "generate.requests.post",
                    return_value=FakeResponse(
                        200,
                        {"choices": [{"message": {"content": "generated article"}}]},
                    ),
                ) as post:
                    result = generate.nvidia_nim_call("nvidia-test-key", "meta/test-model", "test prompt")

        self.assertEqual(result, "generated article")
        self.assertEqual(post.call_args.args[0], "https://nim.example/v1/chat/completions")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer nvidia-test-key")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "meta/test-model")
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 1800)

    def test_redacts_key_and_provider_urls_on_error(self) -> None:
        secret = "nvidia-test-secret"
        response = FakeResponse(
            500,
            {"error": {"message": f"failure at https://integrate.api.nvidia.com/debug with {secret}"}},
        )
        with patch.object(generate, "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"):
            with patch.dict(os.environ, {"NVIDIA_MAX_TOKENS": "2048"}):
                with patch("generate.requests.post", return_value=response):
                    with self.assertRaises(RuntimeError) as raised:
                        generate.nvidia_nim_call(secret, "meta/test-model", "test prompt")

        message = str(raised.exception)
        self.assertNotIn(secret, message)
        self.assertNotIn("https://integrate.api.nvidia.com/", message)
        self.assertIn("[provider URL redacted]", message)

    def test_nvidia_is_the_default_provider(self) -> None:
        with patch.dict(os.environ, {"AI_PROVIDER": "nvidia"}):
            self.assertEqual(generate.selected_ai_provider(), "nvidia")

    def test_openrouter_remains_an_explicit_legacy_provider(self) -> None:
        with patch.dict(os.environ, {"AI_PROVIDER": "openrouter"}):
            self.assertEqual(generate.selected_ai_provider(), "openrouter")

    def test_unknown_provider_is_rejected(self) -> None:
        with patch.dict(os.environ, {"AI_PROVIDER": "unknown"}):
            with self.assertRaisesRegex(ValueError, "AI_PROVIDER must be"):
                generate.selected_ai_provider()


if __name__ == "__main__":
    unittest.main()
