VERSION := $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

.PHONY: build publish clean

build:
	python3 -m build

publish: build
	twine upload dist/blathers-$(VERSION)* --username __token__

clean:
	rm -rf dist/ build/ src/*.egg-info
