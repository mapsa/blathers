"""SHACL validator — runs pyshacl against example instances."""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

from blathers.validators.base import Severity, ValidationResult


class ShaclValidator:
    """Validates example instances against SHACL shapes."""

    def __init__(
        self,
        ontology_path: Path,
        shacl_paths: list[Path],
        example_paths: list[Path],
        import_graphs: list[Graph] | None = None,
    ) -> None:
        self.ontology_path = ontology_path
        self.shacl_paths = shacl_paths
        self.example_paths = example_paths
        self.import_graphs = import_graphs or []

    def validate(self) -> list[ValidationResult]:
        if not self.example_paths:
            return []

        # Build the shapes graph (ontology + SHACL)
        shapes_graph = Graph()
        shapes_graph.parse(str(self.ontology_path), format="turtle")
        for sp in self.shacl_paths:
            shapes_graph.parse(str(sp), format="turtle")

        # Build the ontology graph from resolved imports so pyshacl
        # can resolve class hierarchies (e.g. sh:class dpv:Sector)
        ont_graph = Graph()
        for g in self.import_graphs:
            ont_graph += g

        results: list[ValidationResult] = []

        for example_path in self.example_paths:
            data_graph = Graph()
            data_graph.parse(str(example_path), format="turtle")
            results.extend(
                self._validate_one(data_graph, shapes_graph, ont_graph)
            )

        return results

    def _validate_one(
        self,
        data_graph: Graph,
        shapes_graph: Graph,
        ont_graph: Graph | None = None,
    ) -> list[ValidationResult]:
        from pyshacl import validate as shacl_validate

        kwargs: dict = dict(
            shacl_graph=shapes_graph,
            inference="none",
            abort_on_first=False,
        )
        if ont_graph and len(ont_graph) > 0:
            kwargs["ont_graph"] = ont_graph

        conforms, results_graph, results_text = shacl_validate(
            data_graph,
            **kwargs,
        )

        if conforms:
            return []

        results: list[ValidationResult] = []

        # Use the results graph for structured extraction
        from rdflib.namespace import SH
        SH_NS = SH

        for result_node in results_graph.subjects(
            predicate=None, object=SH_NS.ValidationResult
        ):
            message_val = results_graph.value(result_node, SH_NS.resultMessage)
            focus = results_graph.value(result_node, SH_NS.focusNode)
            severity_uri = results_graph.value(result_node, SH_NS.resultSeverity)

            severity = Severity.ERROR
            if severity_uri and "Warning" in str(severity_uri):
                severity = Severity.WARNING

            msg = str(message_val) if message_val else "SHACL violation"
            if focus:
                msg = f"{focus} — {msg}"

            results.append(ValidationResult(
                validator="shacl",
                severity=severity,
                message=msg,
                term=str(focus) if focus else None,
            ))

        # Fallback: if no structured results but validation failed, use text
        if not results and not conforms:
            results.append(ValidationResult(
                validator="shacl",
                severity=Severity.ERROR,
                message=results_text.strip()[:200],
            ))

        return results
