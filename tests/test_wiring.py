from __future__ import annotations

import importlib.util
import os
import unittest

from probe.registry import load_registry, repo_root


def _load_generate():
    path = repo_root() / "site" / "generate.py"
    spec = importlib.util.spec_from_file_location("watch_generate", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class WiringTests(unittest.TestCase):
    def test_every_registered_check_has_page_runner_and_fixtures(self) -> None:
        root = repo_root()
        for spec in load_registry():
            folder = root / "checks" / spec["id"]
            self.assertTrue((folder / "check.py").is_file(), spec["id"])
            self.assertTrue((folder / "page.md").is_file(), spec["id"])
            self.assertTrue((folder / "test.py").is_file(), spec["id"])
            self.assertIn("run", (folder / "check.py").read_text())

    def test_verdict_helpers_do_not_import_opencrabs(self) -> None:
        text = (repo_root() / "probe" / "sse.py").read_text()
        self.assertNotIn("is_some", text)
        self.assertNotIn("opencrabs", text.lower())

    def test_generate_includes_page_md_and_no_secrets(self) -> None:
        gen = _load_generate()
        spec = next(s for s in load_registry() if s["id"] == "stream_tools")
        html = gen.check_page(spec)
        self.assertIn("stream: true", html)
        self.assertIn("get_weather", html)
        self.assertLessEqual(html.lower().count("is_some"), 1)
        self.assertNotIn(os.environ.get("INFERHUB_API_KEY") or "sk-never", html)
        self.assertNotIn("OpenCrabs", html)
        self.assertIn("platform.openai.com", html)

    def test_homepage_puts_github_in_footer_not_header(self) -> None:
        gen = _load_generate()
        html = gen.index_html(gen.load_runs(), gen.load_aliases(), gen.load_registry())
        header, _, rest = html.partition("</header>")
        footer = rest[rest.rfind("<footer>") :] if "<footer>" in rest else ""
        self.assertNotIn("github.com/alexeyleshchenko/inferhub-watch", header)
        self.assertIn("github.com/alexeyleshchenko/inferhub-watch", footer)
        self.assertIn("INFERHUB_API_KEY", footer)
        self.assertNotIn(os.environ.get("INFERHUB_API_KEY") or "sk-never", html)
        self.assertIn('class="matrix"', html)
        self.assertNotIn('class="rank-table"', html)
        self.assertIn('class="check-col"', html)
        self.assertNotIn("OpenCrabs", html)
        self.assertNotIn("Seven-day", html)
        self.assertIn("Prompt cache", html)
        mornings = gen.distinct_mornings(gen.load_runs())
        if len(mornings) < 2:
            self.assertNotIn("<h2>Mornings</h2>", html)


if __name__ == "__main__":
    unittest.main()
