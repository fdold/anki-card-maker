VENV_PYTHON := ./.venv/bin/python

.PHONY: test test-unit install-dev

test:
	$(VENV_PYTHON) -m pytest

test-unit:
	$(VENV_PYTHON) -m pytest tests/unit

install-dev:
	$(VENV_PYTHON) -m pip install -e ".[dev]"
