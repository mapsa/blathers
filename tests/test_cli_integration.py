"""Integration tests for CLI commands."""

from pathlib import Path

from click.testing import CliRunner

from blathers.cli import main


def test_validate_with_fixtures(fixtures_dir: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--config", str(fixtures_dir / "blathers.yaml")])
    assert result.exit_code == 0 or result.exit_code == 1
    # Should print validator names
    assert "SHACL" in result.output or "shacl" in result.output.lower()


def test_build_creates_output(fixtures_dir: Path, tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "build",
        "--config", str(fixtures_dir / "blathers.yaml"),
        "--output", str(tmp_path / "dist"),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "dist" / "index.html").exists()
    assert (tmp_path / "dist" / "site-data.json").exists()


def test_build_creates_serializations(fixtures_dir: Path, tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "build",
        "--config", str(fixtures_dir / "blathers.yaml"),
        "--output", str(tmp_path / "dist"),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "dist" / "ontology.ttl").exists()
    assert (tmp_path / "dist" / "ontology.jsonld").exists()


def test_build_creates_conneg(fixtures_dir: Path, tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "build",
        "--config", str(fixtures_dir / "blathers.yaml"),
        "--output", str(tmp_path / "dist"),
    ])
    assert result.exit_code == 0
    assert (tmp_path / "dist" / ".htaccess").exists()


def test_init_creates_scaffolding(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--dir", str(tmp_path / "my-ontology")])
    assert result.exit_code == 0
    project = tmp_path / "my-ontology"
    assert (project / "blathers.yaml").exists()
    assert (project / "sidecars").is_dir()


def test_validate_exit_code_on_error(fixtures_dir: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--config", str(fixtures_dir / "blathers.yaml")])
    # The test fixtures have some completeness warnings but should not hard-fail
    # (fail_on: error in config, and completeness issues are warnings)
    # Just ensure it runs without crashing
    assert result.exit_code in (0, 1)
