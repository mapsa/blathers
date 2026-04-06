PYTHON := .venv/bin/python
VERSION := $(shell $(PYTHON) -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

.PHONY: build publish clean

build:
	$(PYTHON) -m build

publish: build
	$(PYTHON) -m twine upload dist/blathers-$(VERSION)* --username __token__ --password "$(TWINE_PASSWORD)"

clean:
	rm -rf dist/ build/ src/*.egg-info
