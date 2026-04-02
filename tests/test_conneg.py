"""Tests for content negotiation config generation."""

from pathlib import Path

from blathers.conneg import generate_conneg


def test_generate_htaccess(tmp_path: Path):
    generate_conneg(
        output_dir=tmp_path,
        generate=["htaccess"],
        base_uri="https://w3id.org/prism",
        formats=["html", "ttl", "jsonld", "nt"],
    )
    htaccess = tmp_path / ".htaccess"
    assert htaccess.exists()
    content = htaccess.read_text()
    assert "RewriteEngine On" in content
    assert "text/turtle" in content
    assert "application/ld+json" in content


def test_generate_nginx(tmp_path: Path):
    generate_conneg(
        output_dir=tmp_path,
        generate=["nginx"],
        base_uri="https://w3id.org/prism",
        formats=["html", "ttl", "jsonld"],
    )
    nginx_conf = tmp_path / "conneg.nginx.conf"
    assert nginx_conf.exists()
    content = nginx_conf.read_text()
    assert "text/turtle" in content
    assert "location" in content


def test_generate_w3id(tmp_path: Path):
    generate_conneg(
        output_dir=tmp_path,
        generate=["w3id"],
        base_uri="https://w3id.org/prism",
        formats=["html", "ttl", "jsonld"],
    )
    w3id = tmp_path / "w3id.htaccess"
    assert w3id.exists()
    content = w3id.read_text()
    assert "RewriteEngine On" in content


def test_generate_multiple(tmp_path: Path):
    generate_conneg(
        output_dir=tmp_path,
        generate=["htaccess", "nginx"],
        base_uri="https://w3id.org/prism",
        formats=["html", "ttl"],
    )
    assert (tmp_path / ".htaccess").exists()
    assert (tmp_path / "conneg.nginx.conf").exists()
