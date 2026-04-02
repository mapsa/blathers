"""Convention validator — naming, metadata, prefix hygiene."""

from __future__ import annotations

import re

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from blathers.validators.base import Severity, ValidationResult


def _local_name(iri: str) -> str:
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.rsplit("/", 1)[-1]


def _is_pascal_case(name: str) -> bool:
    return bool(re.match(r"^[A-Z][a-zA-Z0-9]*$", name))


def _is_camel_case(name: str) -> bool:
    return bool(re.match(r"^[a-z][a-zA-Z0-9]*$", name))


class ConventionValidator:
    """Checks naming conventions and required metadata."""

    def __init__(self, graph: Graph, namespace: str) -> None:
        self.graph = graph
        self.namespace = namespace

    def validate(self) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        results.extend(self._check_naming())
        results.extend(self._check_metadata())
        return results

    def _check_naming(self) -> list[ValidationResult]:
        results = []

        for cls_iri in self.graph.subjects(RDF.type, OWL.Class):
            iri_str = str(cls_iri)
            if not iri_str.startswith(self.namespace):
                continue
            name = _local_name(iri_str)
            if not _is_pascal_case(name):
                results.append(ValidationResult(
                    validator="conventions",
                    severity=Severity.WARNING,
                    message=f"{name} — class names should be PascalCase",
                    term=iri_str,
                ))

        prop_types = [OWL.ObjectProperty, OWL.DatatypeProperty]
        seen = set()
        for pt in prop_types:
            for prop_iri in self.graph.subjects(RDF.type, pt):
                iri_str = str(prop_iri)
                if not iri_str.startswith(self.namespace) or iri_str in seen:
                    continue
                seen.add(iri_str)
                name = _local_name(iri_str)
                if not _is_camel_case(name):
                    results.append(ValidationResult(
                        validator="conventions",
                        severity=Severity.WARNING,
                        message=f"{name} — property names should be camelCase",
                        term=iri_str,
                    ))

        return results

    def _check_metadata(self) -> list[ValidationResult]:
        results = []

        ont_iri = None
        for s in self.graph.subjects(RDF.type, OWL.Ontology):
            ont_iri = s
            break

        if ont_iri is None:
            results.append(ValidationResult(
                validator="conventions",
                severity=Severity.ERROR,
                message="No owl:Ontology declaration found",
            ))
            return results

        checks = [
            (OWL.versionInfo, "version"),
            (DCTERMS.license, "license"),
            (DCTERMS.creator, "creator"),
        ]
        has_title = (
            self.graph.value(ont_iri, DCTERMS.title) is not None
            or self.graph.value(ont_iri, RDFS.label) is not None
        )
        if not has_title:
            results.append(ValidationResult(
                validator="conventions",
                severity=Severity.WARNING,
                message="Ontology missing title (dcterms:title or rdfs:label)",
            ))

        for predicate, name in checks:
            if self.graph.value(ont_iri, predicate) is None:
                results.append(ValidationResult(
                    validator="conventions",
                    severity=Severity.WARNING,
                    message=f"Ontology missing {name} ({predicate})",
                ))

        return results
