"""Tests for convention validator."""

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import OWL, RDF, RDFS

from blathers.validators.base import Severity
from blathers.validators.conventions import ConventionValidator


def _make_graph_bad_naming() -> Graph:
    """Class with camelCase name (should be PascalCase)."""
    g = Graph()
    EX = Namespace("http://example.org/test#")
    g.add((EX.myClass, RDF.type, OWL.Class))  # camelCase — wrong
    g.add((EX.myClass, RDFS.label, Literal("my class")))
    g.add((EX.MyProp, RDF.type, OWL.ObjectProperty))  # PascalCase — wrong
    g.add((EX.MyProp, RDFS.label, Literal("My Prop")))
    return g


def _make_graph_missing_metadata() -> Graph:
    """Ontology missing required metadata."""
    g = Graph()
    ONT = Namespace("http://example.org/test")
    g.add((ONT[""], RDF.type, OWL.Ontology))
    return g


def test_naming_conventions():
    g = _make_graph_bad_naming()
    v = ConventionValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    messages = [r.message for r in results]
    assert any("myClass" in m and "PascalCase" in m for m in messages)
    assert any("MyProp" in m and "camelCase" in m for m in messages)


def test_missing_ontology_metadata():
    g = _make_graph_missing_metadata()
    v = ConventionValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    messages = [r.message.lower() for r in results]
    assert any("version" in m for m in messages)


def test_clean_graph_passes(fixtures_dir):
    from pathlib import Path
    g = Graph()
    g.parse(str(fixtures_dir / "minimal.ttl"), format="turtle")
    v = ConventionValidator(g, namespace="http://example.org/test#")
    results = v.validate()
    errors = [r for r in results if r.severity == Severity.ERROR]
    assert len(errors) == 0
