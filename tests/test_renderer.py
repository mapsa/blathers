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
    # Index now has anchor-based links AND standalone page links
    assert 'href="#MyClass"' in content or "classes/MyClass.html" in content


def test_render_works_with_file_protocol(fixtures_dir: Path, tmp_path: Path):
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    index = (tmp_path / "index.html").read_text()
    # No absolute URLs except the ontology namespace
    assert "http://" not in index or "http://example.org" in index
    # CSS should be inlined
    assert "<style>" in index


def test_render_index_has_term_definition_tables(fixtures_dir: Path, tmp_path: Path):
    """Index page should contain ReSpec-style term definition tables."""
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert 'class="term-def"' in content
    assert 'class="term-contents"' in content
    # Should have prefixed names
    assert "ex:MyClass" in content
    assert "ex:myProperty" in content


def test_render_index_has_hierarchy_tree(fixtures_dir: Path, tmp_path: Path):
    """Index page should contain a collapsible concept hierarchy."""
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert 'id="concept-hierarchy"' in content
    assert 'class="concept-list"' in content
    assert "expand-all" in content
    assert "collapse-all" in content


def test_render_index_has_metadata_header(fixtures_dir: Path, tmp_path: Path):
    """Index page should contain a ReSpec-style metadata header."""
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert 'class="respec-header"' in content
    assert 'class="metadata-dl"' in content
    assert "http://example.org/test#" in content
    assert "0.1.0" in content


def test_render_index_has_toc(fixtures_dir: Path, tmp_path: Path):
    """Index page should contain a sidebar table of contents."""
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert 'class="sidebar"' in content
    assert "Table of Contents" in content
    assert 'href="#classes"' in content
    assert 'href="#properties"' in content


def test_render_index_has_shapes_section(fixtures_dir: Path, tmp_path: Path):
    """Index page should contain SHACL shapes with constraint tables."""
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert 'id="shapes"' in content
    assert 'class="shape-constraints"' in content


def test_render_index_has_two_column_layout(fixtures_dir: Path, tmp_path: Path):
    """Index page should use the two-column page-wrapper layout."""
    manifest = _build_test_manifest(fixtures_dir)
    render_site(manifest, tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert 'class="page-wrapper"' in content
    assert 'class="sidebar"' in content
    assert 'class="content"' in content


def test_manifest_has_prefixed_names(fixtures_dir: Path):
    """Manifest entries should include prefixed_name."""
    manifest = _build_test_manifest(fixtures_dir)
    for cls in manifest["classes"]:
        assert "prefixed_name" in cls
        assert cls["prefixed_name"].startswith("ex:")
    for prop in manifest["properties"]:
        assert "prefixed_name" in prop
        assert prop["prefixed_name"].startswith("ex:")


def test_manifest_has_subject_object_of(fixtures_dir: Path):
    """Class entries should include subject_of and object_of lists."""
    manifest = _build_test_manifest(fixtures_dir)
    # MyClass has myProperty as domain -> subject_of
    my_class = next(c for c in manifest["classes"] if c["local_name"] == "MyClass")
    assert "subject_of" in my_class
    assert any("myProperty" in p for p in my_class["subject_of"])
    # MySubClass has myProperty as range -> object_of
    my_sub = next(c for c in manifest["classes"] if c["local_name"] == "MySubClass")
    assert "object_of" in my_sub
    assert any("myProperty" in p for p in my_sub["object_of"])
