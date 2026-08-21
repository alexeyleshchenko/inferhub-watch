from __future__ import annotations

from probe.http import InferHubClient
from probe.payloads import SINGLE_USER, TOOLS
from probe.result import result
from probe.sse import summarize_nonstream, usage_pricing_fields


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
    usage = usage_pricing_fields(ns.get("usage") or {})
    price_keys = [k for k in ("cost", "market_cost", "gateway_cost", "credit") if k in usage]
    if status != 200 or ns.get("error"):
        summary = ns.get("error") or f"HTTP {status}"
    elif price_keys:
        bits = [f"{k}={usage[k]}" for k in price_keys]
        summary = "Price fields: " + ", ".join(bits) + "."
    else:
        summary = "tokens_only — no cost/credit/market_cost on usage."
    return result(
        check_id="usage_pricing",
        alias=alias,
        status="info",
        summary=summary,
        resolved_model=resolved,
        http_status=status,
        latency_ms=ms,
        evidence={"usage": usage, "error": ns.get("error")},
    )
