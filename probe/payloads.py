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
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
]

SINGLE_USER = "Call get_weather for Paris. Do not answer in text. Use the tool."
PARALLEL_USER = (
    "Call get_weather for Paris AND get_time for Tokyo. "
    "Do not answer in text. Use both tools."
)


def cache_prefix() -> str:
    pad = ("The same routing instructions apply on every turn. " * 80).strip()
    return (
        "You are a tool-calling router. Never answer in prose. "
        "When asked for weather or time, call the matching tool. " + pad
    )
