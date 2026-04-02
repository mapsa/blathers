"""SVG diagram link injection and diagram collection."""

from __future__ import annotations

import re
from pathlib import Path

DIAGRAM_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg"}


def inject_links(svg_content: str, term_names: set[str], base_path: str = "classes") -> str:
    if not term_names:
        return svg_content

    for term in term_names:
        # Match self-closing elements with matching id
        pattern = re.compile(
            rf'(<(?:rect|text|g|ellipse|circle|path|polygon|use)\s[^>]*id="{re.escape(term)}"[^>]*/?>)',
            re.DOTALL,
        )
        # Match elements with closing tags
        pattern_with_close = re.compile(
            rf'(<(?:rect|text|g|ellipse|circle|path|polygon|use)\s[^>]*id="{re.escape(term)}"[^>]*>.*?</(?:rect|text|g|ellipse|circle|path|polygon|use)>)',
            re.DOTALL,
        )

        href = f"{base_path}/{term}.html"
        replacement = (
            f'<a href="{href}" style="cursor:pointer">'
            rf"\1"
            f"</a>"
        )

        svg_content, n = pattern_with_close.subn(replacement, svg_content)
        if n == 0:
            svg_content = pattern.sub(replacement, svg_content)

    return svg_content


def collect_diagrams(figures_dir: Path) -> list[Path]:
    figures_dir = Path(figures_dir)
    if not figures_dir.is_dir():
        return []

    return sorted(
        p for p in figures_dir.iterdir()
        if p.suffix.lower() in DIAGRAM_EXTENSIONS
    )
