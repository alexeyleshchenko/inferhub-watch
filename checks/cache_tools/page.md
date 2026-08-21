# Prompt cache on a streaming completion

This check is **not** about tools. It sends a shared system prefix well past the usual **1024-token** provider floor (enough to write a cache block, not a 70k Cline session) and a one-word user prompt, `stream: true`, no `tools` key, three times. Public JSON stores only a hash of the prefix.

## Pass

The last attempt reports a cache hit: `cached_tokens`, `prompt_tokens_details.cached_tokens`, `prompt_cache_hit_tokens`, or `cache_read_input_tokens` greater than zero.

## Fail

Three streaming completions with `cached_tokens` still 0, or no SSE chunks.
