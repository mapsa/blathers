"""Tests for config loading."""

from pathlib import Path

import pytest

from blathers.config import BlathersConfig, load_config


def test_load_valid_config(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert config.metadata.title == "Test Ontology"
    assert config.metadata.version == "0.1.0"
    assert config.metadata.namespace == "http://example.org/test#"
    assert config.metadata.prefix == "ex"


def test_config_ontology_path(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert config.ontology == Path("minimal.ttl")


def test_config_shacl_paths(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert config.shacl == [Path("shapes.ttl")]


def test_config_imports(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert len(config.imports) == 1
    assert config.imports[0].uri == "http://example.org/imported#"
    assert config.imports[0].prefix == "imp"


def test_config_validation_rules(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert config.validation.fail_on == "error"
    assert config.validation.rules.shacl is True
    assert config.validation.rules.overlap is True


def test_config_conneg(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert "htaccess" in config.conneg.generate
    assert config.conneg.base_uri == "http://example.org/test"


def test_missing_config_raises():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/blathers.yaml"))


def test_config_paths_resolved_relative_to_config_dir(fixtures_dir: Path):
    config = load_config(fixtures_dir / "blathers.yaml")
    assert config.resolve_path(config.ontology).exists()
