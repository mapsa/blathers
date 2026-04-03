# Blathers

Ontology documentation & validation CLI -- bridges auto-extracted OWL/SHACL definitions with Markdown narrative.

[![PyPI version](https://img.shields.io/pypi/v/blathers)](https://pypi.org/project/blathers/)
[![Python versions](https://img.shields.io/pypi/pyversions/blathers)](https://pypi.org/project/blathers/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- **5 validators** -- SHACL, consistency, completeness, naming conventions, and overlap detection
- **Sidecar Markdown** -- author rich narrative alongside your ontology using YAML frontmatter
- **Static HTML output** -- generates a self-contained documentation site with ReSpec-style layout
- **RDF/OWL extraction** -- parses classes, properties, and named individuals via rdflib
- **Content negotiation** -- generates Apache, nginx, and w3id configuration

## Quick start

```bash
pip install blathers
```

Scaffold a new project:

```bash
blathers init my-ontology
cd my-ontology
```

Validate your ontology:

```bash
blathers validate
```

Build the documentation site:

```bash
blathers build
```

## Configuration

Blathers reads from `blathers.yaml` in your project root:

```yaml
ontology: ontology/my-ontology.ttl
shacl: []
sidecars: sidecars/
figures: figures/
output: dist/

metadata:
  title: "My Ontology"
  version: "1.0.0"
  namespace: "http://example.org/onto#"
  prefix: onto

validation:
  fail_on: error
  rules:
    shacl: true
    consistency: true
    completeness: true
    conventions: true
    overlap: true
```

## Sidecar authoring

Create Markdown files in `sidecars/` with YAML frontmatter to add narrative:

```markdown
---
term: onto:MyClass
section: overview
order: 1
---

Description of MyClass and its role in the ontology.
```

## CLI commands

| Command    | Description                                      |
| ---------- | ------------------------------------------------ |
| `init`     | Scaffold a new ontology project                  |
| `validate` | Run validators against ontology and SHACL shapes |
| `build`    | Generate static HTML documentation site          |
| `fetch`    | Fetch remote ontology imports                    |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
