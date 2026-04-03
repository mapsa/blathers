"""Configuration loading and validation for Blathers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ImportConfig(BaseModel):
    uri: str
    prefix: str
    path: Optional[str] = None


class PersonConfig(BaseModel):
    name: str
    affiliation: Optional[str] = None
    url: Optional[str] = None


class MetadataConfig(BaseModel):
    title: str
    version: str
    license: str
    namespace: str
    prefix: str
    # Optional fields for ReSpec-style header
    description: Optional[str] = None
    status: Optional[str] = None
    date: Optional[str] = None
    editors: list[PersonConfig] = Field(default_factory=list)
    authors: list[PersonConfig] = Field(default_factory=list)
    contributors: list[str] = Field(default_factory=list)
    repository: Optional[str] = None
    previous_version: Optional[str] = None
    copyright: Optional[str] = None


class ValidationRules(BaseModel):
    shacl: bool = True
    consistency: bool = True
    completeness: bool = True
    conventions: bool = True
    overlap: bool = True


class ValidationConfig(BaseModel):
    fail_on: str = "error"
    rules: ValidationRules = Field(default_factory=ValidationRules)
    overlap: Optional[dict] = None


class ConnegConfig(BaseModel):
    generate: list[str] = Field(default_factory=list)
    base_uri: str = ""
    formats: list[str] = Field(default_factory=lambda: ["html", "ttl"])


class BlathersConfig(BaseModel):
    ontology: Path
    shacl: list[Path] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    sidecars: Path = Path("sidecars/")
    figures: Path = Path("figures/")
    output: Path = Path("dist/")
    metadata: MetadataConfig
    imports: list[ImportConfig] = Field(default_factory=list)
    conneg: ConnegConfig = Field(default_factory=ConnegConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    _config_dir: Path = Path(".")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def resolve_path(self, rel: Path) -> Path:
        """Resolve a path relative to the config file's directory."""
        return self._config_dir / rel


def load_config(path: Path) -> BlathersConfig:
    """Load and validate a blathers.yaml config file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    config = BlathersConfig(**raw)
    # Store the config directory for path resolution
    object.__setattr__(config, "_config_dir", path.parent)
    return config
