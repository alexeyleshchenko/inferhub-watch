from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "site"))

import cellcopy  # noqa: E402


class CellCopyTests(unittest.TestCase):
    def test_tools_fail_explains_empty_strings(self) -> None:
        note = cellcopy.note(
            {
                "check_id": "stream_tools",
                "status": "fail",
                "summary": '6 chunks with finish_reason ""; 5 tool deltas with name "".',
                "evidence": {
                    "chunk_count": 7,
                    "empty_finish_chunks": 6,
                    "empty_name_chunks": 5,
                    "names": ["get_weather"],
                },
            }
        )
        self.assertIn("Not the OpenAI stream shape", note)
        self.assertIn("null", note)
        self.assertIn('""', note)

    def test_tools_pass_names_the_call(self) -> None:
        note = cellcopy.note(
            {
                "check_id": "stream_tools",
                "status": "pass",
                "summary": "Named tools: get_weather.",
                "evidence": {"names": ["get_weather"], "empty_finish_chunks": 0},
            }
        )
        self.assertIn("get_weather", note)
        self.assertIn("empty string", note)

    def test_cache_pass_uses_fraction(self) -> None:
        note = cellcopy.note(
            {
                "check_id": "cache_tools",
                "status": "pass",
                "summary": "Cache hit (1484 tokens) on a streaming completion without tools.",
                "evidence": {
                    "cached_tokens": 1484,
                    "usage": {"prompt_tokens": 1962},
                },
            }
        )
        self.assertIn("1484 of 1962", note)
        self.assertIn("reused", note)

    def test_price_is_info(self) -> None:
        note = cellcopy.note(
            {
                "check_id": "usage_pricing",
                "status": "info",
                "summary": "cost=0.01",
                "evidence": {"usage": {"cost": 0.01}},
            }
        )
        self.assertIn("cost=0.01", note)
        self.assertIn("not part of Safe to use", note)
        self.assertIn("Info only", note)


if __name__ == "__main__":
    unittest.main()
