.DEFAULT_GOAL := help

.PHONY: help setup install run frontend api backend dev web-install web-build web-dev docker-build docker-run test test-backend test-frontend coverage package

help: ## Show the available commands
	@echo "OT Toolkit commands:"
	@echo "  make setup          Install the app and development dependencies"
	@echo "  make run            Start the frontend (backend must be running)"
	@echo "  make api            Start the FastAPI backend"
	@echo "  make dev            Start the frontend and backend together"
	@echo "  make web-build      Build the browser frontend"
	@echo "  make web-dev        Start the Vite development server"
	@echo "  make docker-build   Build the combined container image"
	@echo "  make docker-run     Run the container on port 8000"
	@echo "  make test           Run the complete test suite"
	@echo "  make test-backend   Run backend tests only"
	@echo "  make test-frontend  Run frontend tests only"
	@echo "  make coverage       Run tests with backend coverage"
	@echo "  make package        Build the Windows executable"

setup install: ## Install the app and development dependencies
	uv sync --extra dev

run frontend: ## Start the desktop frontend (backend must already be running)
	uv run ot-toolkit

api backend: ## Start the FastAPI backend
	uv run ot-toolkit-api

dev: ## Start the frontend and backend together
	$(MAKE) --no-print-directory -j2 api run

web-install: ## Install browser frontend dependencies
	npm --prefix frontend ci

web-build: web-install ## Build browser frontend static files
	npm --prefix frontend run build

web-dev: ## Start Vite with API requests proxied to localhost:8000
	npm --prefix frontend run dev

docker-build: ## Build the combined frontend/backend image
	docker build -t ot-toolkit .

docker-run: ## Run the image with persistent SQLite storage
	docker run --rm -p 8000:8000 -v ot-toolkit-data:/data ot-toolkit

test: ## Run the complete test suite
	uv run pytest

test-backend: ## Run backend tests only
	uv run pytest backend/tests

test-frontend: ## Run frontend tests only
	uv run pytest frontend/tests

coverage: ## Run tests with backend coverage
	uv run pytest --cov=ot_toolkit_backend --cov-report=term-missing

package: ## Build the standalone Windows executable
	powershell -ExecutionPolicy Bypass -File frontend/scripts/build_windows.ps1
