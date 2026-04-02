"""Tests for ontology serialization."""

from pathlib import Path

from blathers.serialize import serialize_ontology


def test_serialize_jsonld(fixtures_dir: Path, tmp_path: Path):
    serialize_ontology(fixtures_dir / "minimal.ttl", tmp_path, ["jsonld"])
    jsonld = tmp_path / "ontology.jsonld"
    assert jsonld.exists()
    content = jsonld.read_text()
    assert "@context" in content or "@graph" in content


def test_serialize_nt(fixtures_dir: Path, tmp_path: Path):
    serialize_ontology(fixtures_dir / "minimal.ttl", tmp_path, ["nt"])
    nt = tmp_path / "ontology.nt"
    assert nt.exists()
    assert len(nt.read_text().strip()) > 0


def test_serialize_ttl_copies_source(fixtures_dir: Path, tmp_path: Path):
    serialize_ontology(fixtures_dir / "minimal.ttl", tmp_path, ["ttl"])
    ttl = tmp_path / "ontology.ttl"
    assert ttl.exists()
    assert "owl:Ontology" in ttl.read_text()


def test_serialize_multiple_formats(fixtures_dir: Path, tmp_path: Path):
    serialize_ontology(fixtures_dir / "minimal.ttl", tmp_path, ["ttl", "jsonld", "nt"])
    assert (tmp_path / "ontology.ttl").exists()
    assert (tmp_path / "ontology.jsonld").exists()
    assert (tmp_path / "ontology.nt").exists()
