.PHONY: react-dev react-up build test test-api logs ps help

# ── React ─────────────────────────────────────────────────────────────────────

react-dev: ## Start React dev server + API (hot reload, port 5173)
	docker compose up --build react-dev api

react-up: ## Start React production build + API (port 3000)
	docker compose up --build react-app api -d

# ── Build ─────────────────────────────────────────────────────────────────────

build: ## Build all images
	docker compose build

# ── Test ──────────────────────────────────────────────────────────────────────

test: ## Run the full test suite (BDD + API unit tests)
	docker compose run --rm test pytest -v

test-api: ## Run API unit tests only
	docker compose run --rm test-api pytest tests/api/ -v

# ── Ops ───────────────────────────────────────────────────────────────────────

logs: ## Tail logs from running services
	docker compose logs -f

ps: ## Show running services
	docker compose ps

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
