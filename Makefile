.PHONY: help build up down logs clean test backend-test frontend-test migrate

help:
	@echo "Payment Gateway Integration - Available commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make logs          - View logs"
	@echo "  make clean         - Clean containers and volumes"
	@echo "  make test          - Run all tests"
	@echo "  make backend-test  - Run backend tests"
	@echo "  make frontend-test - Run frontend tests"
	@echo "  make migrate       - Run database migrations"
	@echo "  make shell         - Open backend shell"
	@echo "  make frontend-shell - Open frontend shell"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

test: backend-test frontend-test

backend-test:
	docker-compose exec backend pytest

frontend-test:
	docker-compose exec frontend npm test

migrate:
	docker-compose exec backend alembic upgrade head

shell:
	docker-compose exec backend bash

frontend-shell:
	docker-compose exec frontend sh

dev:
	docker-compose up

restart:
	docker-compose restart

ps:
	docker-compose ps
