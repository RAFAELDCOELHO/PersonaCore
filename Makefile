.PHONY: install test lint format demo

# `make demo` builds $(VENV) with this interpreter and then pip-installs the package into
# it, so it must be one pyproject can actually accept (requires-python >=3.10,<3.12). A bare
# `command -v python3` fallback is NOT that: on any machine whose python3 is 3.12+ — the
# default on current macOS/Homebrew — it built a venv pip then refused with "Package
# 'personacore' requires a different Python", and because .venv survives the failure, every
# later `make demo` failed identically without ever naming the real cause. So ask each
# candidate for its version instead of trusting its name: a `python3` that happens to be 3.11
# still works, and a 3.12+ one is skipped rather than half-installed into.
# PY_SUPPORTED is the single spelling of that bound; tests/test_demo_bootstrap.py pins it
# equal to pyproject's requires-python so the two cannot drift apart.
PY_SUPPORTED := import sys; raise SystemExit(not ((3,10) <= sys.version_info < (3,12)))
PYTHON ?= $(shell for p in python3.11 python3.10 python3; do "$$p" -c '$(PY_SUPPORTED)' >/dev/null 2>&1 && { command -v "$$p"; break; }; done)
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
	@test -n "$(PYTHON)" || { \
	  echo "make demo needs Python 3.10 or 3.11 on PATH (pyproject requires-python: >=3.10,<3.12)."; \
	  echo "None of python3.11 / python3.10 / python3 reported a supported version."; \
	  echo "Install one, e.g.  brew install python@3.11   or   sudo apt install python3.11"; \
	  exit 1; }
	$(PYTHON) -m venv $(VENV)

# The $(VENV_PY) prerequisite only fires when .venv is ABSENT. A .venv left behind by an
# older `make demo` (or created by hand from a 3.12+ interpreter) satisfies it while still
# being uninstallable — the persistent form of the same failure. Re-check the venv itself.
demo: $(VENV_PY)
	@$(VENV_PY) -c '$(PY_SUPPORTED)' || { \
	  echo "Existing $(VENV) runs $$($(VENV_PY) -V 2>&1), outside pyproject's >=3.10,<3.12."; \
	  echo "Remove it (rm -rf $(VENV)) and re-run make demo."; \
	  exit 1; }
	$(VENV)/bin/pip install -e ".[cpu,demo]" --extra-index-url https://download.pytorch.org/whl/cpu
	$(VENV_PY) scripts/fetch_demo_checkpoint.py
	$(VENV_PY) scripts/demo_app.py

