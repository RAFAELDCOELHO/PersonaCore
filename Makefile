.PHONY: install test lint format demo

# Prefer python3.11 (the project target). If it is missing, use python3.
PYTHON ?= $(shell command -v python3.11 2>/dev/null || command -v python3)
VENV := .venv
VENV_PY := $(VENV)/bin/python

# Local laptop + CI only. NEVER run `make install` on Kaggle — Kaggle's
# pre-installed torch is the Pascal-compatible wheel and must stay untouched.
# `demo` (gradio) is NOT optional for the test suite: tests/test_phase14_demo.py imports
# scripts/personalize_demo.py, which imports gradio at module scope, so without it
# `make test` is a hard pytest COLLECTION error on a fresh clone — not a skip. These
# extras must stay identical to .github/workflows/ci.yml and CLAUDE.md (W-06).
install:
	pip install -e ".[cpu,dev,demo]" --extra-index-url https://download.pytorch.org/whl/cpu

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check . && .venv/bin/ruff format --check .

# isort runs first; ruff (format, then check --fix with rule I) has the final
# word so the end state always matches `make lint` (ruff-canonical imports).
format:
	.venv/bin/isort tests/ scripts/ src/
	.venv/bin/ruff format .
	.venv/bin/ruff check --fix .

# Laptop / public-clone only. NEVER run `make demo` on Kaggle: it creates a local
# `.venv` and installs a CPU torch wheel, which would replace the Pascal-compatible
# Kaggle torch. Story Gradio only (`scripts/demo_app.py`). The teach-then-recall
# demo needs checkpoints that are not in the m1-demo-v1 release.
$(VENV_PY):
	@test -n "$(PYTHON)" || (echo "Need python3.11 or python3 on PATH"; exit 1)
	$(PYTHON) -m venv $(VENV)

demo: $(VENV_PY)
	$(VENV)/bin/pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
	$(VENV_PY) scripts/fetch_demo_checkpoint.py
	$(VENV_PY) scripts/demo_app.py

