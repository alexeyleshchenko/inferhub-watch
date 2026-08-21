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
        self.assertNotIn('class="site-nav"', html)

    def test_homepage_puts_github_in_footer_not_header(self) -> None:
        gen = _load_generate()
        html = gen.index_html(gen.load_runs(), gen.load_aliases(), gen.load_registry())
        header, _, rest = html.partition("</header>")
        self.assertNotIn("github.com/alexeyleshchenko/inferhub-watch", header)
        self.assertNotIn("dispatch-meta", header)
        self.assertIn('class="site-nav"', header)
        self.assertIn('href="#probe"', header)
        self.assertIn('href="#earlier"', header)
        self.assertIn('href="#method"', header)
        self.assertNotIn('href="#report"', header)
        self.assertNotIn('href="#today"', header)
        self.assertNotIn('href="#notes"', header)
        self.assertIn("Ask for another", html)
        self.assertIn("/issues/new", html)
        self.assertIn("models.toml", html)
        self.assertIn("github.com/alexeyleshchenko/inferhub-watch", rest)
        self.assertIn("Run locally", rest)
        self.assertNotIn("<footer", rest)
        self.assertIn("INFERHUB_API_KEY", rest)
        self.assertNotIn(os.environ.get("INFERHUB_API_KEY") or "sk-never", html)
        self.assertIn('class="matrix"', html)
        self.assertNotIn('class="rank-table"', html)
        self.assertIn('class="check-col col-score"', html)
        self.assertIn('href="#check-stream_tools"', html)
        self.assertIn('id="check-stream_tools"', html)
        self.assertIn("<details", html)
        self.assertIn("<summary>", html)
        self.assertIn("get_weather", html)
        self.assertIn("cached_tokens", html)
        self.assertIn("platform.openai.com", html)
        thead, _, after_head = html.partition("</thead>")
        self.assertNotIn("checks/stream_tools.html", thead)
        self.assertNotIn("checks/stream_tools.html", rest[rest.find('id="method"') :])
        self.assertNotIn("OpenCrabs", html)
        self.assertNotIn("Seven-day", html)
        self.assertNotIn("Who should care", html)
        self.assertIn("Prompt cache", html)
        self.assertIn("<h2>Latest results</h2>", html)
        self.assertIn("<h2>Past runs</h2>", html)
        self.assertIn("<h2>How we test</h2>", html)
        self.assertNotIn("<h2>This probe</h2>", html)
        self.assertNotIn("<h2>Last report</h2>", html)
        self.assertNotIn("<h2>Today</h2>", html)
        self.assertNotIn("<h2>Explanations</h2>", html)
        self.assertNotIn("<h2>History</h2>", html)
        self.assertNotIn("<h2>Method</h2>", html)
        self.assertNotIn("Failed scoring checks", html)
        self.assertNotIn("<h2>Mornings</h2>", html)
        self.assertNotIn("<th>Resolved</th>", html)
        self.assertIn('class="alias-cell"', html)
        self.assertIn('class="report"', html)
        self.assertIn('class="explanations"', html)
        self.assertNotIn('class="notes"', html)
        self.assertNotIn('class="about"', html)
        self.assertNotIn('class="hero"', html)
        self.assertIn("The endpoint", html)
        self.assertNotIn("What we probe", html)
        self.assertIn("ClinePass", html)
        self.assertLess(
            html.find('class="report"'),
            html.find('class="history"'),
        )
        self.assertLess(
            html.find('id="earlier"'),
            html.find('id="method"'),
        )
        self.assertLess(
            rest.find('class="verdict"'),
            rest.find("dispatch-meta"),
        )
        self.assertLess(rest.find("dispatch-meta"), rest.find('class="matrix"'))
        self.assertIn("Last probe:", html)
        report = rest[rest.find('id="probe"') : rest.find('id="earlier"')]
        self.assertNotIn("Actions", report)
        self.assertIn("<h1>Safe to use</h1>", html)
        self.assertNotIn("Safe to use:", html)
        self.assertIn("2/2: tools + cache", html)
        self.assertNotIn("Scoring ", html)
        self.assertIn("No alias is safe to use this run.", gen.index_html(
            [
                {
                    "started_at": "2026-08-21T00:00:00",
                    "origin": "local-seed",
                    "cells": [
                        {
                            "alias": "x",
                            "check_id": "stream_tools",
                            "status": "fail",
                            "summary": "miss",
                            "resolved_model": "x",
                        },
                        {
                            "alias": "x",
                            "check_id": "cache_tools",
                            "status": "fail",
                            "summary": "miss",
                            "resolved_model": "x",
                        },
                        {
                            "alias": "x",
                            "check_id": "usage_pricing",
                            "status": "info",
                            "summary": "No price field.",
                            "resolved_model": "x",
                        },
                    ],
                }
            ],
            ["x"],
            gen.load_registry(),
        ))
        self.assertIn("check-col col-score", html)
        self.assertIn("check-col col-info", html)
        self.assertIn("info · not ranked", html)
        self.assertNotIn('class="st-info"><span class="pill"', html)
        self.assertIn('class="grid-miss"', html)
        self.assertIn("Actions · CI", html)
        self.assertIn("seed · fixture", html)
        self.assertIn("<caption>", html)
        self.assertIn('<details class="nav-menu">', html)
        self.assertIn("aria-expanded", html)
        self.assertIn("On this page", html)
        self.assertNotIn('id="nav-toggle"', html)
        self.assertLess(report.find("deepseek-v4-flash"), report.find("gpt-5.6-luna"))
        self.assertIn("Run locally", html)
        self.assertNotIn("Clone and run", html)
        self.assertNotIn("Run it yourself", html)


if __name__ == "__main__":
    unittest.main()
