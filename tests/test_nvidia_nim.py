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
        self.assertEqual(
            post.call_args.kwargs["json"]["chat_template_kwargs"],
            {"enable_thinking": False},
        )

    def test_parse_source_index_accepts_brackets_and_trailing_punctuation(self) -> None:
        bracketed = generate.parse_llm_output(
            "CATEGORY: technology\nTITLE: A sufficiently descriptive test title\n"
            "EXCERPT: A sufficiently descriptive excerpt for this test.\n"
            "SOURCE_INDEX: [2]\nBODY:\n<p>Body text.</p>"
        )
        punctuated = generate.parse_llm_output(
            "CATEGORY: technology\nTITLE: A sufficiently descriptive test title\n"
            "EXCERPT: A sufficiently descriptive excerpt for this test.\n"
            "SOURCE_INDEX: 3.\nBODY:\n<p>Body text.</p>"
        )
        self.assertEqual(bracketed["source_index"], 2)
        self.assertEqual(punctuated["source_index"], 3)

    def test_retries_once_when_model_returns_invalid_source_index(self) -> None:
        articles = [
            {
                "title": "A source article title",
                "description": "Source description",
                "url": "https://example.com/source",
                "source": "Example",
                "publishedAt": "2026-11-20T00:00:00Z",
            }
        ]
        invalid = (
            "CATEGORY: technology\nTITLE: A sufficiently descriptive test title\n"
            "EXCERPT: A sufficiently descriptive excerpt for this test.\n"
            "SOURCE_INDEX: 0\nBODY:\n<p>Body text.</p>"
        )
        valid = (
            "CATEGORY: technology\nTITLE: A sufficiently descriptive test title\n"
            "EXCERPT: A sufficiently descriptive excerpt for this test.\n"
            `SOURCE_INDEX: 1\nBODY:\n<p>${"editorial ".repeat(500).trim()}</p>`
        )
        with patch.object(generate, "NVIDIA_MODEL", "nvidia/test-model"):
            with patch.object(generate, "NVIDIA_FALLBACK_MODELS", []):
                with patch("generate.nvidia_nim_call", side_effect=[invalid, valid]) as call:
                    with patch("generate.title_is_duplicate", return_value=False):
                        result, model = generate.generated_post(
                            articles, [], "nvidia-test-key", provider="nvidia"
                        )
        self.assertEqual(call.call_count, 2)
        self.assertIn("one-based", call.call_args.args[2])
        self.assertEqual(result["source"], articles[0])
        self.assertEqual(model, "nvidia:nvidia/test-model")

    def test_retries_when_article_body_is_too_short(self) -> None:
        article = {
            "title": "A source article title",
            "description": "Source description",
            "url": "https://example.com/source",
            "source": "Example",
            "publishedAt": "2026-11-20T00:00:00Z",
        }
        short_body = "<p>" + " ".join(["draft"] * 250) + "</p>"
        complete_body = "<p>" + " ".join(["editorial"] * 510) + "</p>"

        def output(body: str) -> str:
            return (
                "CATEGORY: technology\\n"
                "TITLE: A sufficiently descriptive editorial title\\n"
                "EXCERPT: A sufficiently descriptive excerpt for this article.\\n"
                "SOURCE_INDEX: 1\\n"
                f"BODY:\\n{body}"
            )

        with patch.object(generate, "NVIDIA_MODEL", "nvidia/test-model"):
            with patch.object(generate, "NVIDIA_FALLBACK_MODELS", []):
                with patch(
                    "generate.nvidia_nim_call",
                    side_effect=[output(short_body), output(complete_body)],
                ) as call:
                    with patch("generate.title_is_duplicate", return_value=False):
                        result, model = generate.generated_post(
                            [article], [], "nvidia-test-key", provider="nvidia"
                        )

        self.assertEqual(call.call_count, 2)
        self.assertIn("500–520 words", call.call_args.args[2])
        self.assertEqual(len(generate.clean_text(result["body"]).split()), 510)
        self.assertEqual(result["source"], article)
        self.assertEqual(model, "nvidia:nvidia/test-model")

    def test_does_not_return_a_short_article_after_retry_limit(self) -> None:
        article = {
            "title": "A source article title",
            "description": "Source description",
            "url": "https://example.com/source",
            "source": "Example",
            "publishedAt": "2026-11-20T00:00:00Z",
        }
        short_output = (
            "CATEGORY: technology\\n"
            "TITLE: A sufficiently descriptive editorial title\\n"
            "EXCERPT: A sufficiently descriptive excerpt for this article.\\n"
            "SOURCE_INDEX: 1\\n"
            "<p>" + " ".join(["draft"] * 250) + "</p>"
        )
        with patch.object(generate, "NVIDIA_MODEL", "nvidia/test-model"):
            with patch.object(generate, "NVIDIA_FALLBACK_MODELS", []):
                with patch("generate.nvidia_nim_call", return_value=short_output) as call:
                    with patch("generate.title_is_duplicate", return_value=False):
                        with self.assertRaisesRegex(
                            RuntimeError, "draft failed validation after 3 attempts"
                        ):
                            generate.generated_post(
                                [article], [], "nvidia-test-key", provider="nvidia"
                            )
        self.assertEqual(call.call_count, 3)

    def test_reports_empty_nemotron_answer_without_leaking_response_content(self) -> None:
        response = FakeResponse(
            200,
            {
                "choices": [
                    {
                        "message": {"content": ""},
                        "finish_reason": "length",
                    }
                ],
                "usage": {
                    "completion_tokens": 2048,
                    "completion_tokens_details": {"reasoning_tokens": 2048},
                },
            },
        )
        with patch.object(generate, "NVIDIA_BASE_URL", "https://nim.example/v1"):
            with patch.dict(os.environ, {"NVIDIA_MAX_TOKENS": "2048"}):
                with patch("generate.requests.post", return_value=response):
                    with self.assertRaisesRegex(
                        ValueError,
                        "finish_reason=length, completion_tokens=2048, reasoning_tokens=2048",
                    ):
                        generate.nvidia_nim_call("nvidia-test-key", "nvidia/test-model", "test prompt")

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

    def test_switches_to_an_available_model_when_configured_model_is_retired(self) -> None:
        payload = {
            "data": [
                {"id": "nvidia/nemotron-3.5-lightning-30b-a3b"},
                {"id": "meta/llama-3.3-70b-instruct"},
            ]
        }
        with patch.object(generate, "NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"):
            with patch.object(generate, "NVIDIA_FALLBACK_MODELS", []):
                with patch.object(generate, "NVIDIA_BASE_URL", "https://nim.example/v1"):
                    with patch(
                        "generate.requests.get",
                        return_value=FakeResponse(200, payload),
                    ):
                        generate.check_ai_provider_api("nvidia-test-key", "nvidia")
                self.assertEqual(
                    generate.NVIDIA_MODEL,
                    "nvidia/nemotron-3.5-lightning-30b-a3b",
                )

    def test_reports_available_models_when_no_supported_model_is_listed(self) -> None:
        payload = {"data": [{"id": "some/other-model"}]}
        with patch.object(generate, "NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"):
            with patch.object(generate, "NVIDIA_FALLBACK_MODELS", []):
                with patch.object(generate, "NVIDIA_BASE_URL", "https://nim.example/v1"):
                    with patch(
                        "generate.requests.get",
                        return_value=FakeResponse(200, payload),
                    ):
                        with self.assertRaisesRegex(RuntimeError, "available models include"):
                            generate.check_ai_provider_api("nvidia-test-key", "nvidia")

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
