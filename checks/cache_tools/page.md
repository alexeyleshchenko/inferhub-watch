# Prompt cache on a streaming completion

This check is **not** about tools. It sends a long shared system prefix and a one-word user prompt, `stream: true`, no `tools` key, three times. Public JSON stores only a hash of the prefix.

## Pass

The last attempt reports `cached_tokens` (or `prompt_tokens_details.cached_tokens`) greater than zero.

## Fail

Three streaming completions with `cached_tokens` still 0, or no SSE chunks.

## Who should care

Anyone relying on InferHub prompt caching for ordinary Chat Completions, not only tool calls.
