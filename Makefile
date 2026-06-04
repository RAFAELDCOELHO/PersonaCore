.PHONY: install test lint format

# Local laptop + CI only. NEVER run `make install` on Kaggle — Kaggle's
# pre-installed torch is the Pascal-compatible wheel and must stay untouched.
install:
	pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

format:
	ruff format . && ruff check --fix .
