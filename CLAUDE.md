# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

> **CLAUDE.ko.md** is a Korean translation for human readers. When editing this file, also update CLAUDE.ko.md. Claude Code should only reference this file (CLAUDE.md).

## Build & Development Commands

```bash
# Dependencies
uv sync                    # Install all workspace dependencies

# Testing
uv run pytest              # Run all tests
make test                  # Same as above
uv run pytest services/ipam/tests/test_domain/test_prefix.py::TestPrefixCreate::test_method  # Single test

# Linting & Formatting
uv run ruff check .        # Lint
make lint                  # Lint (includes frontend)
uv run ruff format .       # Format
make format                # Same as above

# Docker Dev Environment
make dev-up                # Start dev containers
make dev-down              # Stop dev containers
make dev-logs              # Tail dev container logs
make dev-build             # Build dev images

# Frontend
cd frontend && pnpm install && pnpm dev   # Dev server
cd frontend && pnpm lint                  # Lint frontend
```

## Architecture Overview

**uv monorepo workspace** with `services/*` and `shared` packages.

Each service follows **DDD + CQRS + Event Sourcing**:

```
services/<name>/src/<name>/
  domain/          # Aggregates, Entities, Value Objects, Domain Events, Repository interfaces
  application/     # Commands, Queries, Handlers, DTOs
  infrastructure/  # DB models, Repository implementations, Config
  interface/       # FastAPI routers, Schemas, Main app
```

**Shared library** (`shared/src/shared/`) provides:
- `domain/` — Base classes: Entity, ValueObject, AggregateRoot, Repository, DomainService, CustomField, Tag
- `cqrs/` — Command/Query bus, Command/Query base classes
- `event/` — Event Store, DomainEvent, AggregateRoot with ES, Snapshot support
- `api/` — Pagination, Filtering, Sorting, Error handling, OpenAPI utils, Middleware
- `messaging/` — Kafka Producer/Consumer, Serialization
- `db/` — Tenant DB manager (multi-tenancy)

**Tech stack**: Python 3.13, FastAPI, PostgreSQL, Kafka, Redis, Next.js (frontend)

## Design & Implementation Guidelines

### DDD Patterns
- **Entity**: Identity-based domain object with lifecycle
- **Value Object**: Immutable, equality by value
- **Aggregate**: Consistency boundary with AggregateRoot, accessed only through Repository
- **Repository**: Interface in domain layer, implementation in infrastructure
- **Domain Event**: Record of something that happened in the domain
- **Domain Service**: Logic that doesn't belong to a single Aggregate

### CQRS + Event Sourcing Flow
```
Command → CommandHandler → Aggregate (mutate via apply()) → DomainEvent
  → Event Store (append) + Kafka (publish)

Query → QueryHandler → Read Model (denormalized projection)
```

### Multi-Tenancy
- Tenant-level database isolation via `shared.db.tenant_db_manager`
- Each tenant gets its own schema or database

### Cross-Service Communication
- Services communicate **only** via async Kafka events
- No synchronous inter-service calls

### Clean Architecture Layers
- **Domain** depends on nothing
- **Application** depends on Domain
- **Infrastructure** depends on Domain + Application
- **Interface** depends on Application (never directly on Domain internals)

## Code Style

- **Ruff** config: `line-length = 120`, `target-version = "py313"`, `quote-style = "double"`
- Lint rules: E, F, I, N (except N802), W, UP, B, A, SIM
- **Pre-commit hooks** configured: `ruff --fix` + `ruff format`
- Run `uv run ruff check . && uv run ruff format .` before committing

## Project Management

- **GitHub repo**: `fray-cloud/cmdb`
- **Issue tracking**: GitHub Issues with milestone `P1` (Phase 1)
- **PRD**: Issue #1
- **Workflow**: section-by-section commits → push → check issue task checkboxes

## Available Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/grill-me` | "grill me", stress-test a design | Interview relentlessly about a plan until shared understanding |
| `/design-an-interface` | design API, explore interface options | Generate multiple interface designs in parallel |
| `/prd-to-plan` | break down PRD, plan phases | Turn PRD into tracer-bullet implementation plan |
| `/prd-to-issues` | convert PRD to issues | Break PRD into GitHub issues |
| `/triage-issue` | report bug, investigate issue | Triage bug with codebase exploration + TDD fix plan |
| `/ubiquitous-language` | define domain terms, glossary | Extract DDD ubiquitous language from conversation |
| `/request-refactor-plan` | plan refactor, refactoring RFC | Create refactor plan with tiny commits as GitHub issue |
| `/write-a-skill` | create new skill | Create new agent skills with proper structure |
| `/tdd` | TDD, red-green-refactor | Test-driven development loop |
