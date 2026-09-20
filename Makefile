.PHONY: all build-cpp build-frontend test benchmark run clean

PYTHON ?= .venv/bin/python3
PYTEST ?= .venv/bin/pytest

all: build-cpp build-frontend

build-cpp:
	$(MAKE) -C backend/cpp

build-frontend:
	cd frontend && npm run build

test: build-cpp
	$(PYTEST) backend/tests -v --cov=backend/aegis --cov-report=term-missing

benchmark: build-cpp
	$(PYTHON) benchmarks/latency_test.py 200

run: build-cpp build-frontend
	$(PYTHON) -m uvicorn aegis.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

clean:
	$(MAKE) -C backend/cpp clean
	rm -rf frontend/dist .pytest_cache .coverage aegis_trust.db
