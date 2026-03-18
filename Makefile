.PHONY: dev-up dev-down dev-logs dev-build prod-up prod-down prod-build \
       lint format test db-shell kafka-shell redis-shell clean

# Dev environment
dev-up:
	docker compose -f docker-compose.dev.yml up -d

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-build:
	docker build --target dev -t cmdb-base:dev -f infrastructure/docker/Dockerfile.base .
	docker compose -f docker-compose.dev.yml build

# Prod environment
prod-up:
	docker compose -f docker-compose.yml up -d

prod-down:
	docker compose -f docker-compose.yml down

prod-build:
	docker build --target prod -t cmdb-base:prod -f infrastructure/docker/Dockerfile.base .
	docker compose -f docker-compose.yml build

# Development utilities
lint:
	uv run ruff check .
	cd frontend && pnpm lint

format:
	uv run ruff format .

test:
	uv run pytest

db-shell:
	docker compose -f docker-compose.dev.yml exec postgres psql -U cmdb

kafka-shell:
	docker compose -f docker-compose.dev.yml exec kafka bash

redis-shell:
	docker compose -f docker-compose.dev.yml exec redis redis-cli

clean:
	docker compose -f docker-compose.dev.yml down -v --remove-orphans
	docker compose -f docker-compose.yml down -v --remove-orphans
