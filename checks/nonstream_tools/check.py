from __future__ import annotations

from probe.http import InferHubClient
from probe.payloads import SINGLE_USER, TOOLS
from probe.result import result
from probe.sse import summarize_nonstream


def run(client: InferHubClient, alias: str) -> dict:
    payload = {
        "model": alias,
        "messages": [{"role": "user", "content": SINGLE_USER}],
        "tools": TOOLS,
        "tool_choice": "required",
        "stream": False,
    }
    status, raw, ms = client.post(payload)
    ns = summarize_nonstream(raw)
    resolved = ns.get("resolved_model") or alias
    if status != 200 or ns.get("error"):
        return result(
            check_id="nonstream_tools",
            alias=alias,
            status="error",
            summary=ns.get("error") or f"HTTP {status}",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=ns,
        )
    names = ns.get("names") or []
    reason = ns.get("finish_reason")
    if reason == "tool_calls" and not names:
        return result(
            check_id="nonstream_tools",
            alias=alias,
            status="fail",
            summary='finish_reason is tool_calls but tool_calls is empty.',
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=ns,
        )
    if ns.get("blank_names"):
        return result(
            check_id="nonstream_tools",
            alias=alias,
            status="fail",
            summary="A function.name is missing or blank.",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=ns,
        )
    if not names:
        return result(
            check_id="nonstream_tools",
            alias=alias,
            status="fail",
            summary=f"No tool calls (finish_reason={reason!r}).",
            resolved_model=resolved,
            http_status=status,
            latency_ms=ms,
            evidence=ns,
        )
    return result(
        check_id="nonstream_tools",
        alias=alias,
        status="pass",
        summary=f"Named tools: {', '.join(names)}.",
        resolved_model=resolved,
        http_status=status,
        latency_ms=ms,
        evidence=ns,
    )
