"""Tests for JSON manifest generation."""

import json
from pathlib import Path

from blathers.config import load_config
from blathers.extract import extract_ontology
from blathers.manifest import build_manifest
from blathers.sidecars import load_sidecars
from blathers.validators.base import ValidationResult, Severity


def test_manifest_has_metadata(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(
        config.resolve_path(config.ontology),
        shacl_paths=[config.resolve_path(p) for p in config.shacl],
    )
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    manifest = build_manifest(config, data, sidecars, [])
    assert manifest["metadata"]["title"] == "Test Ontology"
    assert manifest["metadata"]["version"] == "0.1.0"
    assert manifest["metadata"]["namespace"] == "http://example.org/test#"


def test_manifest_has_classes(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(
        config.resolve_path(config.ontology),
        shacl_paths=[config.resolve_path(p) for p in config.shacl],
    )
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    manifest = build_manifest(config, data, sidecars, [])
    class_names = [c["local_name"] for c in manifest["classes"]]
    assert "MyClass" in class_names
    assert "MySubClass" in class_names


def test_manifest_class_has_sidecar_html(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(
        config.resolve_path(config.ontology),
        shacl_paths=[config.resolve_path(p) for p in config.shacl],
    )
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    manifest = build_manifest(config, data, sidecars, [])
    my_class = next(c for c in manifest["classes"] if c["local_name"] == "MyClass")
    assert my_class["sidecar"] is not None
    assert "fundamental concept" in my_class["sidecar"]


def test_manifest_has_properties(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(config.resolve_path(config.ontology))
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    manifest = build_manifest(config, data, sidecars, [])
    prop_names = [p["local_name"] for p in manifest["properties"]]
    assert "myProperty" in prop_names


def test_manifest_has_validation_summary(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(config.resolve_path(config.ontology))
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    val_results = [
        ValidationResult(validator="test", severity=Severity.ERROR, message="err"),
        ValidationResult(validator="test", severity=Severity.WARNING, message="warn"),
    ]
    manifest = build_manifest(config, data, sidecars, val_results)
    assert manifest["validation_summary"]["errors"] == 1
    assert manifest["validation_summary"]["warnings"] == 1


def test_manifest_is_json_serializable(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(config.resolve_path(config.ontology))
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    manifest = build_manifest(config, data, sidecars, [])
    json.dumps(manifest)
