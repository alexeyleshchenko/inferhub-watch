from __future__ import annotations

import json
import unittest

from probe.registry import load_check_module


class _Fake:
    def __init__(self, body: dict, status: int = 200) -> None:
        self.body = json.dumps(body)
        self.status = status

    def post(self, payload: dict) -> tuple[int, str, float]:
        return self.status, self.body, 1.0


def _body(*, names: list[str], reason: str = "tool_calls") -> dict:
    return {
        "model": "cb/gpt-5.6-luna",
        "choices": [
            {
                "finish_reason": reason,
                "message": {
                    "tool_calls": [
                        {"function": {"name": n, "arguments": "{}"}} for n in names
                    ]
                },
            }
        ],
    }


class NonstreamToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_check_module("nonstream_tools")

    def test_named_list_passes(self) -> None:
        out = self.check.run(_Fake(_body(names=["get_weather"])), "gpt-5.6-luna")
        self.assertEqual(out["status"], "pass")
        self.assertIn("get_weather", out["summary"])

    def test_empty_list_with_tool_calls_reason_fails(self) -> None:
        body = {
            "choices": [
                {"finish_reason": "tool_calls", "message": {"tool_calls": []}}
            ]
        }
        out = self.check.run(_Fake(body), "gpt-5.6-luna")
        self.assertEqual(out["status"], "fail")
        self.assertIn("empty", out["summary"])

    def test_blank_function_name_fails(self) -> None:
        out = self.check.run(_Fake(_body(names=[""])), "gpt-5.6-luna")
        self.assertEqual(out["status"], "fail")
        self.assertIn("blank", out["summary"])


if __name__ == "__main__":
    unittest.main()
