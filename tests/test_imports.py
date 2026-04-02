"""Tests for import resolution."""

from pathlib import Path

from rdflib import Graph

from blathers.config import ImportConfig
from blathers.imports import ImportResolver, uri_to_cache_filename


def test_resolve_local_path(fixtures_dir: Path, tmp_path: Path):
    imp = ImportConfig(uri="http://example.org/imported#", prefix="imp", path="imported.ttl")
    resolver = ImportResolver(
        imports=[imp],
        project_dir=fixtures_dir,
        cache_dir=tmp_path / ".blathers" / "imports",
    )
    graph = resolver.resolve(imp)
    assert graph is not None
    assert len(graph) > 0


def test_resolve_from_cache(fixtures_dir: Path, tmp_path: Path):
    cache_dir = tmp_path / ".blathers" / "imports"
    cache_dir.mkdir(parents=True)
    cached_file = cache_dir / "http_example.org_imported_.ttl"
    import shutil
    shutil.copy(fixtures_dir / "imported.ttl", cached_file)

    imp = ImportConfig(uri="http://example.org/imported#", prefix="imp")
    resolver = ImportResolver(
        imports=[imp],
        project_dir=tmp_path,
        cache_dir=cache_dir,
    )
    graph = resolver.resolve(imp)
    assert graph is not None
    assert len(graph) > 0


def test_resolve_all(fixtures_dir: Path, tmp_path: Path):
    imp = ImportConfig(uri="http://example.org/imported#", prefix="imp", path="imported.ttl")
    resolver = ImportResolver(
        imports=[imp],
        project_dir=fixtures_dir,
        cache_dir=tmp_path / ".blathers" / "imports",
    )
    graphs = resolver.resolve_all()
    assert "http://example.org/imported#" in graphs
    assert len(graphs["http://example.org/imported#"]) > 0


def test_cache_filename():
    assert uri_to_cache_filename("http://example.org/imported#") == "http_example.org_imported_.ttl"
    assert uri_to_cache_filename("https://w3id.org/dpv#") == "https_w3id.org_dpv_.ttl"
