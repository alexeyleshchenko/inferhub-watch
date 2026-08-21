from __future__ import annotations

import json
import unittest

from probe.payloads import (
    CACHE_PREFIX_MIN_TOKENS,
    approx_prompt_tokens,
    cache_payload,
    cache_prefix,
)
from probe.registry import load_check_module
from probe.sse import cached_tokens


def _sse(chunks: list[dict]) -> str:
    return "".join(f"data: {json.dumps(c)}\n" for c in chunks) + "data: [DONE]\n"


class _Seq:
    def __init__(self, chunk_lists: list[list[dict]]) -> None:
        self.bodies = [_sse(c) for c in chunk_lists]
        self.payloads: list[dict] = []

    def post(self, payload: dict) -> tuple[int, str, float]:
        self.payloads.append(payload)
        return 200, self.bodies.pop(0), 1.0


def _chunks(*, cached: int = 0) -> list[dict]:
    return [
        {
            "model": "cb/gpt-5.6-luna",
            "choices": [{"delta": {"content": "paris"}, "finish_reason": None}],
        },
        {
            "choices": [{"delta": {}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": 100,
                "prompt_tokens_details": {"cached_tokens": cached},
            },
        },
    ]


class CacheToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_check_module("cache_tools")
        cls._pause = cls.check.RETRY_PAUSE_S
        cls.check.RETRY_PAUSE_S = 0

    @classmethod
    def tearDownClass(cls) -> None:
        cls.check.RETRY_PAUSE_S = cls._pause

    def test_request_has_no_tools(self) -> None:
        client = _Seq([_chunks(cached=80)])
        self.check.run(client, "gpt-5.6-luna")
        payload = client.payloads[0]
        self.assertTrue(payload.get("stream"))
        self.assertNotIn("tools", payload)
        self.assertNotIn("tool_choice", payload)

    def test_cache_hit_passes(self) -> None:
        client = _Seq([_chunks(cached=0), _chunks(cached=80)])
        out = self.check.run(client, "gpt-5.6-luna")
        self.assertEqual(out["status"], "pass")
        self.assertIn("Cache hit", out["summary"])
        self.assertNotIn("get_weather", out["summary"])

    def test_miss_after_three_attempts_fails(self) -> None:
        client = _Seq([_chunks(cached=0)] * 3)
        out = self.check.run(client, "gpt-5.6-luna")
        self.assertEqual(out["status"], "fail")
        self.assertIn("cached_tokens", out["summary"])

    def test_prefix_clears_provider_floor(self) -> None:
        prefix = cache_prefix()
        self.assertGreaterEqual(approx_prompt_tokens(prefix), CACHE_PREFIX_MIN_TOKENS)
        payload = cache_payload("deepseek-v4-pro", prefix)
        self.assertNotIn("tools", payload)
        self.assertGreaterEqual(
            approx_prompt_tokens(payload["messages"][0]["content"]),
            CACHE_PREFIX_MIN_TOKENS,
        )

    def test_prefix_min_tokens_and_salt(self) -> None:
        small = cache_prefix(512, salt="threshold-test")
        self.assertGreaterEqual(approx_prompt_tokens(small), 512)
        self.assertLess(approx_prompt_tokens(small), CACHE_PREFIX_MIN_TOKENS)
        self.assertIn("threshold-test", small)

    def test_hit_field_is_not_only_openai_cached_tokens(self) -> None:
        self.assertEqual(cached_tokens({"prompt_cache_hit_tokens": 640}), 640)
        self.assertEqual(
            cached_tokens(
                {
                    "cached_tokens": 0,
                    "prompt_tokens_details": {"cached_tokens": 0},
                    "prompt_cache_hit_tokens": 256,
                }
            ),
            256,
        )


if __name__ == "__main__":
    unittest.main()
