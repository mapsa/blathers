"""Import resolution and caching for ontology dependencies."""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import Graph

from blathers.config import ImportConfig


def uri_to_cache_filename(uri: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", uri)
    safe = re.sub(r"_+", "_", safe)
    return safe + ".ttl"


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
        if imp.path:
            local = self.project_dir / imp.path
            if local.exists():
                g = Graph()
                g.parse(str(local), format="turtle")
                return g

        cache_file = self.cache_dir / uri_to_cache_filename(imp.uri)
        if cache_file.exists():
            g = Graph()
            g.parse(str(cache_file), format="turtle")
            return g

        try:
            g = Graph()
            g.parse(imp.uri)
            self._cache_graph(g, imp.uri)
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
                    self._cache_graph(g, imp.uri)
                    return True
            g.parse(imp.uri)
            self._cache_graph(g, imp.uri)
            return True
        except Exception:
            return False

    def _cache_graph(self, g: Graph, uri: str) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / uri_to_cache_filename(uri)
        g.serialize(str(cache_file), format="turtle")
