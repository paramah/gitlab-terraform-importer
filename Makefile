.PHONY: help install install-dev build clean test lint format run

help: ## Pokaż tę pomoc
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Zainstaluj projekt z Poetry
	poetry install

install-dev: ## Zainstaluj projekt z dev dependencies
	poetry install --with dev

build: ## Zbuduj pakiet
	poetry build
	@echo "Pakiet zbudowany w dist/"
	@ls -lh dist/

clean: ## Usuń pliki build
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

test: ## Uruchom testy
	poetry run pytest tests/ -v

lint: ## Sprawdź kod (ruff)
	poetry run ruff check src/

format: ## Formatuj kod (black)
	poetry run black src/ tests/

run: ## Uruchom CLI (help)
	poetry run gitlab-importer --help

validate: ## Waliduj konfigurację
	poetry run gitlab-importer validate-config

inspect: ## Inspekcja GitLab
	poetry run gitlab-importer inspect

import: ## Import struktury
	poetry run gitlab-importer import-structure

# Development helpers
dev-setup: install-dev ## Przygotuj środowisko dev
	@echo "✓ Środowisko dev gotowe"
	@echo "Dostępne komendy:"
	@echo "  make run       - Uruchom CLI"
	@echo "  make test      - Testy"
	@echo "  make lint      - Linting"
	@echo "  make format    - Formatowanie"

watch: ## Watch mode dla testów
	poetry run pytest-watch

.DEFAULT_GOAL := help
