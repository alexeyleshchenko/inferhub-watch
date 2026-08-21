from __future__ import annotations

from pathlib import Path
from string import Template

DIR = Path(__file__).resolve().parent / "templates"


def render(name: str, **kwargs: str) -> str:
    return Template((DIR / name).read_text()).substitute(kwargs)
