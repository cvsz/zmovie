PRODUCT_JSON ?=
PRODUCT_IMAGE ?=
PRODUCT_COUNT ?= 3
PRODUCT_DURATION ?=
PRODUCT_ASPECT_RATIO ?=
PRODUCT_OUTPUT_DIR ?= data/zflow/products

.PHONY: product-studio product-plan product-video product-video-1 product-video-3 \
	worker-status worker-jobs worker-recover watchdog-status watchdog-run backups backup-status \
	vulkan-status renderer-doctor sdcpp-evidence upgrade-readiness

product-studio: ## Run the reusable product-video frontend at /product
	$(PYTHON) -m uvicorn main:app --host $(HOST) --port $(PORT)

product-plan: ## Assess any product JSON and generate a suitability/creative plan without rendering
	@test -n "$(PRODUCT_JSON)" || { echo "PRODUCT_JSON=/path/to/product.json is required" >&2; exit 2; }
	$(PYTHON) ./scripts/zflow_product.py "$(PRODUCT_JSON)" \
		--plan-only \
		--count "$(PRODUCT_COUNT)" \
		--output-dir "$(PRODUCT_OUTPUT_DIR)" \
		$$(test -z "$(PRODUCT_DURATION)" || printf '%s' '--duration $(PRODUCT_DURATION)') \
		$$(test -z "$(PRODUCT_ASPECT_RATIO)" || printf '%s' '--aspect-ratio $(PRODUCT_ASPECT_RATIO)')

product-video: ## Assess and render reusable product-video variants; PRODUCT_JSON=... PRODUCT_IMAGE=...
	@test -n "$(PRODUCT_JSON)" || { echo "PRODUCT_JSON=/path/to/product.json is required" >&2; exit 2; }
	@test -n "$(PRODUCT_IMAGE)" || { echo "PRODUCT_IMAGE=/path/to/product-image.png is required" >&2; exit 2; }
	@test -n "$(WORKFLOW)" || { echo "WORKFLOW=/path/to/comfyui-video-workflow.json is required" >&2; exit 2; }
	ZMOVIE_COMFYUI_URL="$(RENDERER_URL)" ZMOVIE_COMFYUI_WORKFLOW="$(WORKFLOW)" \
		$(PYTHON) ./scripts/zflow_product.py "$(PRODUCT_JSON)" \
		--image "$(PRODUCT_IMAGE)" \
		--count "$(PRODUCT_COUNT)" \
		--output-dir "$(PRODUCT_OUTPUT_DIR)" \
		$$(test -z "$(PRODUCT_DURATION)" || printf '%s' '--duration $(PRODUCT_DURATION)') \
		$$(test -z "$(PRODUCT_ASPECT_RATIO)" || printf '%s' '--aspect-ratio $(PRODUCT_ASPECT_RATIO)')

product-video-1: PRODUCT_COUNT=1
product-video-1: product-video ## Render one assessed product-video variant

product-video-3: PRODUCT_COUNT=3
product-video-3: product-video ## Render three assessed product-video variants

worker-status: ## Durable worker queue summary
	$(PYTHON) -m zmovie_platform.runtime_ops worker-status

worker-jobs: ## List durable worker jobs
	$(PYTHON) -m zmovie_platform.runtime_ops worker-jobs

worker-recover: ## Dry-run stale worker lease recovery; use APPLY=1 to mutate
	$(PYTHON) -m zmovie_platform.runtime_ops worker-recover $$(test "$(APPLY)" = "1" && printf '%s' '--apply')

watchdog-status: ## Show watchdog inputs without restarting anything
	$(PYTHON) -m zmovie_platform.runtime_ops watchdog-status

watchdog-run: ## Execute one conservative watchdog check
	$(PYTHON) -m zmovie_platform.runtime_ops watchdog-run

backups: ## List verified SQLite backups
	$(PYTHON) -m zmovie_platform.runtime_ops backups

backup-status: ## Show backup coverage/retention status
	$(PYTHON) -m zmovie_platform.runtime_ops backup-status

vulkan-status: ## Inspect /dev/dri, Vulkan and sd-cli devices
	$(PYTHON) -m zmovie_platform.runtime_ops vulkan-status

renderer-doctor: ## Inspect worker-side renderer prerequisites
	$(PYTHON) -m zmovie_platform.runtime_ops renderer-doctor

sdcpp-evidence: ## Record stable-diffusion.cpp runtime evidence (inspection only by default)
	$(PYTHON) -m zmovie_platform.runtime_ops sdcpp-evidence $$(test "$(RUN_SMOKE)" = "1" && printf '%s' '--run-smoke')

upgrade-readiness: ## Refuse unsafe upgrades with active leases or ambiguous external state
	$(PYTHON) -m zmovie_platform.runtime_ops upgrade-readiness
