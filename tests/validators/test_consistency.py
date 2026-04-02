"""Tests for consistency validator."""

from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from blathers.validators.base import Severity
from blathers.validators.consistency import ConsistencyValidator


def _make_graph_with_dangling_range() -> Graph:
    """Graph where a property references a class not defined anywhere."""
    g = Graph()
    EX = Namespace("http://example.org/test#")
    g.bind("ex", EX)
    g.add((EX.MyClass, RDF.type, OWL.Class))
    g.add((EX.MyClass, RDFS.label, Literal("My Class")))
    g.add((EX.MyClass, RDFS.comment, Literal("A class.")))
    g.add((EX.myProp, RDF.type, OWL.ObjectProperty))
    g.add((EX.myProp, RDFS.label, Literal("my prop")))
    g.add((EX.myProp, RDFS.comment, Literal("A prop.")))
    g.add((EX.myProp, RDFS.domain, EX.MyClass))
    g.add((EX.myProp, RDFS.range, EX.NonExistent))  # dangling
    return g


def _make_graph_with_orphan() -> Graph:
    """Graph with a class that is never referenced."""
    g = Graph()
    EX = Namespace("http://example.org/test#")
    g.bind("ex", EX)
    ONT = URIRef("http://example.org/test")
    g.add((ONT, RDF.type, OWL.Ontology))
    g.add((ONT, RDFS.label, Literal("Test")))
    g.add((EX.UsedClass, RDF.type, OWL.Class))
    g.add((EX.UsedClass, RDFS.label, Literal("Used")))
    g.add((EX.UsedClass, RDFS.comment, Literal("Used class.")))
    g.add((EX.OrphanClass, RDF.type, OWL.Class))
    g.add((EX.OrphanClass, RDFS.label, Literal("Orphan")))
    g.add((EX.OrphanClass, RDFS.comment, Literal("Never referenced.")))
    g.add((EX.myProp, RDF.type, OWL.ObjectProperty))
    g.add((EX.myProp, RDFS.label, Literal("my prop")))
    g.add((EX.myProp, RDFS.comment, Literal("A prop.")))
    g.add((EX.myProp, RDFS.domain, EX.UsedClass))
    g.add((EX.myProp, RDFS.range, EX.UsedClass))
    return g


def _make_graph_missing_label() -> Graph:
    """Graph with a class missing rdfs:label."""
    g = Graph()
    EX = Namespace("http://example.org/test#")
    g.bind("ex", EX)
    g.add((EX.NoLabel, RDF.type, OWL.Class))
    return g


def test_dangling_range():
    g = _make_graph_with_dangling_range()
    v = ConsistencyValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    messages = [r.message for r in results]
    assert any("NonExistent" in m for m in messages)


def test_orphan_class():
    g = _make_graph_with_orphan()
    v = ConsistencyValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    messages = [r.message for r in results]
    assert any("OrphanClass" in m and "orphan" in m.lower() for m in messages)


def test_missing_label():
    g = _make_graph_missing_label()
    v = ConsistencyValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    messages = [r.message for r in results]
    assert any("NoLabel" in m and "label" in m.lower() for m in messages)


def test_clean_graph(fixtures_dir: Path):
    g = Graph()
    g.parse(str(fixtures_dir / "minimal.ttl"), format="turtle")
    v = ConsistencyValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    errors = [r for r in results if r.severity == Severity.ERROR]
    assert len(errors) == 0
