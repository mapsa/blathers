"""Static HTML site renderer using Jinja2 templates."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup


# Well-known namespace prefixes
KNOWN_PREFIXES = {
    "http://www.w3.org/2002/07/owl#": "owl",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "http://www.w3.org/ns/shacl#": "sh",
    "http://purl.org/dc/terms/": "dcterms",
    "http://purl.org/vocab/vann/": "vann",
}


def _prefixed(iri: str, prefix: str, namespace: str) -> str:
    """Convert a full IRI to prefix:LocalName."""
    if iri.startswith(namespace):
        return f"{prefix}:{iri[len(namespace):]}"
    for ns, pfx in KNOWN_PREFIXES.items():
        if iri.startswith(ns):
            return f"{pfx}:{iri[len(ns):]}"
    return iri


def _local_name(iri: str) -> str:
    """Extract the local name from an IRI."""
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.rsplit("/", 1)[-1]


def _term_anchor(iri: str, namespace: str) -> str:
    """Return an anchor id for a term IRI."""
    if iri.startswith(namespace):
        return iri[len(namespace):]
    return _local_name(iri)


def _term_link(iri: str, prefix: str, namespace: str, classes: list, properties: list) -> str:
    """Return an HTML anchor link for a term IRI."""
    pname = _prefixed(iri, prefix, namespace)
    anchor = _term_anchor(iri, namespace)
    # Check if the term is in our vocabulary
    all_iris = {c["iri"] for c in classes} | {p["iri"] for p in properties}
    if iri in all_iris:
        return f'<a href="#{anchor}">{pname}</a>'
    return f'<code>{pname}</code>'


def _build_hierarchy(classes: list[dict], namespace: str) -> list[dict]:
    """Build a nested tree from flat class list using superclasses/subclasses.

    Returns a list of root nodes, each with a 'children' list.
    """
    by_iri = {c["iri"]: c for c in classes}

    # Find roots: classes whose superclasses are all outside the namespace
    roots = []
    for cls in classes:
        supers_in_ns = [s for s in cls.get("superclasses", []) if s in by_iri]
        if not supers_in_ns:
            roots.append(cls["iri"])

    def _build_node(iri: str, visited: set) -> dict | None:
        if iri in visited or iri not in by_iri:
            return None
        visited.add(iri)
        cls = by_iri[iri]
        children = []
        for child_iri in cls.get("subclasses", []):
            node = _build_node(child_iri, visited)
            if node:
                children.append(node)
        return {
            "iri": iri,
            "local_name": cls["local_name"],
            "prefixed_name": cls.get("prefixed_name", cls["local_name"]),
            "label": cls.get("label"),
            "comment": cls.get("comment"),
            "children": children,
        }

    tree = []
    visited: set[str] = set()
    for root_iri in roots:
        node = _build_node(root_iri, visited)
        if node:
            tree.append(node)

    # Any classes not yet visited (cycles, disconnected) become additional roots
    for cls in classes:
        if cls["iri"] not in visited:
            node = _build_node(cls["iri"], visited)
            if node:
                tree.append(node)

    return tree


# Inline CSS — ReSpec-style two-column layout, works with file:// protocol
DEFAULT_CSS = r"""
:root, [data-theme="light"] {
    --bg: #ffffff; --fg: #1a1a2e; --accent: #0066cc;
    --border: #e0e0e0; --code-bg: #f5f5f5; --nav-bg: #f8f9fa;
    --toc-bg: #f8f9fa; --term-header-bg: #f0f4f8;
}
[data-theme="dark"] {
    --bg: #1a1a2e; --fg: #e0e0e0; --accent: #66b3ff;
    --border: #333; --code-bg: #2d2d44; --nav-bg: #16213e;
    --toc-bg: #16213e; --term-header-bg: #1e2a3a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: var(--bg); color: var(--fg); line-height: 1.6;
       display: flex; flex-direction: column; min-height: 100vh; }
header { background: var(--nav-bg); border-bottom: 1px solid var(--border); padding: 0.75rem 1.5rem; }
header nav { display: flex; align-items: center; gap: 1rem; max-width: 1400px; margin: 0 auto; }
header .logo { font-weight: 700; font-size: 1.1rem; text-decoration: none; color: var(--fg); }
header .version { font-size: 0.85rem; color: var(--accent); }
#theme-toggle { background: none; border: none; cursor: pointer; font-size: 1.2rem; margin-left: auto; color: var(--fg); }

/* Two-column layout */
.page-wrapper { display: flex; flex: 1; max-width: 1400px; margin: 0 auto; width: 100%; }

/* Sticky sidebar TOC */
.sidebar { width: 280px; flex-shrink: 0; position: sticky; top: 0; height: 100vh;
           overflow-y: auto; padding: 1.5rem 1rem; border-right: 1px solid var(--border);
           background: var(--toc-bg); font-size: 0.85rem; }
.sidebar h2 { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;
              margin: 0 0 0.75rem; border: none; color: #666; }
.sidebar ol { padding-left: 1.2rem; }
.sidebar li { margin: 0.15rem 0; }
.toc-title { display: block; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;
             font-weight: 700; color: #666; text-decoration: none; padding: 0.35rem 0.75rem;
             margin-bottom: 0.5rem; border-radius: 4px; }
.toc-title:hover { color: var(--accent); background: var(--border); }
[data-theme="dark"] .toc-title { color: #aaa; }
.sidebar a { text-decoration: none; color: var(--fg); display: block; padding: 0.3rem 0.75rem; border-radius: 4px; }
.sidebar a:hover { color: var(--accent); background: var(--border); }
.toc-list { list-style: none; padding: 0; margin: 0; }
.toc-list > li { margin: 0; }
.toc-count { display: inline-block; background: var(--border); color: #666; font-size: 0.75em;
             padding: 0.1rem 0.45rem; border-radius: 10px; margin-left: 0.3rem; font-weight: normal; }
[data-theme="dark"] .toc-count { color: #aaa; }
.toc-sub { list-style: none; padding: 0; margin: 0; max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
.toc-list > li:hover .toc-sub, .toc-sub:hover { max-height: 60vh; overflow-y: auto; }
.toc-sub li { margin: 0; }
.toc-sub a { padding: 0.2rem 0.75rem 0.2rem 1.5rem; font-size: 0.82em; color: #666; }
[data-theme="dark"] .toc-sub a { color: #aaa; }
.toc-sub a:hover { color: var(--accent); }

/* Content area */
.content { flex: 1; padding: 2rem 2.5rem; min-width: 0; }

/* Fallback for pages without sidebar (term pages) */
main { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }

footer { text-align: center; padding: 2rem; font-size: 0.85rem; color: #888; border-top: 1px solid var(--border); margin-top: auto; }
a { color: var(--accent); }
h1 { margin-bottom: 0.5rem; font-size: 1.8rem; }
h2 { margin: 2rem 0 0.75rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.25rem; font-size: 1.4rem; }
h3 { margin: 1.5rem 0 0.5rem; font-size: 1.15rem; }
code { background: var(--code-bg); padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.9em; }
.breadcrumb { margin-bottom: 1rem; font-size: 0.9rem; }
.narrative { margin-bottom: 2rem; }
.sidecar-content { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed var(--border); }

/* ReSpec-style metadata header */
.respec-header { margin-bottom: 2rem; }
.respec-header h1 { font-size: 2rem; margin-bottom: 0.25rem; }
.respec-header .subtitle { font-size: 1.2rem; color: #666; margin-bottom: 0.75rem; }
[data-theme="dark"] .respec-header .subtitle { color: #aaa; }
.respec-header .doc-status { color: var(--accent); font-size: 1.1rem; margin-bottom: 1.5rem; }
.respec-header dl { margin: 0 0 1.5rem; }
.respec-header dt { font-weight: 700; margin-top: 0.6rem; margin-bottom: 0.1rem; }
.respec-header dd { margin: 0 0 0.1rem 1.5rem; }
.respec-header .copyright { font-size: 0.85rem; color: #666; margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
[data-theme="dark"] .respec-header .copyright { color: #aaa; }
.respec-header .contributors { font-size: 0.9rem; margin-top: 0.75rem; }

/* Table of Contents (inline fallback) */
.toc { background: var(--toc-bg); border: 1px solid var(--border); border-radius: 4px; padding: 1rem 1.5rem; margin: 1.5rem 0; }
.toc h2 { margin: 0 0 0.5rem; border: none; font-size: 1.1rem; }
.toc ol { padding-left: 1.5rem; }
.toc li { margin: 0.2rem 0; }
.toc a { text-decoration: none; }
.toc a:hover { text-decoration: underline; }

/* Term definition tables */
.term-def { margin-bottom: 2rem; padding: 0; }
.term-def h3 { margin-top: 0; }
.term-contents { width: 100%; border-collapse: collapse; margin: 0.5rem 0 1rem; }
.term-contents th { text-align: left; padding: 0.4rem 0.75rem; width: 180px; vertical-align: top;
                     background: var(--term-header-bg); border-bottom: 1px solid var(--border); font-weight: 600; font-size: 0.9rem; }
.term-contents td { padding: 0.4rem 0.75rem; border-bottom: 1px solid var(--border); }
.table-separator td { padding: 0; height: 0.5rem; border: none; }

/* Legacy summary table */
.term-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.term-table th, .term-table td { text-align: left; padding: 0.5rem; border-bottom: 1px solid var(--border); }
.term-table th { font-weight: 600; background: var(--nav-bg); }

/* Concept hierarchy tree */
.concept-list { list-style: none; padding-left: 0; }
.concept-list ul { list-style: none; padding-left: 1.5rem; }
.concept-list li { margin: 0.15rem 0; }
.concept-list .tree-label { font-weight: 500; }
.concept-list .tree-desc { color: #666; font-size: 0.9em; margin-left: 0.5rem; }
[data-theme="dark"] .concept-list .tree-desc { color: #aaa; }
.btn-hierarchy { background: var(--accent); color: #fff; border: none; cursor: pointer;
                 padding: 0.3rem 0.8rem; border-radius: 3px; font-size: 0.85rem; margin: 0.5rem 0.25rem 0.75rem 0; }
.btn-hierarchy:hover { opacity: 0.9; }

/* SHACL shapes */
.shape-block { margin-bottom: 1.5rem; }
.shape-block h3 { font-size: 1rem; }
.shape-constraints { width: 100%; border-collapse: collapse; margin: 0.5rem 0; }
.shape-constraints th, .shape-constraints td { text-align: left; padding: 0.4rem 0.75rem; border-bottom: 1px solid var(--border); }
.shape-constraints th { background: var(--term-header-bg); font-weight: 600; font-size: 0.9rem; }

/* Serializations */
.serialization-links { list-style: none; padding: 0; }
.serialization-links li { display: inline-block; margin-right: 1rem; }
.serialization-links a { display: inline-block; padding: 0.3rem 0.8rem; border: 1px solid var(--accent); border-radius: 3px; text-decoration: none; }
.serialization-links a:hover { background: var(--accent); color: #fff; }

.iri { margin-bottom: 1rem; }

/* Back to top button */
.back-to-top { position: fixed; bottom: 2rem; right: 2rem; background: var(--accent); color: #fff;
               width: 2.5rem; height: 2.5rem; border-radius: 50%; text-align: center; line-height: 2.5rem;
               text-decoration: none; font-size: 1.2rem; opacity: 0; transition: opacity 0.3s;
               z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
.back-to-top.visible { opacity: 1; }
.back-to-top:hover { background: var(--fg); color: var(--bg); }

@media (max-width: 900px) {
    .page-wrapper { flex-direction: column; }
    .sidebar { width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); }
}
"""


def render_site(manifest: dict, output_dir: Path) -> None:
    """Render the full static site from a manifest dict."""
    output_dir.mkdir(parents=True, exist_ok=True)

    prefix = manifest["metadata"]["prefix"]
    namespace = manifest["metadata"]["namespace"]
    all_classes = manifest["classes"]
    all_properties = manifest["properties"]

    env = Environment(
        loader=PackageLoader("blathers", "templates"),
        autoescape=select_autoescape(["html"]),
    )

    # Register custom filters
    env.filters["prefixed"] = lambda iri: _prefixed(iri, prefix, namespace)
    env.filters["local_name"] = _local_name
    env.filters["term_anchor"] = lambda iri: _term_anchor(iri, namespace)
    env.filters["term_link"] = lambda iri: Markup(_term_link(iri, prefix, namespace, all_classes, all_properties))

    # Write manifest JSON
    (output_dir / "site-data.json").write_text(json.dumps(manifest, indent=2))

    # Write CSS to assets (for term pages that link externally)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "style.css").write_text(DEFAULT_CSS)

    # Build hierarchy tree
    hierarchy = _build_hierarchy(all_classes, namespace)

    # Common template context
    ctx = {
        "metadata": manifest["metadata"],
        "classes": all_classes,
        "properties": all_properties,
        "shapes": manifest["shapes"],
        "sections": manifest["sections"],
        "conneg": manifest.get("conneg", {}),
        "hierarchy": hierarchy,
        "inline_css": DEFAULT_CSS,
    }

    # Render index
    index_tpl = env.get_template("index.html.j2")
    (output_dir / "index.html").write_text(index_tpl.render(base_path="", **ctx))

    # Render class pages
    classes_dir = output_dir / "classes"
    classes_dir.mkdir(exist_ok=True)
    term_tpl = env.get_template("term.html.j2")
    for cls in all_classes:
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
    for prop in all_properties:
        html = term_tpl.render(
            base_path="../",
            term=prop,
            term_type="properties",
            **ctx,
        )
        (props_dir / f"{prop['local_name']}.html").write_text(html)
