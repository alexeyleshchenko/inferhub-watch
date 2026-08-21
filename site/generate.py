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

SCORING = {"stream_tools", "nonstream_tools", "cache_tools"}
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


def rank_rows(runs: list[dict], aliases: list[str]) -> list[dict]:
    recent = runs[-7:]
    latest = runs[-1] if runs else None
    rows = []
    for alias in aliases:
        rates = []
        green_days = 0
        for run in recent:
            ok, total = scoring_pass_count(run, alias)
            rates.append(ok / total)
            if ok == total:
                green_days += 1
        rate = sum(rates) / len(rates) if rates else 0
        broken = []
        today_ok = 0
        resolved = ""
        if latest:
            cmap = cell_map(latest)
            for check_id in ("stream_tools", "nonstream_tools", "cache_tools"):
                cell = cmap.get((alias, check_id))
                if cell and cell.get("status") == "pass":
                    today_ok += 1
                elif cell:
                    broken.append(check_id.replace("_", " "))
                if cell and cell.get("resolved_model"):
                    resolved = cell["resolved_model"]
        rows.append(
            {
                "alias": alias,
                "resolved": resolved,
                "rate": rate,
                "today": f"{today_ok}/3",
                "broken": broken,
                "green_days": green_days,
            }
        )
    rows.sort(key=lambda r: (-r["rate"], r["alias"]))
    return rows


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
    <p class="lede">Daily OpenAI Chat Completions probes against InferHub aliases. Fail means the wire shape missed the documented contract, not that InferHub was down.</p>
    <p class="source"><a href="{GITHUB}">Source on GitHub</a> · how to add a check is in the README</p>
  </header>
  <main>
    {nav}
    {body}
  </main>
  <footer>
    <p>Scoring checks are stream, non-stream, and cache. Pricing is informational. Same ops InferHub balance as OpenCrabs.</p>
    <p><a href="{GITHUB}">alexeyleshchenko/inferhub-watch</a></p>
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
    ranks = rank_rows(runs, aliases)
    bars = []
    for i, row in enumerate(ranks, start=1):
        pct = round(row["rate"] * 100)
        bars.append(
            f"""<div class="rank-row">
              <span class="rank-n">{i:02d}</span>
              <div class="rank-meta">
                <strong>{html.escape(row['alias'])}</strong>
                <span class="pub">{html.escape(row['resolved'] or '—')}</span>
              </div>
              <div class="bar" aria-label="{pct} percent pass over last seven days">
                <span style="width:{pct}%"></span>
              </div>
              <span class="pct">{pct}%</span>
            </div>"""
        )
    rank_table = []
    for i, row in enumerate(ranks, start=1):
        broken = ", ".join(row["broken"]) if row["broken"] else "none"
        rank_table.append(
            f"<tr><td>{i}</td><td>{html.escape(row['alias'])}</td>"
            f"<td>{html.escape(row['today'])}</td>"
            f"<td>{html.escape(broken)}</td>"
            f"<td>{row['green_days']}</td></tr>"
        )

    days = runs[-21:]
    grid_head = "".join(f"<th>{html.escape(day_key(r)[5:])}</th>" for r in days)
    grid_rows = []
    for alias in aliases:
        cells = []
        for run in days:
            ok, total = scoring_pass_count(run, alias)
            cls = "ok" if ok == total else ("mid" if ok else "bad")
            cells.append(f'<td class="{cls}">{ok}/{total}</td>')
        grid_rows.append(f"<tr><th>{html.escape(alias)}</th>{''.join(cells)}</tr>")

    cmap = cell_map(latest)
    check_heads = []
    for spec in registry:
        href = f"checks/{spec['id']}.html"
        check_heads.append(f"<th><a href=\"{html.escape(href)}\">{html.escape(spec['title'])}</a></th>")
    matrix_rows = []
    for alias in aliases:
        tds = [f"<th>{html.escape(alias)}</th>"]
        resolved = ""
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
        tds.insert(1, f"<td class=\"pub\">{html.escape(resolved or '—')}</td>")
        matrix_rows.append(f"<tr>{''.join(tds)}</tr>")

    explainers = []
    for spec in registry:
        explainers.append(
            f'<li><a href="checks/{html.escape(spec["id"])}.html">{html.escape(spec["title"])}</a></li>'
        )

    started = html.escape((latest.get("started_at") or "")[:19].replace("T", " ") + " UTC")
    origin = html.escape(latest.get("origin") or "")
    body = f"""
    <section class="hero">
      <p class="kicker">Last run {started} · {origin}</p>
      <h1>Which alias works better</h1>
      <p>Seven-day pass rate on the three scoring checks. Pricing never ranks.</p>
    </section>
    <section class="ranking">
      {''.join(bars)}
      <table class="rank-table">
        <thead><tr><th>#</th><th>Alias</th><th>Today</th><th>Broken today</th><th>Fully green days (of last 7)</th></tr></thead>
        <tbody>{''.join(rank_table)}</tbody>
      </table>
    </section>
    <section>
      <h2>Stability</h2>
      <p>Each cell is how many of the three scoring checks passed that morning.</p>
      <div class="scroll">
        <table class="grid">
          <thead><tr><th></th>{grid_head}</tr></thead>
          <tbody>{''.join(grid_rows)}</tbody>
        </table>
      </div>
    </section>
    <section>
      <h2>Today</h2>
      <p>Resolved publisher is who InferHub actually routed. Same alias can change prefix between days.</p>
      <div class="scroll">
        <table class="matrix">
          <thead><tr><th>Alias</th><th>Resolved</th>{''.join(check_heads)}</tr></thead>
          <tbody>{''.join(matrix_rows)}</tbody>
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
    extra = ""
    if spec["id"] == "stream_tools":
        extra = (
            "<p class=\"note\">OpenCrabs may still blank tools if it treats "
            "an empty finish_reason as present. That parser is not this score.</p>"
        )
    body = f"<article class=\"explainer\">{article}{extra}</article>"
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
