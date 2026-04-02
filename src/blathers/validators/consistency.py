"""Consistency validator — dangling refs, orphan terms, missing labels."""

from __future__ import annotations

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from blathers.validators.base import Severity, ValidationResult


class ConsistencyValidator:
    """Checks ontology internal consistency."""

    def __init__(self, graph: Graph, namespace: str) -> None:
        self.graph = graph
        self.namespace = namespace

    def validate(self) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        results.extend(self._check_dangling_references())
        results.extend(self._check_missing_labels())
        results.extend(self._check_orphan_terms())
        return results

    def _local_classes(self) -> set[str]:
        return {
            str(s)
            for s in self.graph.subjects(RDF.type, OWL.Class)
            if str(s).startswith(self.namespace)
        }

    def _local_properties(self) -> set[str]:
        prop_types = [OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]
        props = set()
        for pt in prop_types:
            for s in self.graph.subjects(RDF.type, pt):
                if str(s).startswith(self.namespace):
                    props.add(str(s))
        return props

    def _all_local_terms(self) -> set[str]:
        return self._local_classes() | self._local_properties()

    def _local_name(self, iri: str) -> str:
        if "#" in iri:
            return iri.split("#")[-1]
        return iri.rsplit("/", 1)[-1]

    def _check_dangling_references(self) -> list[ValidationResult]:
        results = []
        all_classes = set()
        for s in self.graph.subjects(RDF.type, OWL.Class):
            all_classes.add(str(s))

        for prop_iri in self._local_properties():
            prop_ref = URIRef(prop_iri)
            for pred_name, pred in [("domain", RDFS.domain), ("range", RDFS.range)]:
                obj = self.graph.value(prop_ref, pred)
                if obj is None:
                    continue
                obj_str = str(obj)
                if obj_str.startswith(self.namespace) and obj_str not in all_classes:
                    results.append(ValidationResult(
                        validator="consistency",
                        severity=Severity.ERROR,
                        message=f"{self._local_name(prop_iri)} — {pred_name} {self._local_name(obj_str)} not defined",
                        term=prop_iri,
                    ))
        return results

    def _check_missing_labels(self) -> list[ValidationResult]:
        results = []
        for term_iri in self._all_local_terms():
            ref = URIRef(term_iri)
            name = self._local_name(term_iri)
            if not self.graph.value(ref, RDFS.label):
                results.append(ValidationResult(
                    validator="consistency",
                    severity=Severity.WARNING,
                    message=f"{name} — missing rdfs:label",
                    term=term_iri,
                ))
            if not self.graph.value(ref, RDFS.comment):
                results.append(ValidationResult(
                    validator="consistency",
                    severity=Severity.WARNING,
                    message=f"{name} — missing rdfs:comment",
                    term=term_iri,
                ))
        return results

    def _check_orphan_terms(self) -> list[ValidationResult]:
        results = []
        local_classes = self._local_classes()
        local_props = self._local_properties()

        referenced_classes: set[str] = set()
        for cls_iri in local_classes:
            for obj in self.graph.objects(URIRef(cls_iri), RDFS.subClassOf):
                if str(obj).startswith(self.namespace):
                    referenced_classes.add(str(obj))
        for prop_iri in local_props:
            domain = self.graph.value(URIRef(prop_iri), RDFS.domain)
            range_ = self.graph.value(URIRef(prop_iri), RDFS.range)
            if domain:
                referenced_classes.add(str(domain))
            if range_:
                referenced_classes.add(str(range_))

        for cls_iri in local_classes:
            has_subclass = any(
                str(s).startswith(self.namespace)
                for s in self.graph.subjects(RDFS.subClassOf, URIRef(cls_iri))
            )
            if cls_iri not in referenced_classes and not has_subclass:
                results.append(ValidationResult(
                    validator="consistency",
                    severity=Severity.WARNING,
                    message=f"{self._local_name(cls_iri)} — orphan class (defined but never referenced)",
                    term=cls_iri,
                ))
        return results
