from __future__ import annotations

import unittest

from probe.publishers import publisher_label


class PublisherLabelTests(unittest.TestCase):
    def test_cline_pass(self) -> None:
        self.assertIn("ClinePass", publisher_label("cp/cline-pass/deepseek-v4-pro"))
        self.assertIn(
            "cp/cline-pass/deepseek-v4-pro",
            publisher_label("cp/cline-pass/deepseek-v4-pro"),
        )

    def test_cmc_org(self) -> None:
        self.assertTrue(
            publisher_label("cmc/deepseek/deepseek-v4-flash").startswith("deepseek")
        )

    def test_unknown_prefix_keeps_full_id(self) -> None:
        self.assertIn("cb/gpt-5.6-luna", publisher_label("cb/gpt-5.6-luna"))


if __name__ == "__main__":
    unittest.main()
