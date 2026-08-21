from __future__ import annotations

from probe.http import InferHubClient
from probe.payloads import SINGLE_USER, TOOLS
from probe.result import result
from probe.sse import inspect_stream, parse_sse, resolved_model


def run(client: InferHubClient, alias: str) -> dict:
    payload = {
        "model": alias,
        "messages": [{"role": "user", "content": SINGLE_USER}],
        "tools": TOOLS,
        "tool_choice": "required",
        "stream": True,
    }
    status, raw, ms = client.post(payload)
    if status != 200:
        return result(
            check_id="stream_tools",
            alias=alias,
            status="error",
            summary=f"HTTP {status}: {raw[:180].replace(chr(10), ' ')}",
            http_status=status,
            latency_ms=ms,
        )
    chunks = parse_sse(raw)
    resolved = resolved_model(chunks, alias)
    stats = inspect_stream(chunks)
    if not chunks:
        return result(
            check_id="stream_tools",
            alias=alias,
            status="fail",
            summary="No SSE JSON chunks in the stream.",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=stats,
        )
    if stats["empty_finish_chunks"] or stats["empty_name_chunks"]:
        bits = []
        if stats["empty_finish_chunks"]:
            bits.append(f'{stats["empty_finish_chunks"]} chunks with finish_reason ""')
        if stats["empty_name_chunks"]:
            bits.append(f'{stats["empty_name_chunks"]} tool deltas with name ""')
        return result(
            check_id="stream_tools",
            alias=alias,
            status="fail",
            summary="; ".join(bits) + ".",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=stats,
        )
    if not stats["names"]:
        return result(
            check_id="stream_tools",
            alias=alias,
            status="fail",
            summary="Stream ended without a non-empty tool name.",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=stats,
        )
    return result(
        check_id="stream_tools",
        alias=alias,
        status="pass",
        summary=f"Named tools: {', '.join(stats['names'])}.",
        resolved_model=resolved,
        http_status=status,
        latency_ms=ms,
        evidence=stats,
    )
