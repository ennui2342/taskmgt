.PHONY: react-dev react-up build test test-api install-cli logs ps help

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

# ── CLI ───────────────────────────────────────────────────────────────────────

install-cli: ## Install the tm CLI and symlink to /usr/local/bin
	pip3 install -e ".[cli]"
	ln -sf "$$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))')/tm" /usr/local/bin/tm
	mkdir -p ~/.claude/skills/tm
	cp skills/SKILL.md ~/.claude/skills/tm/
	@echo "tm installed: $$(which tm)"

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
