"""Tests for SVG diagram link injection."""

from pathlib import Path

from blathers.diagrams import inject_links, collect_diagrams


SVG_WITH_IDS = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
  <rect id="MyClass" x="10" y="10" width="100" height="50" fill="#eee"/>
  <text id="MySubClass" x="200" y="35">SubClass</text>
  <rect id="unrelated" x="10" y="100" width="100" height="50"/>
</svg>
"""


def test_inject_links_wraps_matching_ids():
    term_names = {"MyClass", "MySubClass"}
    result = inject_links(SVG_WITH_IDS, term_names, base_path="classes")
    assert 'href="classes/MyClass.html"' in result
    assert 'href="classes/MySubClass.html"' in result
    assert 'href="classes/unrelated.html"' not in result


def test_inject_links_adds_cursor_style():
    term_names = {"MyClass"}
    result = inject_links(SVG_WITH_IDS, term_names, base_path="classes")
    assert "cursor:pointer" in result or "cursor: pointer" in result


def test_inject_links_no_matches():
    result = inject_links(SVG_WITH_IDS, set(), base_path="classes")
    assert "<a " not in result


def test_collect_diagrams_from_dir(tmp_path: Path):
    (tmp_path / "fig1.svg").write_text(SVG_WITH_IDS)
    (tmp_path / "fig2.png").write_bytes(b"PNG_DATA")
    (tmp_path / "readme.txt").write_text("ignore me")
    diagrams = collect_diagrams(tmp_path)
    names = [d.name for d in diagrams]
    assert "fig1.svg" in names
    assert "fig2.png" in names
    assert "readme.txt" not in names


def test_collect_diagrams_missing_dir(tmp_path: Path):
    diagrams = collect_diagrams(tmp_path / "nonexistent")
    assert diagrams == []
