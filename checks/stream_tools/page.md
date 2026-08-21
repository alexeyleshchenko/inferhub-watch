# Tool names in the live stream

InferHub advertises an OpenAI-compatible `/v1/chat/completions` stream. This check asks whether a **streaming** tool-call response matches that convention.

## What we send

A required `get_weather` tool call, `stream: true`. We do **not** send `max_tokens`; some InferHub routes reject it.

## Pass

Intermediate chunks use `finish_reason` of JSON `null` or omit the field. Tool names appear as non-empty strings on first use and never as `""`. The stream includes at least one named tool.

## Fail

Any of:

- a chunk with `"finish_reason": ""`
- a tool delta with `"name": ""`
- a required tool call with no non-empty name by the end of the stream

A non-empty but unusual `finish_reason` is stored in evidence and does not fail v1.

## Who should care

InferHub (fix the stream). Any OpenAI-compatible client that follows the documented delta shape.

OpenCrabs `origin/main` treats a present empty `finish_reason` as terminal (`Option::is_some()`). That is why this OpenAI violation also blanks tools in OpenCrabs. This check does **not** score OpenCrabs. If InferHub sends proper `null`s, the cell is green even if some other OpenCrabs quirk remains.
