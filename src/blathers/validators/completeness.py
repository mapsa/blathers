"""Completeness validator — checks sidecar coverage of ontology terms."""

from __future__ import annotations

from blathers.sidecars import Sidecar
from blathers.validators.base import Severity, ValidationResult


class CompletenessValidator:
    """Checks that all terms have sidecars and all sidecars reference real terms."""

    def __init__(
        self,
        class_iris: set[str],
        property_iris: set[str],
        sidecars: list[Sidecar],
        namespace: str,
        prefix: str,
    ) -> None:
        self.class_iris = class_iris
        self.property_iris = property_iris
        self.sidecars = sidecars
        self.namespace = namespace
        self.prefix = prefix

    def _expand_prefixed(self, term: str) -> str:
        if ":" in term and not term.startswith("http"):
            prefix, local = term.split(":", 1)
            if prefix == self.prefix:
                return self.namespace + local
        return term

    def _local_name(self, iri: str) -> str:
        if "#" in iri:
            return iri.split("#")[-1]
        return iri.rsplit("/", 1)[-1]

    def validate(self) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        all_iris = self.class_iris | self.property_iris

        documented_iris = set()
        for sc in self.sidecars:
            if sc.term:
                documented_iris.add(self._expand_prefixed(sc.term))

        for iri in all_iris:
            if iri not in documented_iris:
                results.append(ValidationResult(
                    validator="completeness",
                    severity=Severity.WARNING,
                    message=f"{self._local_name(iri)} — no sidecar documentation",
                    term=iri,
                ))

        for sc in self.sidecars:
            if sc.term:
                expanded = self._expand_prefixed(sc.term)
                if expanded not in all_iris:
                    results.append(ValidationResult(
                        validator="completeness",
                        severity=Severity.WARNING,
                        message=f"{sc.term} — sidecar references term not found in ontology",
                        term=expanded,
                    ))

        return results
