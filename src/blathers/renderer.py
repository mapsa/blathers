"""Static HTML site renderer using Jinja2 templates."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape


# Minimal CSS for the default theme
DEFAULT_CSS = """
:root, [data-theme="light"] {
    --bg: #ffffff; --fg: #1a1a2e; --accent: #0066cc;
    --border: #e0e0e0; --code-bg: #f5f5f5; --nav-bg: #f8f9fa;
}
[data-theme="dark"] {
    --bg: #1a1a2e; --fg: #e0e0e0; --accent: #66b3ff;
    --border: #333; --code-bg: #2d2d44; --nav-bg: #16213e;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: var(--bg); color: var(--fg); line-height: 1.6; }
header { background: var(--nav-bg); border-bottom: 1px solid var(--border); padding: 0.75rem 1.5rem; }
header nav { display: flex; align-items: center; gap: 1rem; max-width: 1200px; margin: 0 auto; }
header .logo { font-weight: 700; font-size: 1.1rem; text-decoration: none; color: var(--fg); }
header .version { font-size: 0.85rem; color: var(--accent); }
#theme-toggle { background: none; border: none; cursor: pointer; font-size: 1.2rem; margin-left: auto; }
main { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }
footer { text-align: center; padding: 2rem; font-size: 0.85rem; color: #888; border-top: 1px solid var(--border); margin-top: 3rem; }
a { color: var(--accent); }
h1 { margin-bottom: 0.5rem; } h2 { margin: 1.5rem 0 0.75rem; border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
code { background: var(--code-bg); padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.9em; }
.iri { margin-bottom: 1rem; }
.term-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.term-table th, .term-table td { text-align: left; padding: 0.5rem; border-bottom: 1px solid var(--border); }
.term-table th { font-weight: 600; background: var(--nav-bg); }
.breadcrumb { margin-bottom: 1rem; font-size: 0.9rem; }
.narrative { margin-bottom: 2rem; }
.sidecar-content { margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
"""


def render_site(manifest: dict, output_dir: Path) -> None:
    """Render the full static site from a manifest dict."""
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=PackageLoader("blathers", "templates"),
        autoescape=select_autoescape(["html"]),
    )

    # Write manifest JSON
    (output_dir / "site-data.json").write_text(json.dumps(manifest, indent=2))

    # Write CSS
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "style.css").write_text(DEFAULT_CSS)

    # Common template context
    ctx = {
        "metadata": manifest["metadata"],
        "classes": manifest["classes"],
        "properties": manifest["properties"],
        "shapes": manifest["shapes"],
        "sections": manifest["sections"],
        "conneg": manifest.get("conneg", {}),
    }

    # Render index
    index_tpl = env.get_template("index.html.j2")
    (output_dir / "index.html").write_text(index_tpl.render(base_path="", **ctx))

    # Render class pages
    classes_dir = output_dir / "classes"
    classes_dir.mkdir(exist_ok=True)
    term_tpl = env.get_template("term.html.j2")
    for cls in manifest["classes"]:
        html = term_tpl.render(
            base_path="../",
            term=cls,
            term_type="classes",
            **ctx,
        )
        (classes_dir / f"{cls['local_name']}.html").write_text(html)

    # Render property pages
    props_dir = output_dir / "properties"
    props_dir.mkdir(exist_ok=True)
    for prop in manifest["properties"]:
        html = term_tpl.render(
            base_path="../",
            term=prop,
            term_type="properties",
            **ctx,
        )
        (props_dir / f"{prop['local_name']}.html").write_text(html)
