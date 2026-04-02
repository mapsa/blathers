"""Overlap/redundancy validator — detects shadowed imported terms."""

from __future__ import annotations

from rdflib import Graph
from rdflib.namespace import OWL, RDF

from blathers.validators.base import Severity, ValidationResult


def _local_name(iri: str) -> str:
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.rsplit("/", 1)[-1]


def _extract_term_local_names(graph: Graph, namespace: str | None = None) -> dict[str, str]:
    terms: dict[str, str] = {}
    type_preds = [OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]
    for type_pred in type_preds:
        for s in graph.subjects(RDF.type, type_pred):
            iri = str(s)
            if namespace and not iri.startswith(namespace):
                continue
            name = _local_name(iri)
            terms[name] = iri
    return terms


class OverlapValidator:
    def __init__(
        self,
        local_graph: Graph,
        local_namespace: str,
        imported_graphs: dict[str, Graph],
        allowlist: set[str],
    ) -> None:
        self.local_graph = local_graph
        self.local_namespace = local_namespace
        self.imported_graphs = imported_graphs
        self.allowlist = allowlist

    def _expand_allowlist(self) -> set[str]:
        names = set()
        for entry in self.allowlist:
            if ":" in entry:
                names.add(entry.split(":", 1)[1])
            else:
                names.add(entry)
        return names

    def validate(self) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        allowed_names = self._expand_allowlist()
        local_terms = _extract_term_local_names(self.local_graph, self.local_namespace)

        for import_uri, imported_graph in self.imported_graphs.items():
            imported_terms = _extract_term_local_names(imported_graph)

            for local_name, local_iri in local_terms.items():
                if local_name in allowed_names:
                    continue
                if local_name in imported_terms:
                    results.append(ValidationResult(
                        validator="overlap",
                        severity=Severity.WARNING,
                        message=(
                            f"{local_name} — shadows {imported_terms[local_name]} "
                            f"(imported via {import_uri})"
                        ),
                        term=local_iri,
                    ))

        return results
