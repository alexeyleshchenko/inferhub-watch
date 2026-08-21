from __future__ import annotations

import json
import unittest

from probe.registry import load_check_module
from probe.sse import inspect_stream


def _sse(chunks: list[dict]) -> str:
    return "".join(f"data: {json.dumps(chunk)}\n" for chunk in chunks) + "data: [DONE]\n"


class _Fake:
    def __init__(self, body: str, status: int = 200) -> None:
        self.body = body
        self.status = status

    def post(self, payload: dict) -> tuple[int, str, float]:
        return self.status, self.body, 1.0


class StreamToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_check_module("stream_tools")

    def test_empty_finish_reason_fails_openai_shape(self) -> None:
        chunks = [
            {
                "model": "cb/gpt-5.6-luna",
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "c1",
                                    "function": {"name": "get_weather", "arguments": ""},
                                }
                            ]
                        },
                        "finish_reason": "",
                    }
                ],
            }
        ]
        stats = inspect_stream(chunks)
        self.assertGreater(stats["empty_finish_chunks"], 0)
        self.assertIn("get_weather", stats["names"])
        out = self.check.run(_Fake(_sse(chunks)), "gpt-5.6-luna")
        self.assertEqual(out["status"], "fail")
        self.assertIn("finish_reason", out["summary"])

    def test_empty_tool_name_fails_openai_shape(self) -> None:
        chunks = [
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "function": {"name": "", "arguments": "{"},
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ]
            }
        ]
        stats = inspect_stream(chunks)
        self.assertGreater(stats["empty_name_chunks"], 0)
        self.assertEqual(stats["names"], [])
        out = self.check.run(_Fake(_sse(chunks)), "gpt-5.6-luna")
        self.assertEqual(out["status"], "fail")

    def test_null_finish_and_named_tool_is_clean(self) -> None:
        chunks = [
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "function": {"name": "get_weather", "arguments": ""},
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ]
            },
            {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]},
        ]
        stats = inspect_stream(chunks)
        self.assertEqual(stats["empty_finish_chunks"], 0)
        self.assertEqual(stats["empty_name_chunks"], 0)
        self.assertEqual(stats["names"], ["get_weather"])
        out = self.check.run(_Fake(_sse(chunks)), "gpt-5.6-luna")
        self.assertEqual(out["status"], "pass")


if __name__ == "__main__":
    unittest.main()
