PYTHON := python3
PIP := $(PYTHON) -m pip
VENV_DIR := .venv

.PHONY: help setup venv install-dev lint format test docs docker-build docker-test

help:
	@echo "Makefile targets: setup, venv, install-dev, lint, format, test, docker-build, docker-test"

venv:
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Created virtualenv in $(VENV_DIR). Activate with: source $(VENV_DIR)/bin/activate"

setup: venv install-dev

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

lint:
	$(VENV_DIR)/bin/ruff check . || true
	$(VENV_DIR)/bin/black --check . || true
	$(VENV_DIR)/bin/mypy src || true

format:
	$(VENV_DIR)/bin/ruff format . || true
	$(VENV_DIR)/bin/black . || true
	$(VENV_DIR)/bin/isort . || true

test:
	$(VENV_DIR)/bin/pytest -q

docker-build:
	@echo "Build docker image using docker/requirements-docker.txt"
	docker build -f docker/Dockerfile -t tumor-detection:local .

docker-test:
	@echo "Build and run lightweight test image for smoke tests"
	docker build -f docker/Dockerfile.test-lite -t tumor-test-lite .
	docker run --rm tumor-test-lite
