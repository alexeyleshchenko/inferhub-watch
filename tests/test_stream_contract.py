from __future__ import annotations

import unittest

from probe.sse import inspect_stream


class StreamContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
