from __future__ import annotations

import hashlib

from probe.http import InferHubClient
from probe.payloads import cache_payload, cache_prefix
from probe.result import result
from probe.sse import last_usage, parse_sse, resolved_model


def _cached_tokens(usage: dict) -> int:
    details = usage.get("prompt_tokens_details") or {}
    if isinstance(details, dict) and details.get("cached_tokens") is not None:
        return int(details["cached_tokens"] or 0)
    return int(usage.get("cached_tokens") or 0)


def run(client: InferHubClient, alias: str) -> dict:
    prefix = cache_prefix()
    prefix_hash = hashlib.sha256(prefix.encode()).hexdigest()[:12]
    last = None
    cached = 0
    resolved = alias
    for _ in range(3):
        status, raw, ms = client.post(cache_payload(alias, prefix))
        if status != 200:
            return result(
                check_id="cache_tools",
                alias=alias,
                status="error",
                summary=f"HTTP {status}: {raw[:180].replace(chr(10), ' ')}",
                resolved_model=resolved,
                http_status=status,
                latency_ms=ms,
                evidence={"prefix_hash": prefix_hash},
            )
        chunks = parse_sse(raw)
        resolved = resolved_model(chunks, resolved)
        usage = last_usage(chunks)
        cached = _cached_tokens(usage)
        last = (status, usage, ms, len(chunks))
        if cached > 0:
            break

    assert last is not None
    status, usage, ms, n_chunks = last
    evidence = {
        "prefix_hash": prefix_hash,
        "cached_tokens": cached,
        "chunk_count": n_chunks,
        "usage": usage,
        "had_tools": False,
    }
    if n_chunks == 0:
        return result(
            check_id="cache_tools",
            alias=alias,
            status="fail",
            summary="No SSE JSON chunks in the stream.",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=evidence,
        )
    if cached <= 0:
        return result(
            check_id="cache_tools",
            alias=alias,
            status="fail",
            summary="No cached_tokens after 3 streaming completions (no tools in the request).",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=evidence,
        )
    return result(
        check_id="cache_tools",
        alias=alias,
        status="pass",
        summary=f"Cache hit ({cached} tokens) on a streaming completion without tools.",
        resolved_model=resolved,
        http_status=status,
        latency_ms=ms,
        evidence=evidence,
    )
