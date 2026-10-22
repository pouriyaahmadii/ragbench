# RAGBench - Makefile
# Development and operational commands
# All commands should be run from repository root

.PHONY: help up down down-v restart logs logs-api logs-web logs-db logs-qdrant \
        infra-up api-up web-up \
        migrate migrate-create shell-db shell-qdrant shell-api shell-web \
        test test-unit test-integration test-contract test-e2e test-all \
        lint format typecheck \
        eval eval-real \
        benchmark bench-ingestion bench-retrieval bench-generation bench-eval \
        backup-db backup-qdrant backup-all restore-db restore-qdrant \
        clean reindex \
        validate compose-validate secret-scan \
        ci

# Default target
help:
	@echo "RAGBench - Development Commands"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up              Start all services (docker compose up --wait)"
	@echo "  make down            Stop services (preserve volumes)"
	@echo "  make down-v          Stop and remove volumes (clean slate)"
	@echo "  make restart         Restart all services"
	@echo "  make logs            Follow all service logs"
	@echo "  make logs-api        Follow API logs only"
	@echo "  make logs-web        Follow Web logs only"
	@echo "  make logs-db         Follow PostgreSQL logs"
	@echo "  make logs-qdrant     Follow Qdrant logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         Run alembic migrations (upgrade head)"
	@echo "  make migrate-create  Create new migration (interactive)"
	@echo "  make shell-db        PostgreSQL shell (psql)"
	@echo "  make shell-qdrant    Qdrant shell (curl aliases)"
	@echo "  make shell-api       Shell into API container"
	@echo "  make shell-web       Shell into Web container"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests (unit + integration + contract)"
	@echo "  make test-unit       Unit tests only"
	@echo "  make test-integration Integration tests only"
	@echo "  make test-contract   Contract tests only"
	@echo "  make test-e2e        Playwright E2E tests (requires running stack)"
	@echo "  make test-all        All tests including E2E"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run linters (ruff + eslint)"
	@echo "  make format          Auto-format code (ruff + prettier)"
	@echo "  make typecheck       Type checking (mypy + tsc)"
	@echo ""
	@echo "Evaluation:"
	@echo "  make eval            Run fixture evaluation (Mock providers)"
	@echo "  make eval-real       Run real provider evaluation (requires keys)"
	@echo ""
	@echo "Benchmarking:"
	@echo "  make benchmark       Run all benchmarks"
	@echo "  make bench-ingestion Ingestion benchmark only"
	@echo "  make bench-retrieval Retrieval benchmark only"
	@echo "  make bench-generation Generation benchmark only"
	@echo "  make bench-eval      Evaluation benchmark only"
	@echo ""
	@echo "Backup & Restore:"
	@echo "  make backup-db       PostgreSQL dump to backups/"
	@echo "  make backup-qdrant   Qdrant snapshot"
	@echo "  make backup-all      Both database and Qdrant"
	@echo "  make restore-db      Restore PostgreSQL (set FILE=path)"
	@echo "  make restore-qdrant  Restore Qdrant (set SNAPSHOT=name)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean           Remove build artifacts, caches"
	@echo "  make reindex         Re-index all documents (interactive)"
	@echo "  make validate        Validate compose, configs, migrations"
	@echo "  make compose-validate Validate docker compose syntax"
	@echo "  make secret-scan     Scan for secrets (trufflehog)"
	@echo "  make ci              Run full CI pipeline locally"

# =============================================================================
# Infrastructure
# =============================================================================

infra-up:
	docker compose up -d postgres qdrant redis

api-up:
	docker compose up -d api

web-up:
	docker compose up -d web

up:
	docker compose up --wait

down:
	docker compose down

down-v:
	docker compose down -v

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-web:
	docker compose logs -f web

logs-db:
	docker compose logs -f postgres

logs-qdrant:
	docker compose logs -f qdrant

# =============================================================================
# Database
# =============================================================================

migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	docker compose exec api alembic revision --autogenerate -m "$$msg"

shell-db:
	docker compose exec postgres psql -U ragbench -d ragbench

shell-qdrant:
	@echo "Qdrant shell: Use curl commands against http://qdrant:6333"
	@echo "Example: curl http://qdrant:6333/collections"

shell-api:
	docker compose exec api bash

shell-web:
	docker compose exec web sh

# =============================================================================
# Testing
# =============================================================================

test: test-unit test-integration test-contract

test-unit:
	docker compose exec api pytest tests/unit -v --tb=short

test-integration:
	docker compose exec api pytest tests/integration -v --tb=short

test-contract:
	docker compose exec api pytest tests/contract -v --tb=short

test-e2e:
	cd apps/web && npx playwright test

test-all: test test-e2e

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "=== Python Lint (ruff) ==="
	docker compose exec api ruff check .
	@echo "=== Frontend Lint (eslint) ==="
	docker compose exec web npm run lint

format:
	@echo "=== Python Format (ruff) ==="
	docker compose exec api ruff format .
	@echo "=== Frontend Format (prettier) ==="
	docker compose exec web npm run format

typecheck:
	@echo "=== Python Typecheck (mypy) ==="
	docker compose exec api mypy .
	@echo "=== Frontend Typecheck (tsc) ==="
	docker compose exec web npx tsc --noEmit

# =============================================================================
# Evaluation
# =============================================================================

eval:
	docker compose exec api python -m app.evaluation.run_fixture

eval-real:
	@if [ -z "$$OPENAI_API_KEY" ] && [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: Set OPENAI_API_KEY or ANTHROPIC_API_KEY for real evaluation"; \
		exit 1; \
	fi
	docker compose exec -e MOCK_MODE=false api python -m app.evaluation.run_fixture

# =============================================================================
# Benchmarking
# =============================================================================

benchmark: bench-ingestion bench-retrieval bench-generation bench-eval

bench-ingestion:
	docker compose exec api python scripts/benchmarks/ingestion_benchmark.py

bench-retrieval:
	docker compose exec api python scripts/benchmarks/retrieval_benchmark.py

bench-generation:
	docker compose exec api python scripts/benchmarks/generation_benchmark.py

bench-eval:
	docker compose exec api python scripts/benchmarks/evaluation_benchmark.py

# =============================================================================
# Backup & Restore
# =============================================================================

backup-db:
	@mkdir -p backups
	docker compose exec postgres pg_dump -U ragbench -d ragbench > backups/pg_$$(date +%F_%H%M%S).sql
	@echo "Backup saved to backups/pg_$$(date +%F_%H%M%S).sql"

backup-qdrant:
	@mkdir -p backups
	curl -X POST http://127.0.0.1:6333/snapshots | jq -r '.result.name' | xargs -I {} echo "Snapshot created: {}"

backup-all: backup-db backup-qdrant

restore-db:
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backups/pg_2026-10-22.sql"; exit 1; fi
	docker compose exec -T postgres psql -U ragbench -d ragbench < $(FILE)

restore-qdrant:
	@if [ -z "$(SNAPSHOT)" ]; then echo "Usage: make restore-qdrant SNAPSHOT=snapshot_name"; exit 1; fi
	curl -X POST http://127.0.0.1:6333/snapshots/$(SNAPSHOT)/recover

# =============================================================================
# Utilities
# =============================================================================

clean:
	@echo "Cleaning build artifacts and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "Clean complete"

reindex:
	@echo "Re-indexing all documents..."
	@echo "This will prompt for chunking and embedding configuration."
	@echo "Not yet implemented - use API POST /documents/{id}/reindex"

# =============================================================================
# Validation
# =============================================================================

validate: compose-validate
	@echo "Validating configurations..."
	@echo "Checking .env.example exists..."
	@test -f .env.example && echo "OK" || (echo "Missing .env.example" && exit 1)
	@echo "Checking Python syntax..."
	docker compose exec api python -m py_compile $$(find app -name "*.py")
	@echo "Checking TypeScript..."
	docker compose exec web npx tsc --noEmit
	@echo "All validations passed"

compose-validate:
	docker compose config -q && echo "docker compose config valid"

secret-scan:
	@echo "Scanning for secrets..."
	@if command -v trufflehog >/dev/null 2>&1; then \
		trufflehog filesystem . --no-verification --fail; \
	else \
		echo "trufflehog not installed; skipping"; \
	fi

# =============================================================================
# CI Pipeline (Local)
# =============================================================================

ci: lint typecheck test validate secret-scan
	@echo "=== CI Pipeline Complete ==="