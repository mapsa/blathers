"""Tests for CLI entry points."""

from click.testing import CliRunner

from blathers.cli import main


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "1.0.0a1" in result.output


def test_init_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0


def test_validate_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["validate"])
    assert result.exit_code == 0


def test_build_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["build"])
    assert result.exit_code == 0


def test_fetch_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["fetch"])
    assert result.exit_code == 0
