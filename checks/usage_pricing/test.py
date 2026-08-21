from __future__ import annotations

import json
import unittest

from probe.registry import load_check_module, load_registry


def _sse(chunks: list[dict]) -> str:
    return "".join(f"data: {json.dumps(c)}\n" for c in chunks) + "data: [DONE]\n"


class _Fake:
    def __init__(self, chunks: list[dict]) -> None:
        self.body = _sse(chunks)

    def post(self, payload: dict) -> tuple[int, str, float]:
        return 200, self.body, 1.0


class UsagePricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.check = load_check_module("usage_pricing")

    def test_registry_says_price_never_ranks(self) -> None:
        spec = next(s for s in load_registry() if s["id"] == "usage_pricing")
        self.assertFalse(spec["scores_rank"])

    def test_price_fields_are_info_not_fail(self) -> None:
        chunks = [
            {"model": "cb/x", "choices": [{"delta": {}, "finish_reason": "stop"}]},
            {"usage": {"cost": 0.01, "prompt_tokens": 10}},
        ]
        out = self.check.run(_Fake(chunks), "gpt-5.6-luna")
        self.assertEqual(out["status"], "info")
        self.assertIn("cost=", out["summary"])
        self.assertIn("USDC", out["summary"])

    def test_tokens_only_is_info_not_fail(self) -> None:
        chunks = [{"usage": {"prompt_tokens": 10}}]
        out = self.check.run(_Fake(chunks), "gpt-5.6-luna")
        self.assertEqual(out["status"], "info")
        self.assertIn("tokens_only", out["summary"])

    def test_credit_not_merged_with_cost_as_same_unit(self) -> None:
        chunks = [{"usage": {"cost": 0.001, "credit": 0.01}}]
        out = self.check.run(_Fake(chunks), "gpt-5.6-luna")
        self.assertIn("not treated as the same unit", out["summary"])


if __name__ == "__main__":
    unittest.main()
