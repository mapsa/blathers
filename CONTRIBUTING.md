# Contributing to Blathers

Thanks for your interest in contributing! Here's how to get started.

## Prerequisites

- Python 3.10+
- git

## Setup

```bash
git clone https://github.com/mapsa/blathers.git
cd blathers
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

## Code style

- Follow PEP 8 conventions.
- Use type hints for function signatures.
- Keep functions focused and well-documented.

## Pull request process

1. Fork the repo and create a feature branch from `main`.
2. Add tests for any new functionality.
3. Ensure all tests pass with `pytest`.
4. Open a pull request with a clear description of the change.

## Reporting issues

Open an issue at https://github.com/mapsa/blathers/issues with:

- A clear title and description.
- Steps to reproduce the problem.
- Expected vs actual behavior.
- Your Python version and OS.
