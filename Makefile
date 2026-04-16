.PHONY: react-dev react-up build test test-api install-cli logs ps rename-tag delete-tag help

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

# ── DB Admin (live k8s) ───────────────────────────────────────────────────────

rename-tag: ## Rename a tag in the live DB: make rename-tag FROM=old TO=new
	$(if $(FROM),,$(error FROM is required))
	$(if $(TO),,$(error TO is required))
	kubectl --namespace taskmgt exec -it \
		$$(kubectl --namespace taskmgt get pod -l app=api -o jsonpath='{.items[0].metadata.name}') \
		-- bin/taskdb --db /data/tasks.db rename-tag $(FROM) $(TO)

delete-tag: ## Delete a tag from the live DB: make delete-tag TAG=name
	$(if $(TAG),,$(error TAG is required))
	kubectl --namespace taskmgt exec -it \
		$$(kubectl --namespace taskmgt get pod -l app=api -o jsonpath='{.items[0].metadata.name}') \
		-- bin/taskdb --db /data/tasks.db delete-tag $(TAG)

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
