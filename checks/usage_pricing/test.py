from __future__ import annotations

import json
import unittest

from probe.registry import load_check_module, load_registry


class _Fake:
    def __init__(self, body: dict) -> None:
        self.body = json.dumps(body)

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
        body = {
            "model": "cb/x",
            "usage": {"cost": 0.01, "prompt_tokens": 10},
            "choices": [{"finish_reason": "stop", "message": {}}],
        }
        out = self.check.run(_Fake(body), "gpt-5.6-luna")
        self.assertEqual(out["status"], "info")
        self.assertIn("cost=", out["summary"])

    def test_tokens_only_is_info_not_fail(self) -> None:
        body = {
            "usage": {"prompt_tokens": 10},
            "choices": [{"finish_reason": "stop", "message": {}}],
        }
        out = self.check.run(_Fake(body), "gpt-5.6-luna")
        self.assertEqual(out["status"], "info")
        self.assertIn("tokens_only", out["summary"])


if __name__ == "__main__":
    unittest.main()
