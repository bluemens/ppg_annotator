# Makefile for building and installing the ppg-annotator package

PACKAGE_NAME=ppg_annotator
DIST_DIR=dist
VERSION=$(shell python setup.py --version)

.PHONY: help clean build install editable uninstall release

help:
	@echo ""
	@echo "Available commands:"
	@echo "  make build        - Build wheel and source dist"
	@echo "  make install      - Install the built package"
	@echo "  make editable     - Install in editable (-e) mode"
	@echo "  make uninstall    - Uninstall the package"
	@echo "  make release      - Clean + build + install (upgrade)"
	@echo "  make clean        - Remove build artifacts"
	@echo ""

clean:
	rm -rf build/ *.egg-info/ $(DIST_DIR)/

build:
	python setup.py sdist bdist_wheel

install:
	pip install --upgrade $(DIST_DIR)/$(PACKAGE_NAME)-$(VERSION)-py3-none-any.whl

editable:
	pip install --editable .

uninstall:
	pip uninstall -y $(PACKAGE_NAME)

release: clean build install
