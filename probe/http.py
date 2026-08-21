from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from probe.payloads import URL, USER_AGENT


class InferHubClient:
    def __init__(self, api_key: str, timeout: int = 90) -> None:
        self.api_key = api_key
        self.timeout = timeout

    def post(self, payload: dict[str, Any]) -> tuple[int, str, float]:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream, application/json",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                elapsed = (time.monotonic() - started) * 1000
                return resp.status, raw, elapsed
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            elapsed = (time.monotonic() - started) * 1000
            return exc.code, raw, elapsed
