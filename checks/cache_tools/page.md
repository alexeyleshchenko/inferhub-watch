# Tool calls after a prompt-cache hit

We send a long shared system prefix three times (never stored in public JSON — only a hash) and look at `usage` cache fields plus `tool_calls`.

## Pass

The last attempt still has named tools. A reported cache hit with named tools is the success case. A miss with named tools also passes (InferHub did not break tools; it just did not cache).

## Fail

- empty or blank tools on a response that reports cached tokens
- empty or blank tools even without a cache hit (labelled as a tools fail, not a cache fail)

## Who should care

Anyone relying on prompt caching with tools. A cache hit that drops `tool_calls` is worse than a miss.
