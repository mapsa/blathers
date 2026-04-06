"""Load and execute SPARQL example queries against the ontology graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from rdflib import Graph


@dataclass
class ExampleQuery:
    title: str
    description: str
    order: int
    category: str = "Examples"
    sparql_text: str = ""
    columns: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    error: Optional[str] = None


def _prefixed(value: object, ns_map: dict[str, str]) -> str:
    """Convert an rdflib term to a prefixed name if possible."""
    s = str(value)
    for prefix, ns in ns_map.items():
        if s.startswith(ns):
            return f"{prefix}:{s[len(ns):]}"
    return s


def load_and_run_queries(sparql_dir: Path, graph: Graph) -> list[ExampleQuery]:
    """Load queries listed in queries.yaml, execute each against graph, return results."""
    manifest_path = sparql_dir / "queries.yaml"
    if not manifest_path.exists():
        return []

    with manifest_path.open() as f:
        entries = yaml.safe_load(f) or []

    ns_map = {str(prefix): str(ns) for prefix, ns in graph.namespaces() if prefix}

    queries: list[ExampleQuery] = []
    for entry in entries:
        path = sparql_dir / entry["file"]
        if not path.exists():
            continue

        sparql_text = path.read_text().strip()
        title = entry.get("title", path.stem)
        description = entry.get("description", "")
        order = int(entry.get("order", 99))
        category = entry.get("category", "Examples")

        try:
            result = graph.query(sparql_text)
            columns = [str(v) for v in result.vars]
            rows = [
                [_prefixed(cell, ns_map) if cell is not None else "" for cell in row]
                for row in result
            ]
            queries.append(ExampleQuery(
                title=title,
                description=description,
                order=order,
                category=category,
                sparql_text=sparql_text,
                columns=columns,
                rows=rows,
            ))
        except Exception as exc:
            queries.append(ExampleQuery(
                title=title,
                description=description,
                order=order,
                category=category,
                sparql_text=sparql_text,
                error=str(exc),
            ))

    return sorted(queries, key=lambda q: q.order)
