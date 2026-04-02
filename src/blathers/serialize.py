"""Ontology serialization to multiple RDF formats."""

from __future__ import annotations

import shutil
from pathlib import Path

from rdflib import Graph

FORMAT_MAP = {
    "ttl": ("turtle", "ontology.ttl"),
    "jsonld": ("json-ld", "ontology.jsonld"),
    "nt": ("nt", "ontology.nt"),
    "owl": ("xml", "ontology.owl"),
}


def serialize_ontology(source_path: Path, output_dir: Path, formats: list[str]) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    g = Graph()
    g.parse(str(source_path), format="turtle")

    for fmt in formats:
        if fmt not in FORMAT_MAP:
            continue

        rdflib_format, filename = FORMAT_MAP[fmt]
        out_path = output_dir / filename

        if fmt == "ttl":
            shutil.copy2(source_path, out_path)
        elif fmt == "jsonld":
            # Passing a context ensures @context and @graph keys are present
            g.serialize(
                str(out_path),
                format=rdflib_format,
                context={"owl": "http://www.w3.org/2002/07/owl#"},
            )
        else:
            g.serialize(str(out_path), format=rdflib_format)

        created.append(out_path)

    return created
