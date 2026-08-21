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
from probe.publishers import publisher_label  # noqa: E402

GITHUB = "https://github.com/alexeyleshchenko/inferhub-watch"


def base_href() -> str:
    raw = os.environ.get("PAGES_BASE", "/inferhub-watch").rstrip("/")
    return raw or ""


def md_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    list_items: list[str] = []
    fence: list[str] | None = None

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
        if fence is not None:
            if stripped.startswith("```"):
                code = html.escape("\n".join(fence))
                out.append(f"<pre><code>{code}</code></pre>")
                fence = None
            else:
                fence.append(line)
            continue
        if stripped.startswith("```"):
            flush_para()
            flush_list()
            fence = []
            continue
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
    if fence is not None:
        out.append(f"<pre><code>{html.escape(chr(10).join(fence))}</code></pre>")
    return "\n".join(out)


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
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


def scoring_ids(registry: list[dict]) -> list[str]:
    return [spec["id"] for spec in registry if spec.get("scores_rank")]


def scoring_pass_count(run: dict, alias: str, check_ids: list[str]) -> tuple[int, int]:
    cmap = cell_map(run)
    ok = 0
    for check_id in check_ids:
        cell = cmap.get((alias, check_id))
        if cell and cell.get("status") == "pass":
            ok += 1
    return ok, len(check_ids)


def run_stamp(run: dict) -> str:
    raw = run.get("started_at") or ""
    day = raw[5:10] if len(raw) >= 10 else day_key(run)
    clock = raw[11:16] if len(raw) >= 16 else ""
    return f"{day} {clock}".strip()


def alias_heading(alias: str, resolved: str) -> str:
    return (
        f'<th class="alias-cell">'
        f'<span class="alias">{html.escape(alias)}</span>'
        f'<span class="pub">{html.escape(publisher_label(resolved))}</span>'
        "</th>"
    )


def origin_label(run: dict) -> str:
    raw = (run.get("origin") or "").strip()
    if raw == "github-actions":
        return "Actions"
    if raw.endswith("-seed") or "seed" in raw:
        return "seed"
    return raw or "run"


def shell(
    title: str,
    body: str,
    *,
    crumb: str = "",
    nested: bool = False,
    masthead: str = "",
    page_class: str = "",
) -> str:
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
    cls = f' class="{html.escape(page_class)}"' if page_class else ""
    fonts = (
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500"
        "&family=Newsreader:ital,opsz,wght@0,8..72,400;0,8..72,600;1,8..72,400&display=swap"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{fonts}" rel="stylesheet">
  <link rel="stylesheet" href="{html.escape(css)}">
</head>
<body{cls}>
  <header class="site-header">
    <a class="mark" href="{html.escape(home)}">InferHub Watch</a>
    {masthead}
  </header>
  <main>
    {nav}
    {body}
  </main>
  <footer>
    <p>Clone <a href="{GITHUB}">alexeyleshchenko/inferhub-watch</a>, set <code>INFERHUB_API_KEY</code>, run <code>python3 -m probe.run</code>. How to add a check or alias is in the README (open a GitHub issue to propose a new alias).</p>
    <p>Scoring checks are stream and cache. Pricing is informational and never ranks. A pass is only that check. Probes run from GitHub Actions on the site owner’s InferHub key.</p>
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
    window = runs[-14:]

    grid_head = []
    for run in window:
        stamp = html.escape(run_stamp(run))
        label = origin_label(run)
        grid_head.append(
            f'<th>{stamp}<span class="origin">{html.escape(label)}</span></th>'
        )
    score_ids = scoring_ids(registry)
    grid_rows = []
    for alias in aliases:
        cells = []
        for run in window:
            ok, total = scoring_pass_count(run, alias, score_ids)
            cls = "ok" if ok == total else ("mid" if ok else "bad")
            cells.append(f'<td class="{cls}">{ok}/{total}</td>')
        last_map = cell_map(window[-1])
        resolved = ""
        for spec in registry:
            cell = last_map.get((alias, spec["id"])) or {}
            resolved = cell.get("resolved_model") or resolved
        grid_rows.append(f"<tr>{alias_heading(alias, resolved)}{''.join(cells)}</tr>")

    cmap = cell_map(latest)
    check_heads = []
    for spec in registry:
        href = f"checks/{spec['id']}.html"
        check_heads.append(
            f'<th class="check-col"><a href="{html.escape(href)}">'
            f"{html.escape(spec['title'])}</a></th>"
        )
    matrix_rows = []
    safe = []
    broken_bits = []
    for alias in aliases:
        resolved = ""
        failed_titles = []
        check_tds = []
        for spec in registry:
            cell = cmap.get((alias, spec["id"])) or {}
            resolved = cell.get("resolved_model") or resolved
            status = cell.get("status") or "missing"
            summary = cell.get("summary") or ""
            check_tds.append(
                f'<td class="st-{html.escape(status)}">'
                f'<span class="pill">{html.escape(status)}</span>'
                f'<p class="cell-note">{html.escape(summary)}</p></td>'
            )
            if spec.get("scores_rank") and status in ("fail", "error"):
                failed_titles.append(spec["title"])
        matrix_rows.append(
            f"<tr>{alias_heading(alias, resolved)}{''.join(check_tds)}</tr>"
        )
        ok, total = scoring_pass_count(latest, alias, score_ids)
        if total and ok == total:
            safe.append(alias)
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

    started = html.escape(
        (latest.get("started_at") or "")[:19].replace("T", " ") + " UTC"
    )
    origin = html.escape(origin_label(latest))
    masthead = (
        f'<p class="dispatch-meta"><time datetime="{html.escape((latest.get("started_at") or "")[:19])}">'
        f"{started}</time> · {origin}</p>"
    )
    n_score = len(score_ids) or 1
    if safe:
        rec = ", ".join(f"<code>{html.escape(a)}</code>" for a in safe)
        recommend = f'<p class="verdict">Scoring {n_score}/{n_score}: {rec}.</p>'
    else:
        recommend = (
            '<p class="verdict">No alias passed every scoring check this run.</p>'
        )
    broken_after = ""
    if broken_bits:
        broken_after = (
            '<p class="broken-label">Failed scoring checks:</p>'
            f'<ul class="broken">{"".join(broken_bits)}</ul>'
        )
    body = f"""
    <section class="hero">
      <h1>Daily probe of <a href="https://inferhub.dev/">InferHub</a> <code>/v1/chat/completions</code> streaming shapes.</h1>
    </section>
    <section class="today">
      <h2>Today</h2>
      {recommend}
      <div class="scroll">
        <table class="matrix">
          <thead><tr><th>Alias</th>{"".join(check_heads)}</tr></thead>
          <tbody>{"".join(matrix_rows)}</tbody>
        </table>
      </div>
      {broken_after}
    </section>
    <section class="history">
      <h2>History</h2>
      <div class="scroll">
        <table class="grid">
          <thead><tr><th>Alias</th>{"".join(grid_head)}</tr></thead>
          <tbody>{"".join(grid_rows)}</tbody>
        </table>
      </div>
    </section>
    <aside class="notes">
      <h2>How to read this</h2>
      <p>We send the alias in <code>model</code>. The line under it is who InferHub served. A pass is only that check, not a full SDK suite. Info never fails a cell. History is each committed probe (same-day reruns stay as their own columns).</p>
      <ul class="explainers">{"".join(explainers)}</ul>
    </aside>
    """
    return shell("InferHub Watch", body, masthead=masthead, page_class="board")


def check_page(spec: dict) -> str:
    md = (ROOT / "checks" / spec["id"] / "page.md").read_text()
    article = md_to_html(md)
    body = f'<article class="explainer">{article}</article>'
    return shell(
        spec["title"], body, crumb=spec["title"], nested=True, page_class="brief"
    )


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
