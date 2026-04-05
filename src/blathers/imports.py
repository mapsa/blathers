"""Import resolution and caching for ontology dependencies."""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import Graph

from blathers.config import ImportConfig


def uri_to_cache_filename(uri: str, profile: str | None = None) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", uri)
    safe = re.sub(r"_+", "_", safe)
    if profile:
        safe = f"{safe}__{profile}"
    return safe + ".ttl"


def _resolve_uri(uri: str, profile: str | None) -> str:
    """Apply profile to a URI for content negotiation.

    For vocabularies that support profile-based conneg (e.g., DPV),
    appending the profile to the URI path selects the variant:
      https://w3id.org/dpv/ai + profile "owl" → https://w3id.org/dpv/ai/owl
    """
    if not profile:
        return uri
    base = uri.rstrip("/")
    return f"{base}/{profile}"


class ImportResolver:
    def __init__(
        self,
        imports: list[ImportConfig],
        project_dir: Path,
        cache_dir: Path,
    ) -> None:
        self.imports = imports
        self.project_dir = project_dir
        self.cache_dir = cache_dir

    def resolve(self, imp: ImportConfig) -> Graph | None:
        # 1. Try local path first
        if imp.path:
            local = self.project_dir / imp.path
            if local.exists():
                g = Graph()
                g.parse(str(local), format="turtle")
                return g

        # 2. Try cache (profile-specific)
        cache_file = self.cache_dir / uri_to_cache_filename(
            imp.uri, imp.profile
        )
        if cache_file.exists():
            g = Graph()
            g.parse(str(cache_file), format="turtle")
            return g

        # 3. Fetch remotely with profile-resolved URI
        fetch_uri = _resolve_uri(imp.uri, imp.profile)
        try:
            g = Graph()
            g.parse(fetch_uri)
            self._cache_graph(g, imp.uri, imp.profile)
            return g
        except Exception:
            return None

    def resolve_all(self) -> dict[str, Graph]:
        resolved: dict[str, Graph] = {}
        for imp in self.imports:
            graph = self.resolve(imp)
            if graph is not None:
                resolved[imp.uri] = graph
        return resolved

    def fetch_and_cache(self, imp: ImportConfig) -> bool:
        try:
            g = Graph()
            if imp.path:
                local = self.project_dir / imp.path
                if local.exists():
                    g.parse(str(local), format="turtle")
                    self._cache_graph(g, imp.uri, imp.profile)
                    return True
            fetch_uri = _resolve_uri(imp.uri, imp.profile)
            g.parse(fetch_uri)
            self._cache_graph(g, imp.uri, imp.profile)
            return True
        except Exception:
            return False

    def _cache_graph(
        self, g: Graph, uri: str, profile: str | None = None
    ) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / uri_to_cache_filename(uri, profile)
        g.serialize(str(cache_file), format="turtle")
