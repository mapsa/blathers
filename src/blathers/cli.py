"""CLI entry points for Blathers."""

import click

from blathers import __version__


@click.group()
@click.version_option(version=__version__, prog_name="blathers")
def main() -> None:
    """Blathers — Ontology documentation & validation."""


@main.command()
def init() -> None:
    """Scaffold a new Blathers project."""
    click.echo("init: not yet implemented")


@main.command()
def validate() -> None:
    """Run all validators."""
    click.echo("validate: not yet implemented")


@main.command()
def build() -> None:
    """Validate, extract, and render static site."""
    click.echo("build: not yet implemented")


@main.command()
def fetch() -> None:
    """Pre-fetch and cache imported ontologies."""
    click.echo("fetch: not yet implemented")
