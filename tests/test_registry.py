from __future__ import annotations

import unittest
from pathlib import Path

from probe.registry import load_registry, repo_root
from probe.sse import inspect_stream


class RegistryTests(unittest.TestCase):
    def test_every_registered_check_has_page_and_runner(self) -> None:
        root = repo_root()
        for spec in load_registry():
            folder = root / "checks" / spec["id"]
            self.assertTrue((folder / "check.py").is_file(), spec["id"])
            self.assertTrue((folder / "page.md").is_file(), spec["id"])
            self.assertIn("run", (folder / "check.py").read_text())

    def test_verdict_helpers_do_not_import_opencrabs(self) -> None:
        text = Path(__file__).resolve().parents[1].joinpath("probe/sse.py").read_text()
        self.assertNotIn("is_some", text)
        self.assertNotIn("opencrabs", text.lower())
        inspect_stream  # imported for the contract module to stay wired


if __name__ == "__main__":
    unittest.main()
