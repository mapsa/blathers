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


def _build_hierarchy(classes: list[dict], namespace: str, individuals: list[dict] | None = None) -> list[dict]:
    """Build a nested tree from flat class list using superclasses/subclasses.

    Returns a list of root nodes, each with a 'children' list.
    Individuals are included as leaf nodes under their parent class.
    """
    by_iri = {c["iri"]: c for c in classes}

    # Build map of class IRI -> individuals that are instances of that class
    ind_by_class: dict[str, list[dict]] = {}
    for ind in (individuals or []):
        for type_iri in ind.get("types", []):
            ind_by_class.setdefault(type_iri, []).append(ind)

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
        # Append individuals as leaf nodes
        for ind in ind_by_class.get(iri, []):
            children.append({
                "iri": ind["iri"],
                "local_name": ind["local_name"],
                "prefixed_name": ind.get("prefixed_name", ind["local_name"]),
                "label": ind.get("label"),
                "comment": ind.get("comment"),
                "children": [],
                "is_individual": True,
                "types": ind.get("types", []),
            })
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
    --bg: #ffffff; --fg: #1a1a2e; --accent: #635bff;
    --accent-hover: #5046e5;
    --border: #e3e8ee; --code-bg: #f6f9fc; --nav-bg: #f6f9fc;
    --toc-bg: #f6f9fc; --term-header-bg: #f0f4f8;
    --text-secondary: #697386;
}
[data-theme="dark"] {
    --bg: #0a1628; --fg: #e3e8ee; --accent: #7c73ff;
    --accent-hover: #9b94ff;
    --border: #2a3a50; --code-bg: #1a2742; --nav-bg: #0e1d33;
    --toc-bg: #0e1d33; --term-header-bg: #152238;
    --text-secondary: #8898aa;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: var(--bg); color: var(--fg); line-height: 1.6;
       display: flex; flex-direction: column; min-height: 100vh; }
header { background: var(--nav-bg); border-bottom: 1px solid var(--border); padding: 0.6rem 1.5rem;
         position: sticky; top: 0; z-index: 50; backdrop-filter: blur(8px); }
header nav { display: flex; align-items: center; gap: 1rem; max-width: 1400px; margin: 0 auto; }
header .logo { font-weight: 700; font-size: 1.1rem; text-decoration: none; color: var(--fg); }
header .version { font-size: 0.85rem; color: var(--accent); }
/* Theme toggle switch */
.theme-switch { position: relative; display: inline-block; width: 48px; height: 26px; cursor: pointer; margin-left: auto; flex-shrink: 0; }
.theme-switch input { display: none; }
.theme-slider { position: absolute; inset: 0; background: #e0e0e0; border-radius: 26px; transition: background 0.3s; }
.theme-slider::before { content: ""; position: absolute; width: 20px; height: 20px; left: 3px; bottom: 3px;
                         background: #fff; border-radius: 50%; transition: transform 0.3s; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
.theme-switch input:checked + .theme-slider { background: #4a5568; }
.theme-switch input:checked + .theme-slider::before { transform: translateX(22px); }
.theme-icon { position: absolute; top: 50%; transform: translateY(-50%); }
.theme-icon.sun { left: 5px; color: #f6ad55; }
.theme-icon.moon { right: 5px; color: #e2e8f0; }

/* Two-column layout */
.page-wrapper { display: flex; flex: 1; max-width: 1400px; margin: 0 auto; width: 100%; }

/* Sticky sidebar TOC */
.sidebar { width: 280px; flex-shrink: 0; position: sticky; top: 3rem; align-self: flex-start;
           max-height: calc(100vh - 3rem); overflow-y: auto; padding: 1.5rem 1rem; border-right: 1px solid var(--border);
           background: var(--toc-bg); font-size: 0.85rem; }
.sidebar h2 { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;
              margin: 0 0 0.75rem; border: none; color: var(--text-secondary); }
.sidebar ol { padding-left: 1.2rem; }
.sidebar li { margin: 0.15rem 0; }
.toc-title { display: block; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;
             font-weight: 700; color: var(--text-secondary); text-decoration: none; padding: 0.35rem 0.75rem;
             margin-bottom: 0.5rem; border-radius: 6px; }
.toc-title:hover { color: var(--accent); background: var(--border); text-decoration: none; }
.sidebar a { text-decoration: none; color: var(--fg); display: block; padding: 0.3rem 0.75rem; border-radius: 6px; }
.sidebar a:hover { color: var(--accent); background: var(--border); text-decoration: none; }
.toc-list { list-style: none; padding: 0; margin: 0; }
.toc-list > li { margin: 0; }
.toc-count { display: inline-block; background: var(--border); color: var(--text-secondary); font-size: 0.75em;
             padding: 0.1rem 0.45rem; border-radius: 10px; margin-left: 0.3rem; font-weight: normal; }
.toc-sub { list-style: none; padding: 0; margin: 0; max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
.toc-sub.open { max-height: 60vh; overflow-y: auto; }
.toc-sub li { margin: 0; }
.toc-sub a { padding: 0.2rem 0.75rem 0.2rem 1.5rem; font-size: 0.82em; color: var(--text-secondary); }
.toc-sub a:hover { color: var(--accent); }

/* Content area */
.content { flex: 1; padding: 2rem 2.5rem; min-width: 0; padding-bottom: 60vh; }

/* Fallback for pages without sidebar (term pages) */
main { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }

footer { text-align: center; padding: 2rem; font-size: 0.85rem; color: var(--text-secondary); border-top: 1px solid var(--border); margin-top: auto; }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); text-decoration: underline; }
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
.respec-header .subtitle { font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.respec-header .doc-status { color: var(--accent); font-size: 1rem; margin-bottom: 1rem; }
.respec-header dl { margin: 0 0 0.75rem; display: grid; grid-template-columns: auto 1fr; gap: 0.2rem 1rem; align-items: baseline; }
.respec-header dt { font-weight: 700; white-space: nowrap; }
.respec-header dd { margin: 0; }
.respec-header .copyright { font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px solid var(--border); }
.respec-header .contributors { font-size: 0.9rem; margin-top: 0.5rem; }
.orcid-link { text-decoration: none; }
.orcid-icon { width: 16px; height: 16px; vertical-align: text-bottom; display: inline-block; }

/* Table of Contents (inline fallback) */
.toc { background: var(--toc-bg); border: 1px solid var(--border); border-radius: 6px; padding: 1rem 1.5rem; margin: 1.5rem 0; }
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

/* Hierarchy two-panel layout */
.hierarchy-section { display: flex; gap: 1.5rem; min-height: 300px; }
.hierarchy-left { flex: 0 0 40%; overflow-y: auto; max-height: 70vh;
                  border: 1px solid var(--border); border-radius: 6px; padding: 1rem; }
.hierarchy-right { flex: 1; position: sticky; top: 5rem; align-self: flex-start;
                   border: 1px solid var(--border); border-radius: 6px; padding: 1.25rem;
                   background: var(--nav-bg); max-height: 70vh; overflow-y: auto; }
.hierarchy-right .detail-empty { color: var(--text-secondary); font-style: italic; }
.hierarchy-right h3 { margin: 0 0 0.5rem; font-size: 1.2rem; }
.hierarchy-right .detail-iri { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.75rem; word-break: break-all; }
.hierarchy-right .detail-row { margin-bottom: 0.5rem; }
.hierarchy-right .detail-row dt { font-weight: 600; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.1rem; }
.hierarchy-right .detail-row dd { margin: 0; }
.hierarchy-right .detail-def { margin-bottom: 0.75rem; line-height: 1.5; }
.hierarchy-right .detail-link { display: inline-block; margin-top: 0.5rem; font-weight: 500; }

/* Selected term in tree */
.hierarchy-tree .tree-term.selected { background: var(--accent); color: #fff; }

/* Hierarchy tree — file-tree style */
.hierarchy-tree { list-style: none; padding: 0; margin: 0; font-size: 0.95rem; }
.hierarchy-tree ul { list-style: none; padding: 0; margin: 0; }
.hierarchy-tree li { position: relative; padding-left: 2rem; }
.hierarchy-tree > ul > li { padding-left: 0; } /* root items no indent */

/* Vertical connector lines */
.hierarchy-tree li li::before { content: ""; position: absolute; left: 0.6rem; top: 0; bottom: 0;
                                 border-left: 2px solid var(--accent); opacity: 0.25; }
.hierarchy-tree li li:last-child::before { bottom: calc(100% - 1.1rem); }

/* Horizontal branch lines */
.hierarchy-tree li li::after { content: ""; position: absolute; left: 0.6rem; top: 1.1rem;
                                width: 1rem; border-top: 2px solid var(--accent); opacity: 0.25; }

/* Class chips — bold, prominent */
.hierarchy-tree .tree-term { display: inline-block; padding: 0.25rem 0.75rem; margin: 0.2rem 0;
                              border-radius: 6px; text-decoration: none; color: var(--fg);
                              font-weight: 600; font-size: 0.9rem; transition: all 0.15s;
                              position: relative; z-index: 1; background: var(--code-bg);
                              border: 1px solid transparent; }
.hierarchy-tree .tree-term:hover { background: var(--accent); color: #fff; border-color: var(--accent); }

/* Individual nodes — lighter pill style with dot indicator */
.tree-individual { font-weight: 400 !important; font-style: normal !important; background: transparent !important;
                   border: 1px dashed var(--border) !important; color: var(--text-secondary) !important; }
.tree-individual::before { content: ""; display: inline-block; width: 6px; height: 6px;
                           border-radius: 50%; background: var(--accent); opacity: 0.5;
                           margin-right: 0.4rem; vertical-align: middle; }
.tree-individual:hover { background: var(--accent) !important; color: #fff !important;
                         border-color: var(--accent) !important; }
.tree-individual:hover::before { background: #fff; opacity: 1; }
.instance-chip { display: inline-block; padding: 0.15rem 0.6rem; background: var(--code-bg);
                 border-radius: 6px; font-size: 0.85em; margin: 0.1rem 0.2rem;
                 border: 1px dashed var(--border); color: var(--text-secondary); }

/* Tooltip */
.hierarchy-tree .tree-term[title] { cursor: pointer; }

/* SHACL shapes */
.shape-block { margin-bottom: 1.5rem; }
.shape-block h3 { font-size: 1rem; }
.shape-constraints { width: 100%; border-collapse: collapse; margin: 0.5rem 0; }
.shape-constraints th, .shape-constraints td { text-align: left; padding: 0.4rem 0.75rem; border-bottom: 1px solid var(--border); }
.shape-constraints th { background: var(--term-header-bg); font-weight: 600; font-size: 0.9rem; }

/* Serializations */
.serialization-links { list-style: none; padding: 0; }
.serialization-links li { display: inline-block; margin-right: 1rem; }
.serialization-links a { display: inline-block; padding: 0.3rem 0.8rem; border: 1px solid var(--accent); border-radius: 6px; text-decoration: none; }
.serialization-links a:hover { background: var(--accent); color: #fff; }

.iri { margin-bottom: 1rem; }

/* Back to top button */
.back-to-top { position: fixed; bottom: 2rem; right: 2rem; background: var(--accent); color: #fff;
               width: 2.5rem; height: 2.5rem; border-radius: 50%; text-align: center; line-height: 2.5rem;
               text-decoration: none; font-size: 1.2rem; opacity: 0; transition: opacity 0.3s;
               z-index: 100; box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
.back-to-top.visible { opacity: 1; }
.back-to-top:hover { background: var(--accent-hover); color: #fff; text-decoration: none; }

/* Search */
.sidebar-search { width: 100%; padding: 0.4rem 0.6rem; border: 1px solid var(--border); border-radius: 6px;
                   background: var(--bg); color: var(--fg); font-size: 0.85rem; margin-bottom: 0.75rem;
                   outline: none; }
.sidebar-search:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(99,91,255,0.15); }
.sidebar-search::placeholder { color: var(--text-secondary); }
.toc-sub li.search-hidden { display: none; }

/* Scroll spy active */
.toc-list a.active { color: var(--accent); font-weight: 600; border-left: 3px solid var(--accent); padding-left: calc(0.75rem - 3px); }

/* Smooth scroll + offset */
html { scroll-behavior: smooth; }
.term-def, section[id], .shape-block { scroll-margin-top: 4.5rem; }

/* Highlight animation */
@keyframes term-flash { from { background: rgba(99,91,255,0.12); } to { background: transparent; } }
.term-def.highlight { animation: term-flash 1.5s ease-out; }

@media (max-width: 900px) {
    .page-wrapper { flex-direction: column; }
    .sidebar { width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); }
    .hierarchy-section { flex-direction: column; }
    .hierarchy-left { max-height: 50vh; }
    .hierarchy-right { position: static; }
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
    hierarchy = _build_hierarchy(all_classes, namespace, manifest.get("individuals", []))

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
