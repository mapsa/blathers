"""CLI entry points for Blathers."""

from __future__ import annotations

import glob as globmod
import sys
from pathlib import Path

import click

from blathers import __version__


@click.group()
@click.version_option(version=__version__, prog_name="blathers")
def main() -> None:
    """Blathers — Ontology documentation & validation."""


@main.command()
@click.option("--dir", "project_dir", default=".", help="Directory to scaffold")
def init(project_dir: str) -> None:
    """Scaffold a new Blathers project."""
    root = Path(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "ontology").mkdir(exist_ok=True)
    (root / "shacl").mkdir(exist_ok=True)
    (root / "examples").mkdir(exist_ok=True)
    (root / "figures").mkdir(exist_ok=True)
    (root / "sidecars").mkdir(exist_ok=True)

    config_path = root / "blathers.yaml"
    if not config_path.exists():
        config_path.write_text(
            "ontology: ontology/my-ontology.ttl\n"
            "shacl:\n"
            "  - shacl/shapes.ttl\n"
            "examples:\n"
            "  - examples/*.ttl\n"
            "sidecars: sidecars/\n"
            "figures: figures/\n"
            "output: dist/\n"
            "\n"
            "metadata:\n"
            '  title: "My Ontology"\n'
            '  version: "0.1.0"\n'
            "  license: MIT\n"
            '  namespace: "http://example.org/my-ontology#"\n'
            "  prefix: myont\n"
            "\n"
            "validation:\n"
            "  fail_on: error\n"
            "  rules:\n"
            "    shacl: true\n"
            "    consistency: true\n"
            "    completeness: true\n"
            "    conventions: true\n"
            "    overlap: true\n"
        )

    # Create a starter sidecar
    index_sidecar = root / "sidecars" / "_index.md"
    if not index_sidecar.exists():
        index_sidecar.write_text(
            "---\n"
            "section: introduction\n"
            "order: 1\n"
            "---\n"
            "\n"
            "# My Ontology\n"
            "\n"
            "Welcome to the documentation.\n"
        )

    click.echo(f"Scaffolded Blathers project at {root}")


@main.command()
@click.option("--config", "config_path", default="blathers.yaml", help="Path to blathers.yaml")
def validate(config_path: str) -> None:
    """Run all validators."""
    from blathers.config import load_config
    from blathers.extract import extract_ontology
    from blathers.imports import ImportResolver
    from blathers.sidecars import load_sidecars
    from blathers.validators.base import Severity

    config = load_config(Path(config_path))

    # Extract ontology
    shacl_paths = [config.resolve_path(p) for p in config.shacl]
    data = extract_ontology(config.resolve_path(config.ontology), shacl_paths=shacl_paths)
    sidecars = load_sidecars(config.resolve_path(config.sidecars))

    all_results = []

    # SHACL
    if config.validation.rules.shacl:
        from blathers.validators.shacl import ShaclValidator

        example_paths = []
        for pattern in config.examples:
            example_paths.extend(
                Path(p) for p in globmod.glob(str(config.resolve_path(Path(pattern))))
            )
        v = ShaclValidator(
            ontology_path=config.resolve_path(config.ontology),
            shacl_paths=shacl_paths,
            example_paths=example_paths,
        )
        results = v.validate()
        _print_validator_results("SHACL", results)
        all_results.extend(results)

    # Consistency
    if config.validation.rules.consistency:
        from blathers.validators.consistency import ConsistencyValidator

        v = ConsistencyValidator(data.graph, namespace=data.namespace)
        results = v.validate()
        _print_validator_results("Consistency", results)
        all_results.extend(results)

    # Completeness
    if config.validation.rules.completeness:
        from blathers.validators.completeness import CompletenessValidator

        class_iris = {c.iri for c in data.classes}
        prop_iris = {p.iri for p in data.properties}
        v = CompletenessValidator(
            class_iris=class_iris,
            property_iris=prop_iris,
            sidecars=sidecars,
            namespace=data.namespace,
            prefix=config.metadata.prefix,
        )
        results = v.validate()
        _print_validator_results("Completeness", results)
        all_results.extend(results)

    # Conventions
    if config.validation.rules.conventions:
        from blathers.validators.conventions import ConventionValidator

        v = ConventionValidator(data.graph, namespace=data.namespace)
        results = v.validate()
        _print_validator_results("Conventions", results)
        all_results.extend(results)

    # Overlap
    if config.validation.rules.overlap:
        from blathers.validators.overlap import OverlapValidator

        resolver = ImportResolver(
            imports=config.imports,
            project_dir=config._config_dir,
            cache_dir=config._config_dir / ".blathers" / "imports",
        )
        imported_graphs = resolver.resolve_all()
        allowlist = set()
        if config.validation.overlap and isinstance(config.validation.overlap, dict):
            allowlist = set(config.validation.overlap.get("allow", []))
        v = OverlapValidator(
            local_graph=data.graph,
            local_namespace=data.namespace,
            imported_graphs=imported_graphs,
            allowlist=allowlist,
        )
        results = v.validate()
        _print_validator_results("Overlap", results)
        all_results.extend(results)

    # Summary
    errors = sum(1 for r in all_results if r.severity == Severity.ERROR)
    warnings = sum(1 for r in all_results if r.severity == Severity.WARNING)
    click.echo(f"\n  {errors} errors, {warnings} warnings")

    if errors > 0 and config.validation.fail_on == "error":
        sys.exit(1)
    if warnings > 0 and config.validation.fail_on == "warning":
        sys.exit(1)


@main.command()
@click.option("--config", "config_path", default="blathers.yaml", help="Path to blathers.yaml")
@click.option("--output", "output_dir", default=None, help="Override output directory")
def build(config_path: str, output_dir: str | None) -> None:
    """Validate, extract, and render static site."""
    from blathers.config import load_config
    from blathers.conneg import generate_conneg
    from blathers.extract import extract_ontology
    from blathers.imports import ImportResolver
    from blathers.manifest import build_manifest
    from blathers.renderer import render_site
    from blathers.serialize import serialize_ontology
    from blathers.sidecars import load_sidecars
    from blathers.validators.base import Severity

    config = load_config(Path(config_path))
    out = Path(output_dir) if output_dir else config.resolve_path(config.output)

    # Extract
    shacl_paths = [config.resolve_path(p) for p in config.shacl]
    data = extract_ontology(config.resolve_path(config.ontology), shacl_paths=shacl_paths)
    sidecars = load_sidecars(config.resolve_path(config.sidecars))

    # Build manifest
    manifest = build_manifest(config, data, sidecars, [])

    # Render HTML
    render_site(manifest, out)
    click.echo(f"  HTML site rendered to {out}")

    # Serialize
    formats = config.conneg.formats if config.conneg.formats else ["ttl"]
    serialize_ontology(config.resolve_path(config.ontology), out, formats)
    click.echo(f"  Serializations: {', '.join(formats)}")

    # Content negotiation
    if config.conneg.generate:
        generate_conneg(out, config.conneg.generate, config.conneg.base_uri, formats)
        click.echo(f"  Content negotiation: {', '.join(config.conneg.generate)}")

    # Versioned copy
    version = config.metadata.version
    version_dir = out / version
    if not version_dir.exists():
        import shutil
        shutil.copytree(out, version_dir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(version))
        click.echo(f"  Versioned snapshot: {version_dir}")

    click.echo(f"\n  Build complete.")


@main.command()
@click.option("--config", "config_path", default="blathers.yaml", help="Path to blathers.yaml")
def fetch(config_path: str) -> None:
    """Pre-fetch and cache imported ontologies."""
    from blathers.config import load_config
    from blathers.imports import ImportResolver

    config = load_config(Path(config_path))
    resolver = ImportResolver(
        imports=config.imports,
        project_dir=config._config_dir,
        cache_dir=config._config_dir / ".blathers" / "imports",
    )

    for imp in config.imports:
        ok = resolver.fetch_and_cache(imp)
        if ok:
            click.echo(f"  Cached: {imp.uri}")
        else:
            click.echo(f"  FAILED: {imp.uri}", err=True)


def _print_validator_results(name: str, results: list) -> None:
    from blathers.validators.base import Severity

    if not results:
        click.echo(f"  {name:15s} OK")
        return

    click.echo(f"  {name}")
    for r in results:
        severity = r.severity.value.upper()
        click.echo(f"    {severity:8s} {r.message}")
