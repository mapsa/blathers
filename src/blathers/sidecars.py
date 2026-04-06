"""Sidecar Markdown file parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter
import markdown


@dataclass
class Sidecar:
    filename: str
    path: Path
    term: str | None
    section: str | None
    order: int
    body: str
    html: str
    is_narrative: bool
    standalone_page: bool = False
    description: str = ""


def _parse_sidecar(path: Path) -> Sidecar:
    """Parse a single Markdown sidecar with YAML frontmatter."""
    post = frontmatter.load(str(path))
    body = post.content
    html = markdown.markdown(body, extensions=["tables", "fenced_code", "attr_list", "admonition"])
    filename = path.name
    is_narrative = filename.startswith("_")

    standalone_page = bool(post.get("page", False))
    description = str(post.get("description", ""))

    return Sidecar(
        filename=filename,
        path=path,
        term=post.get("term"),
        section=post.get("section"),
        order=post.get("order", 999),
        body=body,
        html=html,
        is_narrative=is_narrative,
        standalone_page=standalone_page,
        description=description,
    )


def load_sidecars(sidecars_dir: Path) -> list[Sidecar]:
    """Load all .md sidecar files from a directory."""
    sidecars_dir = Path(sidecars_dir)
    if not sidecars_dir.is_dir():
        return []

    sidecars = []
    for md_file in sorted(sidecars_dir.glob("*.md")):
        sidecars.append(_parse_sidecar(md_file))

    return sorted(sidecars, key=lambda s: s.order)
