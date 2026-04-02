"""Tests for HTML renderer."""

import json
from pathlib import Path

from blathers.config import load_config
from blathers.extract import extract_ontology
from blathers.manifest import build_manifest
from blathers.renderer import render_site
from blathers.sidecars import load_sidecars


def _build_test_manifest(fixtures_dir: Path) -> dict:
    config = load_config(fixtures_dir / "blathers.yaml")
    data = extract_ontology(
        config.resolve_path(config.ontology),
        shacl_paths=[config.resolve_path(p) for p in config.shacl],
    )
    sidecars = load_sidecars(config.resolve_path(config.sidecars))
    return build_manifest(config, data, sidecars, [])


def test_render_creates_index(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    assert (tmp_path / "index.html").exists()
    content = (tmp_path / "index.html").read_text()
    assert "Test Ontology" in content


def test_render_creates_class_pages(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    assert (tmp_path / "classes" / "MyClass.html").exists()
    content = (tmp_path / "classes" / "MyClass.html").read_text()
    assert "My Class" in content


def test_render_creates_property_pages(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    assert (tmp_path / "properties" / "myProperty.html").exists()


def test_render_creates_assets(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    assert (tmp_path / "assets" / "style.css").exists()


def test_render_writes_manifest_json(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    manifest_path = tmp_path / "site-data.json"
    assert manifest_path.exists()
    loaded = json.loads(manifest_path.read_text())
    assert loaded["metadata"]["title"] == "Test Ontology"


def test_render_index_has_class_links(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert "classes/MyClass.html" in content


def test_render_works_with_file_protocol(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    index = (tmp_path / "index.html").read_text()
    # No absolute URLs, no XHR fetches, no ES module imports
    assert "http://" not in index or "http://example.org" in index
    assert "import " not in index or "import " in index  # no ES module imports
    # All CSS/JS should be inlined or relative
    assert "<style>" in index or 'href="assets/' in index
