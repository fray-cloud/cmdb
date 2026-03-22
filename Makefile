.PHONY: dev-up dev-down dev-logs dev-build dev-init prod-up prod-down prod-build \
       lint format test db-shell kafka-shell redis-shell clean dev-keygen dev-cert

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

dev-init: dev-build dev-up
	@echo "Running database migrations..."
	docker compose -f docker-compose.dev.yml run --rm auth-init
	docker compose -f docker-compose.dev.yml run --rm ipam-init
	docker compose -f docker-compose.dev.yml run --rm event-init
	docker compose -f docker-compose.dev.yml run --rm tenant-init
	@echo "All migrations completed."

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

dev-cert:
	@mkdir -p infrastructure/nginx/ssl
	openssl req -x509 -nodes -days 365 \
		-newkey rsa:2048 \
		-keyout infrastructure/nginx/ssl/key.pem \
		-out infrastructure/nginx/ssl/cert.pem \
		-subj "/CN=localhost"
	@echo "SSL certificates generated in infrastructure/nginx/ssl/"

dev-keygen:
	@mkdir -p keys
	openssl genrsa -out keys/private.pem 2048
	openssl rsa -in keys/private.pem -pubout -out keys/public.pem
	@echo "RSA keys generated in keys/"

clean:
	docker compose -f docker-compose.dev.yml down -v --remove-orphans
