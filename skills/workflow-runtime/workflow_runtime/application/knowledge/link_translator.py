from __future__ import annotations

import os
import re

MARKDOWN_LINK_PATTERN: re.Pattern[str] = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKILINK_PATTERN: re.Pattern[str] = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
FRONTMATTER_PATTERN: re.Pattern[str] = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def translate_links_to_wikilinks(content: str) -> str:
    """Convert standard Markdown links and absolute file:// links targeting .md files to [[wikilinks]]."""
    def repl(match: re.Match[str]) -> str:
        label = match.group(1) or ""
        url = match.group(2) or ""

        clean_url = url
        if clean_url.startswith("file://"):
            clean_url = clean_url[7:]

        clean_url = clean_url.split("#")[0]

        if clean_url.endswith(".md"):
            basename = os.path.basename(clean_url)
            note_name = os.path.splitext(basename)[0]

            if label.strip().lower() == note_name.strip().lower() or label.strip() == basename:
                return f"[[{note_name}]]"
            else:
                return f"[[{note_name}|{label}]]"
        return match.group(0) or ""

    return MARKDOWN_LINK_PATTERN.sub(repl, content)


def translate_wikilinks_to_markdown(content: str) -> str:
    """Convert Obsidian [[wikilinks]] back to standard Markdown links or text."""
    def repl(match: re.Match[str]) -> str:
        target = match.group(1) or ""
        raw_label = match.group(2)
        label = raw_label if raw_label else target

        url = target.replace(" ", "%20")
        if not url.endswith(".md"):
            url += ".md"

        return f"[{label}]({url})"

    return WIKILINK_PATTERN.sub(repl, content)


def extract_frontmatter(content: str) -> tuple[str | None, str]:
    """Extract YAML frontmatter from markdown content."""
    match = FRONTMATTER_PATTERN.search(content)
    if match:
        return match.group(1), content[match.end():]
    return None, content


__all__ = [
    "translate_links_to_wikilinks",
    "translate_wikilinks_to_markdown",
    "extract_frontmatter",
]
