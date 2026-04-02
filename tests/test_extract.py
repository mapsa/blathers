"""Tests for RDF/OWL extraction."""

from pathlib import Path

from blathers.extract import OntologyData, extract_ontology


def test_extract_metadata(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    assert data.metadata["title"] == "Test Ontology"
    assert data.metadata["version"] == "0.1.0"


def test_extract_classes(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    iris = [c.iri for c in data.classes]
    assert "http://example.org/test#MyClass" in iris
    assert "http://example.org/test#MySubClass" in iris


def test_extract_class_labels(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    my_class = next(c for c in data.classes if c.local_name == "MyClass")
    assert my_class.label == "My Class"
    assert my_class.comment == "A test class."


def test_extract_class_hierarchy(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    sub = next(c for c in data.classes if c.local_name == "MySubClass")
    assert "http://example.org/test#MyClass" in sub.superclasses


def test_extract_properties(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    props = [p.iri for p in data.properties]
    assert "http://example.org/test#myProperty" in props


def test_extract_property_domain_range(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    prop = next(p for p in data.properties if p.local_name == "myProperty")
    assert prop.domain == "http://example.org/test#MyClass"
    assert prop.range == "http://example.org/test#MySubClass"


def test_extract_shapes(fixtures_dir: Path):
    data = extract_ontology(
        fixtures_dir / "minimal.ttl",
        shacl_paths=[fixtures_dir / "shapes.ttl"],
    )
    assert len(data.shapes) >= 1
    shape = data.shapes[0]
    assert shape.target_class == "http://example.org/test#MyClass"


def test_extract_namespace(fixtures_dir: Path):
    data = extract_ontology(fixtures_dir / "minimal.ttl")
    assert data.namespace == "http://example.org/test#"
