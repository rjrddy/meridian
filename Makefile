PY ?= .venv/bin/python
.PHONY: setup build lint test bench demo seed scan
setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e '.[dev]'
	npm ci --prefix apps/web
build:
	$(PY) -m pip install --no-deps -e .
	npm run build --prefix apps/web
lint:
	$(PY) -m ruff check meridian tests benchmarks scripts setup.py
	$(PY) -m ruff format --check meridian tests benchmarks scripts setup.py
	.venv/bin/clang-format --dry-run --Werror core/fusion.cpp
	npm run lint --prefix apps/web
test:
	$(PY) -m pytest -q
bench:
	$(PY) benchmarks/run.py
demo:
	docker compose up --build
seed:
	$(PY) scripts/seed.py
scan:
	$(PY) -m pip_audit
	npm audit --prefix apps/web --audit-level=high
