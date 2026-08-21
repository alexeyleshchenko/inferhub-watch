from __future__ import annotations

import hashlib

from probe.http import InferHubClient
from probe.payloads import PARALLEL_USER, TOOLS, cache_prefix
from probe.result import result
from probe.sse import summarize_nonstream, usage_pricing_fields


def _cached_tokens(usage: dict) -> int:
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict) and details.get("cached_tokens") is not None:
        return int(details["cached_tokens"] or 0)
    return int(usage.get("cached_tokens") or 0)


def _tools_ok(ns: dict) -> bool:
    names = [n for n in (ns.get("names") or []) if n]
    if ns.get("blank_names"):
        return False
    if ns.get("finish_reason") == "tool_calls" and not names:
        return False
    return bool(names)


def run(client: InferHubClient, alias: str) -> dict:
    prefix = cache_prefix()
    prefix_hash = hashlib.sha256(prefix.encode()).hexdigest()[:12]
    messages_seed = [
        {"role": "system", "content": prefix},
        {"role": "user", "content": PARALLEL_USER},
    ]
    last = None
    cached = 0
    resolved = alias
    for _ in range(3):
        status, raw, ms = client.post(
            {
                "model": alias,
                "messages": messages_seed,
                "tools": TOOLS,
                "tool_choice": "required",
                "stream": False,
            }
        )
        ns = summarize_nonstream(raw)
        last = (status, ns, ms)
        resolved = ns.get("resolved_model") or resolved
        if status != 200 or ns.get("error"):
            return result(
                check_id="cache_tools",
                alias=alias,
                status="error",
                summary=ns.get("error") or f"HTTP {status}",
                resolved_model=resolved,
                http_status=status,
                latency_ms=ms,
                evidence={"prefix_hash": prefix_hash, **ns},
            )
        cached = _cached_tokens(ns.get("usage") or {})
        if cached > 0:
            break

    assert last is not None
    status, ns, ms = last
    ok = _tools_ok(ns)
    usage = usage_pricing_fields(ns.get("usage") or {})
    evidence = {
        "prefix_hash": prefix_hash,
        "cached_tokens": cached,
        "names": ns.get("names"),
        "finish_reason": ns.get("finish_reason"),
        "usage": usage,
    }
    if not ok and cached > 0:
        return result(
            check_id="cache_tools",
            alias=alias,
            status="fail",
            summary=f"Cache hit ({cached} tokens) but tools empty or blank.",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=evidence,
        )
    if not ok:
        return result(
            check_id="cache_tools",
            alias=alias,
            status="fail",
            summary="No cache hit; tools already empty or blank (tools fail, not a cache fail).",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=evidence,
        )
    if cached > 0:
        summary = f"Cache hit ({cached} tokens); tools {', '.join(n for n in ns['names'] if n)}."
    else:
        summary = "No cache hit reported; tools still named."
    return result(
        check_id="cache_tools",
        alias=alias,
        status="pass",
        summary=summary,
        resolved_model=resolved,
        http_status=status,
        latency_ms=ms,
        evidence=evidence,
    )
