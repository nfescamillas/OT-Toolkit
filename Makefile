.DEFAULT_GOAL := help

.PHONY: help setup install run frontend api backend dev test test-backend test-frontend coverage package

help: ## Show the available commands
	@echo "OT Toolkit commands:"
	@echo "  make setup          Install the app and development dependencies"
	@echo "  make run            Start the desktop frontend"
	@echo "  make api            Start the FastAPI backend"
	@echo "  make dev            Start the frontend and backend together"
	@echo "  make test           Run the complete test suite"
	@echo "  make test-backend   Run backend tests only"
	@echo "  make test-frontend  Run frontend tests only"
	@echo "  make coverage       Run tests with backend coverage"
	@echo "  make package        Build the Windows executable"

setup install: ## Install the app and development dependencies
	uv sync --extra dev

run frontend: ## Start the desktop frontend
	uv run ot-toolkit

api backend: ## Start the FastAPI backend
	uv run ot-toolkit-api

dev: ## Start the frontend and backend together
	$(MAKE) --no-print-directory -j2 api run

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
