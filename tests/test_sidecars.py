"""Tests for sidecar parsing."""

from pathlib import Path

from blathers.sidecars import Sidecar, load_sidecars


def test_load_sidecars(fixtures_dir: Path):
    sidecars = load_sidecars(fixtures_dir / "sidecars")
    assert len(sidecars) == 2


def test_term_sidecar(fixtures_dir: Path):
    sidecars = load_sidecars(fixtures_dir / "sidecars")
    by_name = {s.filename: s for s in sidecars}
    my_class = by_name["MyClass.md"]
    assert my_class.term == "ex:MyClass"
    assert my_class.section == "overview"
    assert my_class.order == 1
    assert "fundamental concept" in my_class.body


def test_narrative_sidecar(fixtures_dir: Path):
    sidecars = load_sidecars(fixtures_dir / "sidecars")
    by_name = {s.filename: s for s in sidecars}
    index = by_name["_index.md"]
    assert index.term is None
    assert index.section == "introduction"
    assert index.is_narrative is True


def test_sidecar_html_rendering(fixtures_dir: Path):
    sidecars = load_sidecars(fixtures_dir / "sidecars")
    by_name = {s.filename: s for s in sidecars}
    index = by_name["_index.md"]
    assert "<h1>" in index.html or "<h1" in index.html


def test_empty_dir_returns_empty(tmp_path: Path):
    sidecars = load_sidecars(tmp_path)
    assert sidecars == []


def test_missing_dir_returns_empty(tmp_path: Path):
    sidecars = load_sidecars(tmp_path / "nonexistent")
    assert sidecars == []
