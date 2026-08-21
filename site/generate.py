from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from probe.registry import load_aliases, load_registry  # noqa: E402

GITHUB = "https://github.com/alexeyleshchenko/inferhub-watch"


def base_href() -> str:
    raw = os.environ.get("PAGES_BASE", "/inferhub-watch").rstrip("/")
    return raw or ""


def md_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    list_items: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            body = inline(" ".join(para))
            out.append(f"<p>{body}</p>")
            para = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{inline(i)}</li>" for i in list_items)
            out.append(f"<ul>{items}</ul>")
            list_items = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_para()
            flush_list()
            continue
        if stripped.startswith("# "):
            flush_para()
            flush_list()
            out.append(f"<h1>{inline(stripped[2:])}</h1>")
            continue
        if stripped.startswith("## "):
            flush_para()
            flush_list()
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith("- "):
            flush_para()
            list_items.append(stripped[2:])
            continue
        para.append(stripped)
    flush_para()
    flush_list()
    return "\n".join(out)


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def load_runs() -> list[dict]:
    files = sorted((ROOT / "data" / "runs").glob("*.json"))
    runs = []
    for path in files:
        runs.append(json.loads(path.read_text()))
    return runs


def day_key(run: dict) -> str:
    raw = run.get("started_at") or ""
    return raw[:10]


def cell_map(run: dict) -> dict[tuple[str, str], dict]:
    return {(c["alias"], c["check_id"]): c for c in run.get("cells") or []}


def scoring_pass_count(run: dict, alias: str) -> tuple[int, int]:
    cmap = cell_map(run)
    ok = 0
    for check_id in ("stream_tools", "nonstream_tools", "cache_tools"):
        cell = cmap.get((alias, check_id))
        if cell and cell.get("status") == "pass":
            ok += 1
    return ok, 3


def distinct_mornings(runs: list[dict]) -> list[dict]:
    """Keep the latest run per UTC date so a seed and an Actions rerun are one morning."""
    by_day: dict[str, dict] = {}
    for run in runs:
        by_day[day_key(run)] = run
    return [by_day[key] for key in sorted(by_day)]


def origin_label(run: dict) -> str:
    raw = (run.get("origin") or "").strip()
    if raw == "github-actions":
        return "Actions"
    if raw.endswith("-seed") or "seed" in raw:
        return "seed"
    return raw or "run"


def shell(title: str, body: str, *, crumb: str = "", nested: bool = False) -> str:
    base = base_href()
    if base:
        home = f"{base}/"
        css = f"{base}/style.css"
    elif nested:
        home = "../index.html"
        css = "../style.css"
    else:
        home = "./"
        css = "style.css"
    nav = (
        f'<p class="crumb"><a href="{html.escape(home)}">InferHub Watch</a> / {html.escape(crumb)}</p>'
        if crumb
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{html.escape(css)}">
</head>
<body>
  <header class="site-header">
    <a class="mark" href="{html.escape(home)}">InferHub Watch</a>
  </header>
  <main>
    {nav}
    {body}
  </main>
  <footer>
    <p>Contributor: <a href="{GITHUB}">alexeyleshchenko/inferhub-watch</a>. How to add a check is in the README.</p>
    <p>Scoring checks are stream, non-stream, and cache. Pricing is informational and never ranks. Same ops InferHub balance as OpenCrabs.</p>
  </footer>
</body>
</html>
"""


def index_html(runs: list[dict], aliases: list[str], registry: list[dict]) -> str:
    if not runs:
        body = """
        <section>
          <h1>No runs yet</h1>
          <p>Set the <code>INFERHUB_API_KEY</code> Actions secret, then run <strong>Probe InferHub</strong> from the Actions tab. This page fills in after the first commit to <code>data/runs/</code>.</p>
        </section>
        """
        return shell("InferHub Watch", body)

    latest = runs[-1]
    mornings = distinct_mornings(runs)
    window = mornings[-7:]
    n_mornings = len(window)

    grid_head = []
    for run in window:
        day = html.escape(day_key(run)[5:])
        label = origin_label(run)
        grid_head.append(f"<th>{day}<span class=\"origin\">{html.escape(label)}</span></th>")
    grid_rows = []
    for alias in aliases:
        cells = []
        for run in window:
            ok, total = scoring_pass_count(run, alias)
            cls = "ok" if ok == total else ("mid" if ok else "bad")
            cells.append(f'<td class="{cls}">{ok}/{total}</td>')
        grid_rows.append(f"<tr><th>{html.escape(alias)}</th>{''.join(cells)}</tr>")

    cmap = cell_map(latest)
    check_heads = []
    for spec in registry:
        href = f"checks/{spec['id']}.html"
        check_heads.append(
            f'<th class="check-col"><a href="{html.escape(href)}">'
            f"{html.escape(spec['title'])}</a></th>"
        )
    matrix_rows = []
    broken_bits = []
    for alias in aliases:
        tds = [f"<th>{html.escape(alias)}</th>"]
        resolved = ""
        failed_titles = []
        for spec in registry:
            cell = cmap.get((alias, spec["id"])) or {}
            resolved = cell.get("resolved_model") or resolved
            status = cell.get("status") or "missing"
            summary = cell.get("summary") or ""
            tds.append(
                f'<td class="st-{html.escape(status)}">'
                f'<span class="pill">{html.escape(status)}</span>'
                f'<p>{html.escape(summary)}</p></td>'
            )
            if spec.get("scores_rank") and status in ("fail", "error"):
                failed_titles.append(spec["title"])
        tds.insert(1, f"<td class=\"pub\">{html.escape(resolved or '—')}</td>")
        matrix_rows.append(f"<tr>{''.join(tds)}</tr>")
        if failed_titles:
            broken_bits.append(
                f"<li><code>{html.escape(alias)}</code> — {html.escape(', '.join(failed_titles))}</li>"
            )

    explainers = []
    for spec in registry:
        blurb = html.escape(spec.get("blurb") or "")
        explainers.append(
            f'<li><a href="checks/{html.escape(spec["id"])}.html">{html.escape(spec["title"])}</a>'
            f"<p>{blurb}</p></li>"
        )

    started = html.escape((latest.get("started_at") or "")[:19].replace("T", " ") + " UTC")
    origin = html.escape(origin_label(latest))
    if n_mornings < 7:
        hero_window = (
            f"Treat <strong>Today</strong> as the source of truth until this page has "
            f"seven distinct UTC dates ({n_mornings} so far)."
        )
        window_caption = (
            f"Each cell is how many of the three scoring checks passed that UTC morning. "
            f"{n_mornings} morning{'s' if n_mornings != 1 else ''}, not 7. "
            f"Same-UTC-day reruns collapse to the later file."
        )
    else:
        hero_window = (
            "Today is the latest morning. The grid below is the last seven distinct UTC dates."
        )
        window_caption = (
            "Each cell is how many of the three scoring checks passed that UTC morning. "
            "Last 7 distinct mornings."
        )
    broken_block = ""
    if broken_bits:
        broken_block = (
            "<p class=\"broken-label\">Broken today (same names as the columns):</p>"
            f"<ul class=\"broken\">{''.join(broken_bits)}</ul>"
        )
    body = f"""
    <section class="hero">
      <p class="kicker">Last run {started} · {origin}</p>
      <h1>For people sending <code>tools</code> to <a href="https://inferhub.dev/">InferHub</a> <code>/v1/chat/completions</code>.</h1>
      <p>Green means that morning’s JSON matched the documented OpenAI Chat Completions shape for the check. OpenCrabs is not scored.</p>
      <p>{hero_window}</p>
    </section>
    <section>
      <h2>Today</h2>
      <p>The alias is what we request; the resolved publisher is the <code>cb/</code>, <code>cp/</code>, or <code>cmc/</code> prefix InferHub returned.</p>
      {broken_block}
      <div class="scroll">
        <table class="matrix">
          <thead><tr><th>Alias</th><th>Resolved</th>{''.join(check_heads)}</tr></thead>
          <tbody>{''.join(matrix_rows)}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Mornings</h2>
      <p>{window_caption}</p>
      <div class="scroll">
        <table class="grid">
          <thead><tr><th></th>{''.join(grid_head)}</tr></thead>
          <tbody>{''.join(grid_rows)}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>What each check means</h2>
      <ul class="explainers">{''.join(explainers)}</ul>
    </section>
    """
    return shell("InferHub Watch", body)


def check_page(spec: dict) -> str:
    md = (ROOT / "checks" / spec["id"] / "page.md").read_text()
    article = md_to_html(md)
    body = f"<article class=\"explainer\">{article}</article>"
    return shell(spec["title"], body, crumb=spec["title"], nested=True)


def main() -> int:
    dist = ROOT / "site" / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    shutil.copy(ROOT / "site" / "style.css", dist / "style.css")
    aliases = load_aliases()
    registry = load_registry()
    runs = load_runs()
    (dist / "index.html").write_text(index_html(runs, aliases, registry))
    checks_dir = dist / "checks"
    checks_dir.mkdir()
    for spec in registry:
        (checks_dir / f"{spec['id']}.html").write_text(check_page(spec))
    print(dist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
