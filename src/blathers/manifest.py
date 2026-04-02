"""JSON manifest generation — the contract between extraction and rendering."""

from __future__ import annotations

from blathers.config import BlathersConfig
from blathers.extract import OntologyData
from blathers.sidecars import Sidecar
from blathers.validators.base import Severity, ValidationResult


def _match_sidecar(term_iri: str, prefix: str, namespace: str, sidecars: list[Sidecar]) -> Sidecar | None:
    local_name = term_iri.split("#")[-1] if "#" in term_iri else term_iri.rsplit("/", 1)[-1]
    prefixed = f"{prefix}:{local_name}"
    for sc in sidecars:
        if sc.term == prefixed:
            return sc
        if sc.term == term_iri:
            return sc
        if not sc.is_narrative and sc.filename.replace(".md", "") == local_name:
            return sc
    return None


def build_manifest(
    config: BlathersConfig,
    data: OntologyData,
    sidecars: list[Sidecar],
    validation_results: list[ValidationResult],
) -> dict:
    prefix = config.metadata.prefix
    namespace = config.metadata.namespace

    classes = []
    for cls in data.classes:
        sc = _match_sidecar(cls.iri, prefix, namespace, sidecars)
        classes.append({
            "iri": cls.iri,
            "local_name": cls.local_name,
            "label": cls.label,
            "comment": cls.comment,
            "superclasses": cls.superclasses,
            "subclasses": cls.subclasses,
            "properties": cls.properties,
            "sidecar": sc.html if sc else None,
        })

    properties = []
    for prop in data.properties:
        sc = _match_sidecar(prop.iri, prefix, namespace, sidecars)
        properties.append({
            "iri": prop.iri,
            "local_name": prop.local_name,
            "label": prop.label,
            "comment": prop.comment,
            "domain": prop.domain,
            "range": prop.range,
            "prop_type": prop.prop_type,
            "sidecar": sc.html if sc else None,
        })

    shapes = []
    for shape in data.shapes:
        shapes.append({
            "iri": shape.iri,
            "local_name": shape.local_name,
            "target_class": shape.target_class,
            "constraints": [
                {"path": c.path, "min_count": c.min_count, "max_count": c.max_count, "node_class": c.node_class}
                for c in shape.constraints
            ],
        })

    sections = []
    for sc in sidecars:
        if sc.is_narrative:
            sections.append({
                "filename": sc.filename,
                "section": sc.section,
                "order": sc.order,
                "html": sc.html,
            })

    error_count = sum(1 for r in validation_results if r.severity == Severity.ERROR)
    warning_count = sum(1 for r in validation_results if r.severity == Severity.WARNING)

    return {
        "metadata": {
            "title": config.metadata.title,
            "version": config.metadata.version,
            "license": config.metadata.license,
            "namespace": config.metadata.namespace,
            "prefix": config.metadata.prefix,
        },
        "classes": classes,
        "properties": properties,
        "shapes": shapes,
        "sections": sections,
        "conneg": {
            "formats": config.conneg.formats,
            "base_uri": config.conneg.base_uri,
        },
        "validation_summary": {
            "errors": error_count,
            "warnings": warning_count,
        },
    }
