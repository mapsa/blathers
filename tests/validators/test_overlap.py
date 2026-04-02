"""Tests for overlap/redundancy validator."""

from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import OWL, RDF, RDFS

from blathers.validators.base import Severity
from blathers.validators.overlap import OverlapValidator


def test_detect_name_shadow(fixtures_dir: Path):
    local_g = Graph()
    local_g.parse(str(fixtures_dir / "minimal.ttl"), format="turtle")

    imported_g = Graph()
    imported_g.parse(str(fixtures_dir / "imported.ttl"), format="turtle")

    v = OverlapValidator(
        local_graph=local_g,
        local_namespace="http://example.org/test#",
        imported_graphs={"http://example.org/imported#": imported_g},
        allowlist=set(),
    )
    results = v.validate()
    messages = [r.message for r in results]
    assert any("MyClass" in m and "shadows" in m.lower() for m in messages)


def test_allowlist_suppresses(fixtures_dir: Path):
    local_g = Graph()
    local_g.parse(str(fixtures_dir / "minimal.ttl"), format="turtle")

    imported_g = Graph()
    imported_g.parse(str(fixtures_dir / "imported.ttl"), format="turtle")

    v = OverlapValidator(
        local_graph=local_g,
        local_namespace="http://example.org/test#",
        imported_graphs={"http://example.org/imported#": imported_g},
        allowlist={"ex:MyClass"},
    )
    results = v.validate()
    messages = [r.message for r in results]
    assert not any("MyClass" in m for m in messages)


def test_no_overlap_when_names_differ(fixtures_dir: Path):
    local_g = Graph()
    EX = Namespace("http://example.org/test#")
    local_g.add((EX.UniqueClass, RDF.type, OWL.Class))
    local_g.add((EX.UniqueClass, RDFS.label, Literal("Unique")))

    imported_g = Graph()
    imported_g.parse(str(fixtures_dir / "imported.ttl"), format="turtle")

    v = OverlapValidator(
        local_graph=local_g,
        local_namespace="http://example.org/test#",
        imported_graphs={"http://example.org/imported#": imported_g},
        allowlist=set(),
    )
    results = v.validate()
    assert len(results) == 0
