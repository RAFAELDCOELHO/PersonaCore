.PHONY: install test lint format

# Local laptop + CI only. NEVER run `make install` on Kaggle — Kaggle's
# pre-installed torch is the Pascal-compatible wheel and must stay untouched.
install:
	pip install -e ".[cpu,dev]" --extra-index-url https://download.pytorch.org/whl/cpu

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

# isort runs first; ruff (format, then check --fix with rule I) has the final
# word so the end state always matches `make lint` (ruff-canonical imports).
format:
	.venv/bin/isort tests/ scripts/ src/
	.venv/bin/ruff format .
	.venv/bin/ruff check --fix .
