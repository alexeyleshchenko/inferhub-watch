"""Human labels for InferHub resolved `model` ids.

Prefixes come from InferHub’s live market and price table (Family column),
not from guessing. Unknown first segments stay as the raw prefix plus the
full served id.
"""

from __future__ import annotations

# First path segment → InferHub “Family” / curated upstream name.
SEGMENT_FAMILY = {
    "cc": "Claude Code",
    "cp": "ClinePass",
    "ocg": "OpenCode Go",
    "zai": "z.ai",
    "cx": "Codex",
    "ali": "Ali",
    "mimo": "Mimo",
}


def publisher_label(resolved: str) -> str:
    raw = (resolved or "").strip()
    if not raw:
        return "—"
    parts = raw.split("/")
    head = parts[0]
    if head == "cmc" and len(parts) >= 2:
        return f"{parts[1]} · {raw}"
    if head == "cp" and len(parts) >= 2:
        family = SEGMENT_FAMILY.get(head, head)
        vendor = parts[1]
        if vendor != "cline-pass":
            return f"{family} / {vendor} · {raw}"
        return f"{family} · {raw}"
    family = SEGMENT_FAMILY.get(head)
    if family:
        return f"{family} · {raw}"
    return f"{head} · {raw}"
