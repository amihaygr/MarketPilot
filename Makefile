.PHONY: help validate test lint format compose-config up down status logs

help:
	@echo "validate       Validate Python, contracts and Compose"
	@echo "test           Run the unit and contract test suite"
	@echo "compose-config Render and validate Docker Compose"
	@echo "up             Start the local platform"
	@echo "down           Stop the local platform"

validate: repository-check lint test compose-config

repository-check:
	python scripts/validate_repository.py

test:
	docker compose --profile tools run --rm --build test-runner

lint:
	docker compose --profile tools run --rm --build test-runner sh -c "ruff check . && ruff format --check ."

format:
	python -m ruff format .
	python -m ruff check --fix .

compose-config:
	docker compose --env-file .env config --quiet

up:
	docker compose --env-file .env up -d

down:
	docker compose --env-file .env down

status:
	docker compose ps

logs:
	docker compose logs --tail=200
