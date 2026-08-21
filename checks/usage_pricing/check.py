from __future__ import annotations

from probe.http import InferHubClient
from probe.payloads import completion_payload
from probe.result import result
from probe.sse import last_usage, parse_sse, resolved_model, usage_pricing_fields


def _price_summary(usage: dict) -> str:
    cost_keys = [k for k in ("cost", "market_cost", "gateway_cost") if k in usage]
    has_credit = "credit" in usage
    if not cost_keys and not has_credit:
        return (
            "tokens_only — no cost/credit/market_cost. InferHub bills consumers in USDC; "
            "this response did not include a price field."
        )
    bits = [f"{k}={usage[k]}" for k in cost_keys]
    if has_credit:
        bits.append(f"credit={usage['credit']}")
    note = (
        " InferHub consumer billing is USDC; these numbers are copied as returned. "
        "`cost` / `market_cost` / `gateway_cost` are not treated as the same unit as `credit`."
    )
    return "Price fields: " + ", ".join(bits) + "." + note


def run(client: InferHubClient, alias: str) -> dict:
    status, raw, ms = client.post(completion_payload(alias, stream=True))
    chunks = parse_sse(raw) if status == 200 else []
    resolved = resolved_model(chunks, alias)
    usage = usage_pricing_fields(last_usage(chunks))
    if status != 200:
        summary = f"HTTP {status}: {raw[:180].replace(chr(10), ' ')}"
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
