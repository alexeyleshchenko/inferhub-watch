from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from probe.http import InferHubClient
from probe.registry import load_aliases, load_check_module, load_registry, repo_root


def main() -> int:
    key = os.environ.get("INFERHUB_API_KEY", "").strip()
    if not key:
        print("INFERHUB_API_KEY is required", file=sys.stderr)
        return 2
    client = InferHubClient(key)
    aliases = load_aliases()
    registry = load_registry()
    cells = []
    errors = []
    for alias in aliases:
        for spec in registry:
            module = load_check_module(spec["id"])
            try:
                cells.append(module.run(client, alias))
            except Exception as exc:  # noqa: BLE001 — keep the day, record the cell
                errors.append(f"{alias}/{spec['id']}: {exc}")
                cells.append(
                    {
                        "check_id": spec["id"],
                        "alias": alias,
                        "resolved_model": "",
                        "status": "error",
                        "summary": str(exc),
                        "http_status": None,
                        "latency_ms": None,
                        "evidence": {},
                    }
                )
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y-%m-%dT%H%M%SZ")
    payload = {
        "started_at": started.isoformat(),
        "origin": "github-actions",
        "api": "https://api.inferhub.dev/v1/chat/completions",
        "aliases": aliases,
        "checks": [c["id"] for c in registry],
        "cells": cells,
        "runner_errors": errors,
    }
    out = repo_root() / "data" / "runs" / f"{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
