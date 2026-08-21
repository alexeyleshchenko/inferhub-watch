# InferHub Watch

Public daily probes of InferHub’s OpenAI-compatible Chat Completions API.

## Language

**Alias**:
The short model name we request (`gpt-5.6-luna`).
_Avoid_: “model” alone when the publisher prefix matters.

**Resolved publisher**:
The `model` string InferHub returns (`cb/gpt-5.6-luna`). That is who served the call.

**Check**:
One registered experiment: `checks/<id>/check.py` plus `checks/<id>/page.md`.

**Pass / fail**:
Whether InferHub matched the OpenAI Chat Completions shape that check documents.
_Avoid_: “InferHub is down”, “OpenCrabs is broken”, scoring OpenCrabs’ parser.

**Info**:
Recorded, never fails the suite (`usage_pricing`).

**Scoring checks**:
`stream_tools`, `nonstream_tools`, and `cache_tools`. These rank aliases. Pricing does not.
