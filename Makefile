SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
HOST ?= 127.0.0.1
PORT ?= 8080
COMPOSE ?= docker compose
PROVIDER ?= comfyui
PROJECT_ID ?=
RUN_ID ?=
JOB_ID ?=
TOPIC ?=
CONFIRM ?=
BACKEND ?= auto
WORKFLOW ?=
ROLE ?= video
RENDERER_URL ?= http://127.0.0.1:8188

.PHONY: help install full-stack upgrade uninstall purge backup status health doctor logs restart start stop control ctl \
	dev-setup dev test lint audit check compose-up compose-down compose-build compose-logs compose-ps \
	renderer-install renderer-config renderer-smoke renderer-production providers projects readiness content render assemble prepare export production run-status \
	bili-session bili-status bili-approve bili-publish production-release

help: ## Show Makefile commands
	@awk 'BEGIN {FS = ":.*## "; printf "zMovie automation\n\nUsage:\n  make <target> [VAR=value]\n\nTargets:\n"} /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Native production install on Ubuntu/Debian (systemd + Playwright + FFmpeg + TTS + CLI)
	sudo bash ./install.sh install
	sudo install -m 0755 /opt/zmovie/scripts/zmovie-ctl.sh /usr/local/bin/zmovie-ctl

full-stack: install ## Install zMovie + ComfyUI software stack; preserve existing renderer workflow
	@set -Eeuo pipefail; \
	if systemctl is-active --quiet comfyui 2>/dev/null; then \
		echo "ComfyUI service already active; preserving the existing renderer installation."; \
	else \
		echo "Installing ComfyUI backend=$(BACKEND)..."; \
		sudo env COMFYUI_BACKEND="$(BACKEND)" bash ./scripts/install-comfyui.sh; \
	fi; \
	configured="$$(sudo sed -n 's/^ZMOVIE_COMFYUI_WORKFLOW=//p' /etc/zmovie/zmovie.env 2>/dev/null | tail -n1)"; \
	if [[ -z "$$configured" ]]; then \
		echo "No renderer workflow configured; installing the model-free smoke workflow for integration checks only."; \
		sudo bash ./scripts/configure-comfyui.sh ./workflows/comfyui/smoke_api.json http://127.0.0.1:8188 smoke; \
	else \
		echo "Existing renderer workflow preserved: $$configured"; \
	fi; \
	echo; \
	echo "Full software stack installed."; \
	echo "Run: sudo zmovie-ctl doctor"; \
	echo "Real AI-video production additionally requires production_video_ready=true (role=video + accelerator)."

upgrade: ## Backup and upgrade the native production installation and CLI
	sudo bash ./install.sh upgrade
	sudo install -m 0755 /opt/zmovie/scripts/zmovie-ctl.sh /usr/local/bin/zmovie-ctl

uninstall: ## Remove service/code/config but retain persistent data
	sudo bash ./install.sh uninstall
	sudo rm -f /usr/local/bin/zmovie-ctl

purge: ## Remove service/code/config/data after taking a database backup
	sudo bash ./install.sh uninstall --purge
	sudo rm -f /usr/local/bin/zmovie-ctl

backup: ## Create a SQLite backup
	sudo bash ./install.sh backup

status: ## Show service status and health
	sudo zmovie-ctl status

health: ## Show health JSON
	sudo zmovie-ctl health

doctor: ## Check zMovie, FFmpeg, ComfyUI and production-render readiness
	sudo zmovie-ctl doctor

logs: ## Show recent service logs; use LINES=200 to change amount
	sudo zmovie-ctl logs $${LINES:-100}

restart: ## Restart zMovie service
	sudo zmovie-ctl restart

start: ## Start zMovie service
	sudo zmovie-ctl start

stop: ## Stop zMovie service
	sudo zmovie-ctl stop

control: ## Open the interactive CLI control panel
	sudo zmovie-ctl

ctl: control ## Alias for interactive CLI control panel

dev-setup: ## Create local venv and install Python + Chromium dependencies
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip wheel
	$(PIP) install -r requirements.txt
	PLAYWRIGHT_BROWSERS_PATH=.playwright $(PY) -m playwright install chromium

dev: ## Run local development API/Studio
	@test -x "$(PY)" || { echo "Run 'make dev-setup' first" >&2; exit 2; }
	$(PY) -m uvicorn main:app --host $(HOST) --port $(PORT) --reload

test: ## Run unit tests
	$(PYTHON) -m unittest discover -s tests -v

lint: ## Run Ruff when installed
	$(PYTHON) -m ruff check app.py main.py zmovie_platform tests

audit: ## Audit Python dependencies when pip-audit is installed
	$(PYTHON) -m pip_audit -r requirements.txt

check: ## Run compile, tests, shell syntax and frontend JS syntax
	$(PYTHON) -m compileall -q zmovie.py app.py main.py zmovie_platform tests
	$(PYTHON) -m unittest discover -s tests -v
	bash -n install.sh install-docker.sh scripts/*.sh
	node --check static/app.js
	node --check static/studio-preview.js

compose-build: ## Build Docker production image
	$(COMPOSE) build

compose-up: ## Start Docker stack
	$(COMPOSE) up -d --build

compose-down: ## Stop Docker stack
	$(COMPOSE) down

compose-logs: ## Follow Docker stack logs
	$(COMPOSE) logs -f --tail=$${LINES:-100}

compose-ps: ## Show Docker stack state
	$(COMPOSE) ps

renderer-install: ## Install/update local ComfyUI service; BACKEND=auto|nvidia|rocm|cpu
	sudo env COMFYUI_BACKEND="$(BACKEND)" bash ./scripts/install-comfyui.sh

renderer-config: ## Configure a workflow; WORKFLOW=/path/api.json ROLE=generic|smoke|video RENDERER_URL=http://host:8188
	@test -n "$(WORKFLOW)" || { echo "WORKFLOW=/real/path/to/workflow_api.json is required" >&2; exit 2; }
	sudo bash ./scripts/configure-comfyui.sh "$(WORKFLOW)" "$(RENDERER_URL)" "$(ROLE)"

renderer-smoke: ## Configure bundled model-free ComfyUI smoke workflow (never production-ready)
	sudo bash ./scripts/configure-comfyui.sh ./workflows/comfyui/smoke_api.json "$(RENDERER_URL)" smoke

renderer-production: ## Configure remote accelerated production video ComfyUI; WORKFLOW=... RENDERER_URL=http(s)://GPU:8188
	@test -n "$(WORKFLOW)" || { echo "WORKFLOW=/real/path/to/video_workflow_api.json is required" >&2; exit 2; }
	@test "$(RENDERER_URL)" != "http://127.0.0.1:8188" || { echo "renderer-production requires the real remote/private GPU URL; for a local accelerated GPU use renderer-config ROLE=video" >&2; exit 2; }
	sudo bash ./scripts/configure-remote-comfyui.sh "$(WORKFLOW)" "$(RENDERER_URL)"

providers: ## List render providers
	sudo zmovie-ctl providers

projects: ## List projects
	sudo zmovie-ctl projects

readiness: ## Show strict production readiness; PROJECT_ID=prj_...
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	sudo zmovie-ctl readiness "$(PROJECT_ID)"

content: ## Generate content + storyboard; TOPIC='...'
	@test -n "$(TOPIC)" || { echo "TOPIC is required" >&2; exit 2; }
	sudo zmovie-ctl content --topic "$(TOPIC)"

render: ## Render every shot with a real provider; PROJECT_ID=... PROVIDER=comfyui
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	sudo zmovie-ctl render "$(PROJECT_ID)" "$(PROVIDER)"

assemble: ## Strict production assembly; PROJECT_ID=prj_...
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	sudo zmovie-ctl assemble "$(PROJECT_ID)"

prepare: ## Prepare Bilibili package from validated final; PROJECT_ID=prj_...
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	sudo zmovie-ctl prepare "$(PROJECT_ID)"

export: ## Build production ZIP + checksums; PROJECT_ID=prj_...
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	sudo zmovie-ctl export "$(PROJECT_ID)"

production: ## One-click render->validate->assemble->prepare->export; stops at approval gate
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	sudo zmovie-ctl production "$(PROJECT_ID)" "$(PROVIDER)"

run-status: ## Production run status; PROJECT_ID=... optional RUN_ID=prod_...
	@test -n "$(PROJECT_ID)" || { echo "PROJECT_ID is required" >&2; exit 2; }
	@if [[ -n "$(RUN_ID)" ]]; then sudo zmovie-ctl run-status "$(PROJECT_ID)" "$(RUN_ID)"; else sudo zmovie-ctl run-status "$(PROJECT_ID)"; fi

bili-session: ## Check live Bilibili Creator Center session
	sudo zmovie-ctl bili-session

bili-status: ## Show Bilibili publish job; JOB_ID=pub_...
	@test -n "$(JOB_ID)" || { echo "JOB_ID is required" >&2; exit 2; }
	sudo zmovie-ctl bili-status "$(JOB_ID)"

bili-approve: ## Record exact-package approval; JOB_ID=pub_... CONFIRM=APPROVE
	@test "$(CONFIRM)" = "APPROVE" || { echo "CONFIRM=APPROVE is required" >&2; exit 2; }
	@test -n "$(JOB_ID)" || { echo "JOB_ID is required" >&2; exit 2; }
	sudo zmovie-ctl bili-approve "$(JOB_ID)" APPROVE

bili-publish: ## ONE real external submission; JOB_ID=pub_... CONFIRM=CONFIRM-PUBLISH
	@test "$(CONFIRM)" = "CONFIRM-PUBLISH" || { echo "CONFIRM=CONFIRM-PUBLISH is required" >&2; exit 2; }
	@test -n "$(JOB_ID)" || { echo "JOB_ID is required" >&2; exit 2; }
	sudo zmovie-ctl bili-publish "$(JOB_ID)" CONFIRM-PUBLISH

production-release: ## Build the maintained ZeaZDev/Bilibili release candidate and stop at human approval
	sudo bash ./scripts/production-release.sh
