PRODUCT_JSON ?=
PRODUCT_IMAGE ?=
PRODUCT_COUNT ?= 3
PRODUCT_DURATION ?=
PRODUCT_ASPECT_RATIO ?=
PRODUCT_OUTPUT_DIR ?= data/zflow/products

.PHONY: product-plan product-video product-video-1 product-video-3

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
