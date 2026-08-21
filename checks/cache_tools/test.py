from __future__ import annotations

import json
import unittest

from probe.registry import load_check_module


class _Seq:
    def __init__(self, bodies: list[dict]) -> None:
        self.bodies = [json.dumps(b) for b in bodies]

    def post(self, payload: dict) -> tuple[int, str, float]:
        return 200, self.bodies.pop(0), 1.0


def _body(*, names: list[str], cached: int = 0) -> dict:
    usage: dict = {"prompt_tokens": 100}
    if cached:
        usage["prompt_tokens_details"] = {"cached_tokens": cached}
    return {
        "model": "cb/gpt-5.6-luna",
        "usage": usage,
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "tool_calls": [
                        {"function": {"name": n, "arguments": "{}"}} for n in names
                    ]
                },
            }
        ],
    }


class CacheToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_check_module("cache_tools")

    def test_cache_hit_with_named_tools_passes(self) -> None:
        client = _Seq(
            [
                _body(names=["get_weather"], cached=0),
                _body(names=["get_weather"], cached=80),
            ]
        )
        out = self.check.run(client, "gpt-5.6-luna")
        self.assertEqual(out["status"], "pass")
        self.assertIn("Cache hit", out["summary"])

    def test_cache_hit_with_blank_tools_fails(self) -> None:
        client = _Seq([_body(names=[""], cached=40)] * 3)
        out = self.check.run(client, "gpt-5.6-luna")
        self.assertEqual(out["status"], "fail")
        self.assertIn("Cache hit", out["summary"])

    def test_miss_with_named_tools_still_passes(self) -> None:
        client = _Seq([_body(names=["get_weather"], cached=0)] * 3)
        out = self.check.run(client, "gpt-5.6-luna")
        self.assertEqual(out["status"], "pass")
        self.assertIn("No cache hit", out["summary"])


if __name__ == "__main__":
    unittest.main()
