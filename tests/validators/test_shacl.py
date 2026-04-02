"""Tests for SHACL validator."""

from pathlib import Path

from blathers.validators.base import Severity
from blathers.validators.shacl import ShaclValidator


def test_shacl_valid_instance(fixtures_dir: Path):
    v = ShaclValidator(
        ontology_path=fixtures_dir / "minimal.ttl",
        shacl_paths=[fixtures_dir / "shapes.ttl"],
        example_paths=[fixtures_dir / "instance.ttl"],
    )
    results = v.validate()
    errors = [r for r in results if r.severity == Severity.ERROR]
    assert len(errors) == 0


def test_shacl_invalid_instance(fixtures_dir: Path):
    v = ShaclValidator(
        ontology_path=fixtures_dir / "minimal.ttl",
        shacl_paths=[fixtures_dir / "shapes.ttl"],
        example_paths=[fixtures_dir / "bad-instance.ttl"],
    )
    results = v.validate()
    errors = [r for r in results if r.severity == Severity.ERROR]
    assert len(errors) > 0


def test_shacl_result_has_message(fixtures_dir: Path):
    v = ShaclValidator(
        ontology_path=fixtures_dir / "minimal.ttl",
        shacl_paths=[fixtures_dir / "shapes.ttl"],
        example_paths=[fixtures_dir / "bad-instance.ttl"],
    )
    results = v.validate()
    assert all(r.message for r in results)
    assert all(r.validator == "shacl" for r in results)


def test_shacl_no_examples_returns_empty(fixtures_dir: Path):
    v = ShaclValidator(
        ontology_path=fixtures_dir / "minimal.ttl",
        shacl_paths=[fixtures_dir / "shapes.ttl"],
        example_paths=[],
    )
    results = v.validate()
    assert results == []
