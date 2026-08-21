# Tool names in the live stream

InferHub advertises an OpenAI-compatible `/v1/chat/completions` stream. This check asks whether a **streaming** tool-call response matches that convention.

OpenAI documents streaming chat completions and tool-call deltas here: [Chat Completions streaming](https://platform.openai.com/docs/api-reference/chat/streaming) and [function calling](https://platform.openai.com/docs/guides/function-calling).

## What we send

`stream: true`, `tool_choice: required`, one `get_weather` tool. We do **not** send `max_tokens`; some InferHub routes reject it. We request the **alias** in `model`; InferHub may return a different `model` string.

```json
{
  "model": "<alias>",
  "messages": [
    {
      "role": "user",
      "content": "Call get_weather for Paris. Do not answer in text. Use the tool."
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
          "type": "object",
          "properties": {"city": {"type": "string"}},
          "required": ["city"]
        }
      }
    }
  ],
  "tool_choice": "required",
  "stream": true
}
```

## Pass

Intermediate chunks use `finish_reason` of JSON `null` or omit the field. Tool names appear as non-empty strings on first use and never as `""`. The stream includes at least one named tool.

## Fail

Any of:

- a chunk with `"finish_reason": ""`
- a tool delta with `"name": ""`
- a required tool call with no non-empty name by the end of the stream

A non-empty but unusual `finish_reason` is stored in evidence and does not fail this check. Out of scope: truncation, JSON schema, parallel tools, other SDK behavior.
