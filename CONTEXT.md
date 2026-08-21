# InferHub Watch

Public daily probes of InferHub’s OpenAI-compatible Chat Completions API.

## Language

**Alias**:
The short model name we request (`gpt-5.6-luna`).
_Avoid_: “model” alone when the publisher prefix matters.

**Resolved publisher**:
The `model` string InferHub returns, shown with a family label when InferHub’s market table names it (`ClinePass · cp/cline-pass/…`).

**Check**:
One registered experiment: `checks/<id>/check.py` plus `checks/<id>/page.md`.

**Pass / fail**:
Whether InferHub matched the shape that check documents.
_Avoid_: “InferHub is down.”

**Info**:
Recorded, never fails the suite (`usage_pricing`).

**Scoring checks**:
`stream_tools` (streaming tool names) and `cache_tools` (prompt cache on a streaming completion **without** tools). Pricing does not score.
