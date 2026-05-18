.PHONY: install dev up down restart lint

install:
	uv sync

## Run API in Docker with live reload (source files mounted, no rebuild needed).
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

up:
	docker compose up --build -d

down:
	docker compose down

## Restart dev containers (live reload — no image rebuild needed).
restart:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

## Auto-fix imports/style; report any remaining logic errors.
lint:
	uv run ruff check --fix .
	uv run ruff format .
