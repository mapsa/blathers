"""High-risk AI system classification using SHACL shapes (e.g. AIRO Annex III shapes)."""

from __future__ import annotations

import re
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, URIRef

AIRO = Namespace("https://w3id.org/airo#")
VAIR = Namespace("https://w3id.org/vair#")
SH   = Namespace("http://www.w3.org/ns/shacl#")
PRISM = Namespace("https://w3id.org/prism#")

# Properties whose object values may be VAIR classes used as individuals
_CLASS_AS_VALUE_PROPS = {AIRO.hasPurpose, AIRO.isAppliedWithinDomain, AIRO.hasCapability}

_ANNEX_LABEL_RE = re.compile(r"AnnexIII[-_](\w+)$", re.IGNORECASE)


def _add_self_typing(graph: Graph) -> None:
    """Bridge the class-as-value pattern: vair:X rdf:type vair:X.

    AIRO examples use VAIR class IRIs directly as property values rather than
    typed individuals. SHACL sh:class checks require rdf:type, so we add a
    self-typing triple for each VAIR IRI used as a purpose/domain/capability.
    """
    additions = []
    for s, p, o in graph:
        if p in _CLASS_AS_VALUE_PROPS and str(o).startswith(str(VAIR)):
            additions.append((o, RDF.type, o))
    for triple in additions:
        graph.add(triple)


def _shape_label(shape_iri: URIRef) -> str:
    """Extract a human-readable label from a shape IRI like ex:AnnexIII-5b."""
    local = str(shape_iri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
    m = _ANNEX_LABEL_RE.search(local)
    if m:
        suffix = m.group(1)
        # Insert space before digit run: "4b" -> "4b", keep as-is but prefix
        return f"Annex III {suffix}"
    return local


def classify_high_risk(data_graph: Graph, shapes_paths: list[Path]) -> int:
    """Run SHACL classification shapes and materialise results into data_graph.

    For each violation (system matches a high-risk shape), adds:
        <system> prism:isHighRiskUnder "Annex III Xn"

    Returns the number of high-risk classifications added.
    """
    if not shapes_paths:
        return 0

    shapes_graph = Graph()
    for p in shapes_paths:
        shapes_graph.parse(str(p))

    _add_self_typing(data_graph)

    _, results_graph, _ = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
    )

    count = 0
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        system = results_graph.value(result, SH.focusNode)
        shape  = results_graph.value(result, SH.sourceShape)
        if system and shape:
            label = _shape_label(shape)
            data_graph.add((system, PRISM.isHighRiskUnder, Literal(label)))
            count += 1

    return count
