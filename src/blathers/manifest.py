"""JSON manifest generation — the contract between extraction and rendering."""

from __future__ import annotations

from blathers.config import BlathersConfig
from blathers.extract import OntologyData
from blathers.sidecars import Sidecar
from blathers.validators.base import Severity, ValidationResult


def _prefixed_name(iri: str, prefix: str, namespace: str) -> str:
    """Return prefix:LocalName for an IRI."""
    if iri.startswith(namespace):
        return f"{prefix}:{iri[len(namespace):]}"
    known = {
        "http://www.w3.org/2002/07/owl#": "owl",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
        "http://www.w3.org/2001/XMLSchema#": "xsd",
        "http://www.w3.org/ns/shacl#": "sh",
    }
    for ns, pfx in known.items():
        if iri.startswith(ns):
            return f"{pfx}:{iri[len(ns):]}"
    return iri


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

    # First pass: build property list and compute subject_of / object_of maps
    properties = []
    subject_of_map: dict[str, list[str]] = {}  # class IRI -> list of property IRIs
    object_of_map: dict[str, list[str]] = {}   # class IRI -> list of property IRIs

    for prop in data.properties:
        sc = _match_sidecar(prop.iri, prefix, namespace, sidecars)
        properties.append({
            "iri": prop.iri,
            "local_name": prop.local_name,
            "prefixed_name": _prefixed_name(prop.iri, prefix, namespace),
            "label": prop.label,
            "comment": prop.comment,
            "domain": prop.domain,
            "range": prop.range,
            "prop_type": prop.prop_type,
            "sidecar": sc.html if sc else None,
        })
        if prop.domain:
            subject_of_map.setdefault(prop.domain, []).append(prop.iri)
        if prop.range:
            object_of_map.setdefault(prop.range, []).append(prop.iri)

    classes = []
    for cls in data.classes:
        sc = _match_sidecar(cls.iri, prefix, namespace, sidecars)
        classes.append({
            "iri": cls.iri,
            "local_name": cls.local_name,
            "prefixed_name": _prefixed_name(cls.iri, prefix, namespace),
            "label": cls.label,
            "comment": cls.comment,
            "superclasses": cls.superclasses,
            "subclasses": cls.subclasses,
            "properties": cls.properties,
            "subject_of": subject_of_map.get(cls.iri, []),
            "object_of": object_of_map.get(cls.iri, []),
            "sidecar": sc.html if sc else None,
        })

    shapes = []
    for shape in data.shapes:
        shapes.append({
            "iri": shape.iri,
            "local_name": shape.local_name,
            "prefixed_name": _prefixed_name(shape.iri, prefix, namespace),
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
            "description": config.metadata.description,
            "status": config.metadata.status,
            "date": config.metadata.date,
            "editors": [
                {"name": e.name, "affiliation": e.affiliation, "url": e.url, "orcid": e.orcid}
                for e in config.metadata.editors
            ],
            "authors": [
                {"name": a.name, "affiliation": a.affiliation, "url": a.url, "orcid": a.orcid}
                for a in config.metadata.authors
            ],
            "contributors": list(config.metadata.contributors),
            "repository": config.metadata.repository,
            "previous_version": config.metadata.previous_version,
            "copyright": config.metadata.copyright,
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
