# Prompt cache on a streaming completion

This check is **not** about tools. It sends a shared system prefix of about **2k tokens**, `stream: true`, no `tools` key, up to three times with **2 seconds** between attempts so a cache write can show up as `cached_tokens`. Public JSON stores only a hash of the prefix.

## Pass

The last attempt reports a cache hit: `cached_tokens`, `prompt_tokens_details.cached_tokens`, `prompt_cache_hit_tokens`, or `cache_read_input_tokens` greater than zero.

## Fail

Three streaming completions with `cached_tokens` still 0, or no SSE chunks.
