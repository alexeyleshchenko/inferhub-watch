"""Shared OpenAI-shaped tool payloads. No max_tokens — some InferHub routes 400 it."""

from __future__ import annotations

URL = "https://api.inferhub.dev/v1/chat/completions"
USER_AGENT = "inferhub-watch/1.0"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]

SINGLE_USER = "Call get_weather for Paris. Do not answer in text. Use the tool."


def completion_payload(
    alias: str, *, stream: bool, system: str | None = None, with_tools: bool = True
) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": SINGLE_USER})
    payload: dict = {
        "model": alias,
        "messages": messages,
        "stream": stream,
    }
    if with_tools:
        payload["tools"] = TOOLS
        payload["tool_choice"] = "required"
    return payload


CACHE_USER = "Reply with the single word paris. Nothing else."


def cache_prefix() -> str:
    pad = ("The same instructions apply on every turn. " * 80).strip()
    return (
        "You are a concise assistant. Follow the user. "
        "Keep answers to one word when asked. " + pad
    )


def cache_payload(alias: str, system: str) -> dict:
    return {
        "model": alias,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": CACHE_USER},
        ],
        "stream": True,
    }
