"""RDF/OWL ontology extraction using rdflib."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

SH = Namespace("http://www.w3.org/ns/shacl#")
VANN = Namespace("http://purl.org/vocab/vann/")


def _local_name(iri: str) -> str:
    """Extract the local name from an IRI (after # or last /)."""
    if "#" in iri:
        return iri.split("#")[-1]
    return iri.rsplit("/", 1)[-1]


def _str_or_none(val) -> str | None:
    return str(val) if val is not None else None


@dataclass
class ExtractedClass:
    iri: str
    local_name: str
    label: str | None = None
    comment: str | None = None
    superclasses: list[str] = field(default_factory=list)
    subclasses: list[str] = field(default_factory=list)
    properties: list[str] = field(default_factory=list)


@dataclass
class ExtractedProperty:
    iri: str
    local_name: str
    label: str | None = None
    comment: str | None = None
    domain: str | None = None
    range: str | None = None
    prop_type: str = "ObjectProperty"


@dataclass
class ShapeConstraint:
    path: str | None = None
    min_count: int | None = None
    max_count: int | None = None
    node_class: str | None = None


@dataclass
class ExtractedShape:
    iri: str
    local_name: str
    target_class: str | None = None
    constraints: list[ShapeConstraint] = field(default_factory=list)


@dataclass
class ExtractedIndividual:
    iri: str
    local_name: str
    label: str | None = None
    comment: str | None = None
    types: list[str] = field(default_factory=list)  # classes this is an instance of


@dataclass
class OntologyData:
    namespace: str
    metadata: dict[str, str]
    classes: list[ExtractedClass]
    properties: list[ExtractedProperty]
    shapes: list[ExtractedShape]
    individuals: list[ExtractedIndividual]
    graph: Graph


def _find_ontology_iri(g: Graph) -> URIRef | None:
    """Find the ontology IRI in the graph."""
    for s in g.subjects(RDF.type, OWL.Ontology):
        return s
    return None


def _extract_metadata(g: Graph, ont_iri: URIRef | None) -> dict[str, str]:
    """Extract ontology-level metadata."""
    meta: dict[str, str] = {}
    if ont_iri is None:
        return meta

    for pred, key in [
        (RDFS.label, "title"),
        (RDFS.comment, "description"),
        (OWL.versionInfo, "version"),
        (DCTERMS.license, "license"),
        (DCTERMS.creator, "creator"),
        (DCTERMS.title, "title"),
        (VANN.preferredNamespacePrefix, "prefix"),
        (VANN.preferredNamespaceUri, "namespace"),
    ]:
        for obj in g.objects(ont_iri, pred):
            val = str(obj)
            if key not in meta or key == "title":
                meta[key] = val
    return meta


def _extract_classes(g: Graph, namespace: str) -> list[ExtractedClass]:
    """Extract all OWL classes in the ontology namespace."""
    classes = []
    for cls_iri in g.subjects(RDF.type, OWL.Class):
        iri_str = str(cls_iri)
        if not iri_str.startswith(namespace):
            continue
        label = _str_or_none(g.value(cls_iri, RDFS.label))
        comment = _str_or_none(g.value(cls_iri, RDFS.comment))
        supers = [str(s) for s in g.objects(cls_iri, RDFS.subClassOf) if isinstance(s, URIRef)]
        classes.append(ExtractedClass(
            iri=iri_str,
            local_name=_local_name(iri_str),
            label=label,
            comment=comment,
            superclasses=supers,
        ))

    # Populate subclasses by inverse lookup
    for cls in classes:
        for other in classes:
            if cls.iri in other.superclasses:
                cls.subclasses.append(other.iri)

    return classes


def _extract_properties(g: Graph, namespace: str) -> list[ExtractedProperty]:
    """Extract all OWL properties in the ontology namespace."""
    props = []
    prop_types = [
        (OWL.ObjectProperty, "ObjectProperty"),
        (OWL.DatatypeProperty, "DatatypeProperty"),
        (OWL.AnnotationProperty, "AnnotationProperty"),
    ]
    seen = set()
    for rdf_type, type_name in prop_types:
        for prop_iri in g.subjects(RDF.type, rdf_type):
            iri_str = str(prop_iri)
            if not iri_str.startswith(namespace) or iri_str in seen:
                continue
            seen.add(iri_str)
            label = _str_or_none(g.value(prop_iri, RDFS.label))
            comment = _str_or_none(g.value(prop_iri, RDFS.comment))
            domain = _str_or_none(g.value(prop_iri, RDFS.domain))
            range_ = _str_or_none(g.value(prop_iri, RDFS.range))
            props.append(ExtractedProperty(
                iri=iri_str,
                local_name=_local_name(iri_str),
                label=label,
                comment=comment,
                domain=domain,
                range=range_,
                prop_type=type_name,
            ))
    return props


def _extract_shapes(g: Graph) -> list[ExtractedShape]:
    """Extract SHACL shapes."""
    shapes = []
    for shape_iri in g.subjects(RDF.type, SH.NodeShape):
        iri_str = str(shape_iri)
        target = _str_or_none(g.value(shape_iri, SH.targetClass))

        constraints = []
        for prop_shape in g.objects(shape_iri, SH.property):
            path = _str_or_none(g.value(prop_shape, SH.path))
            min_c = g.value(prop_shape, SH.minCount)
            max_c = g.value(prop_shape, SH.maxCount)
            cls = _str_or_none(g.value(prop_shape, SH["class"]))
            constraints.append(ShapeConstraint(
                path=path,
                min_count=int(min_c) if min_c is not None else None,
                max_count=int(max_c) if max_c is not None else None,
                node_class=cls,
            ))

        shapes.append(ExtractedShape(
            iri=iri_str,
            local_name=_local_name(iri_str),
            target_class=target,
            constraints=constraints,
        ))
    return shapes


def _extract_individuals(g: Graph, namespace: str) -> list[ExtractedIndividual]:
    """Extract all owl:NamedIndividual subjects in the ontology namespace."""
    individuals = []
    for ind_iri in g.subjects(RDF.type, OWL.NamedIndividual):
        iri_str = str(ind_iri)
        if not iri_str.startswith(namespace):
            continue
        label = _str_or_none(g.value(ind_iri, RDFS.label))
        comment = _str_or_none(g.value(ind_iri, RDFS.comment))
        types = [
            str(t)
            for t in g.objects(ind_iri, RDF.type)
            if isinstance(t, URIRef) and str(t) != str(OWL.NamedIndividual)
        ]
        individuals.append(ExtractedIndividual(
            iri=iri_str,
            local_name=_local_name(iri_str),
            label=label,
            comment=comment,
            types=types,
        ))
    return individuals


def _populate_class_properties(classes: list[ExtractedClass], properties: list[ExtractedProperty]) -> None:
    """Link properties to their domain classes."""
    class_map = {c.iri: c for c in classes}
    for prop in properties:
        if prop.domain and prop.domain in class_map:
            class_map[prop.domain].properties.append(prop.iri)


def _detect_namespace(g: Graph, ont_iri: URIRef | None) -> str:
    """Detect the ontology namespace from VANN annotation or ontology IRI."""
    if ont_iri is not None:
        ns = g.value(ont_iri, VANN.preferredNamespaceUri)
        if ns:
            return str(ns)
        iri_str = str(ont_iri)
        if iri_str.endswith("#") or iri_str.endswith("/"):
            return iri_str
        return iri_str + "#"
    return ""


def extract_ontology(
    ontology_path: Path,
    shacl_paths: list[Path] | None = None,
) -> OntologyData:
    """Parse an OWL ontology and optional SHACL shapes, extracting all terms."""
    g = Graph()
    g.parse(str(ontology_path), format="turtle")

    if shacl_paths:
        for sp in shacl_paths:
            g.parse(str(sp), format="turtle")

    ont_iri = _find_ontology_iri(g)
    namespace = _detect_namespace(g, ont_iri)
    metadata = _extract_metadata(g, ont_iri)
    classes = _extract_classes(g, namespace)
    properties = _extract_properties(g, namespace)
    shapes = _extract_shapes(g)
    individuals = _extract_individuals(g, namespace)
    _populate_class_properties(classes, properties)

    return OntologyData(
        namespace=namespace,
        metadata=metadata,
        classes=classes,
        properties=properties,
        shapes=shapes,
        individuals=individuals,
        graph=g,
    )
