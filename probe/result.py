from __future__ import annotations

from typing import Any


def result(
    *,
    check_id: str,
    alias: str,
    status: str,
    summary: str,
    resolved_model: str = "",
    http_status: int | None = None,
    latency_ms: float | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "alias": alias,
        "resolved_model": resolved_model,
        "status": status,
        "summary": summary,
        "http_status": http_status,
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
        "evidence": evidence or {},
    }
