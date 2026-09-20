.PHONY: all init build-cpp build-frontend test benchmark run clean redis-start redis-stop redis-ping docker-build docker-up docker-down

init:
	./scripts/init_services.sh

PYTHON ?= .venv/bin/python3
PYTEST ?= .venv/bin/pytest
REDIS_SERVER ?= bin/redis-server
REDIS_CLI ?= bin/redis-cli

all: build-cpp build-frontend

build-cpp:
	$(MAKE) -C backend/cpp

build-frontend:
	cd frontend && npm run build

test: build-cpp
	$(PYTEST) backend/tests -v --cov=backend/aegis --cov-report=term-missing

benchmark: build-cpp
	$(PYTHON) benchmarks/latency_test.py 200

# Native Redis Service Controls
redis-start:
	@if [ -f "$(REDIS_SERVER)" ]; then \
		$(REDIS_SERVER) redis.conf && echo "Redis daemon started on port 6379."; \
	else \
		echo "Redis server binary not found. Run 'make build-redis' or use system redis-server."; \
	fi

redis-stop:
	@if [ -f "$(REDIS_CLI)" ]; then \
		$(REDIS_CLI) shutdown nosave 2>/dev/null || true && echo "Redis daemon stopped."; \
	fi

redis-ping:
	@if [ -f "$(REDIS_CLI)" ]; then \
		$(REDIS_CLI) ping; \
	else \
		echo "PONG (In-Memory Fallback Active)"; \
	fi

# Docker & Container Orchestration
docker-build:
	docker compose build

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

run: build-cpp build-frontend
	$(PYTHON) -m uvicorn aegis.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

clean:
	$(MAKE) -C backend/cpp clean
	rm -rf frontend/dist .pytest_cache .coverage veles_shield.db aegis_trust.db
