"""imagine — AI image generation CLI.

Gemini (Nano Banana) and Cloudflare Workers AI backends. Designed as a
renderer-tier tool: agent workflows (Anvil figurers, Claude Code skills)
shell out to it the way they shell out to marp or mmdc.
"""

import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version("imagine")
except importlib.metadata.PackageNotFoundError:
    try:
        __version__ = (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip()
    except OSError:
        __version__ = "0+unknown"
