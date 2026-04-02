"""Tests for completeness validator."""

from blathers.sidecars import Sidecar
from blathers.validators.base import Severity
from blathers.validators.completeness import CompletenessValidator


def _make_sidecar(term: str | None = None, filename: str = "test.md") -> Sidecar:
    from pathlib import Path
    return Sidecar(
        filename=filename,
        path=Path(filename),
        term=term,
        section=None,
        order=0,
        body="",
        html="",
        is_narrative=term is None,
    )


def test_undocumented_class():
    class_iris = {"http://example.org/test#MyClass", "http://example.org/test#OtherClass"}
    property_iris: set[str] = set()
    sidecars = [_make_sidecar("ex:MyClass", "MyClass.md")]

    v = CompletenessValidator(
        class_iris=class_iris,
        property_iris=property_iris,
        sidecars=sidecars,
        namespace="http://example.org/test#",
        prefix="ex",
    )
    results = v.validate()
    messages = [r.message for r in results]
    assert any("OtherClass" in m and "no sidecar" in m.lower() for m in messages)


def test_sidecar_references_nonexistent_term():
    class_iris = {"http://example.org/test#MyClass"}
    property_iris: set[str] = set()
    sidecars = [
        _make_sidecar("ex:MyClass", "MyClass.md"),
        _make_sidecar("ex:Ghost", "Ghost.md"),
    ]

    v = CompletenessValidator(
        class_iris=class_iris,
        property_iris=property_iris,
        sidecars=sidecars,
        namespace="http://example.org/test#",
        prefix="ex",
    )
    results = v.validate()
    messages = [r.message for r in results]
    assert any("Ghost" in m and "not found" in m.lower() for m in messages)


def test_complete_coverage():
    class_iris = {"http://example.org/test#MyClass"}
    property_iris: set[str] = set()
    sidecars = [_make_sidecar("ex:MyClass", "MyClass.md")]

    v = CompletenessValidator(
        class_iris=class_iris,
        property_iris=property_iris,
        sidecars=sidecars,
        namespace="http://example.org/test#",
        prefix="ex",
    )
    results = v.validate()
    assert len(results) == 0
