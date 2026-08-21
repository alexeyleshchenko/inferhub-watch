from __future__ import annotations

from probe.http import InferHubClient
from probe.payloads import completion_payload
from probe.result import http_preview, result
from probe.sse import last_usage, parse_sse, resolved_model, usage_pricing_fields


def _price_summary(usage: dict) -> str:
    keys = [k for k in ("cost", "market_cost", "gateway_cost", "credit") if k in usage]
    if not keys:
        return "No price field."
    return ", ".join(f"{k}={usage[k]}" for k in keys)


def run(client: InferHubClient, alias: str) -> dict:
    status, raw, ms = client.post(completion_payload(alias, stream=True))
    chunks = parse_sse(raw) if status == 200 else []
    resolved = resolved_model(chunks, alias)
    usage = usage_pricing_fields(last_usage(chunks))
    if status != 200:
        summary = http_preview(status, raw)
    else:
        summary = _price_summary(usage)
    return result(
        check_id="usage_pricing",
        alias=alias,
        status="info",
        summary=summary,
        resolved_model=resolved,
        http_status=status,
        latency_ms=ms,
        evidence={"usage": usage},
    )
