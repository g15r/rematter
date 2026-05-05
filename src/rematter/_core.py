"""Core parsing and serialization helpers for markdown frontmatter."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from slugify import slugify

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)", re.DOTALL)
FENCE_RE = re.compile(r"^(\s*)(```+|~~~+)")
# Block-level lines that should never be joined with neighbors.
SPECIAL_LINE_RE = re.compile(
    r"""^\s*(
        \#{1,6}\s              # heading
      | [-*+]\s                # bullet list
      | \d+[.)]\s              # ordered list
      | >                      # blockquote
      | \|                     # table row
      | (-{3,}|\*{3,}|_{3,})\s*$  # horizontal rule
      | <[!/a-zA-Z]            # html block
    )""",
    re.VERBOSE,
)
TABLE_LINE_RE = re.compile(r"^\s*\|")
ATX_HEADING_RE = re.compile(r"^(#{1,6})(\s+.*)$")
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2} - ")
WIKILINK_RE = re.compile(r"(?<!\!)\[\[([^|\]]+?)(?:\|([^\]]+?))?\]\]")
WIKILINK_IMAGE_RE = re.compile(r"!\[\[([^|\]]+?)(?:\|([^\]]+?))?\]\]")
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
TYPE_TAG_RE = re.compile(r"(?<!\w)#([A-Z][a-zA-Z]+)")


def _slugify(name: str) -> str:
    """Convert a display name to a URL-safe slug."""
    return slugify(name)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split raw markdown into (frontmatter_block, body) without parsing YAML.

    The frontmatter block includes the `---` delimiters and the trailing newline
    after the closing delimiter. Returns ("", text) when no frontmatter is present.
    Used by body-only transforms (reflow, fix-tables) that don't need to interpret
    frontmatter — only to leave it untouched.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return text[: m.start(2)], text[m.start(2) :]


def _load(path: Path) -> tuple[dict[str, Any], str] | None:
    """Parse YAML frontmatter from a markdown file.

    Returns (frontmatter_dict, body) or None if the file has no valid frontmatter.
    Files without frontmatter are silently skipped by callers.
    """
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    try:
        fm: Any = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    return fm, m.group(2).lstrip("\n")


def _dump(fm: dict[str, Any], body: str) -> str:
    """Serialize a frontmatter dict and body back to markdown content."""
    if not fm:
        return body
    fm_str = yaml.dump(
        fm,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip("\n")
    return f"---\n{fm_str}\n---\n{body}"
