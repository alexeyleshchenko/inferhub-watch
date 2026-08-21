# Complete tool calls without streaming

Same tools as the stream check, but `stream: false`. InferHub should return a complete `choices[0].message.tool_calls` list.

## Pass

At least one tool call with a non-empty `function.name`.

## Fail

- `finish_reason` is `tool_calls` and the list is empty
- a `function.name` is missing or blank
- no tool calls at all when tools were required

## Who should care

Clients that buffer the whole response (SDKs, batch jobs). Empty `tool_calls` with `finish_reason: tool_calls` is an OpenAI contract miss.
