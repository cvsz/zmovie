# Hyperframes in zMovie

zMovie includes a production-safe port of the Hyperframes creative template catalog from:

`cvsz/zworkforce/packages/zsp-aitool`

The copied preview assets originate from:

`packages/zsp-aitool/public/images/hyperframes/`

The template metadata and safety semantics originate from:

`packages/zsp-aitool/src/lib/hyperframes/template-marketplace.ts`

## Included templates

| ID | Category | Default format | Duration |
| --- | --- | --- | ---: |
| `showcase-clean` | product showcase | 9:16 | 15s |
| `discount-safe` | discount alert | 1:1 | 12s |
| `compare-fair` | comparison | 16:9 | 20s |
| `testimonial-style-safe` | testimonial-style | 9:16 | 18s |
| `short-cut-social` | social short cut | 9:16 | 10s |

## Studio

Open `/studio`, choose a Hyperframes creative template, then use **Generate Content + Storyboard**. Selecting a template applies its suggested aspect ratio and duration in the Studio form and sends the template ID to the server-side storyboard generator.

The server does not trust arbitrary template payloads from the browser. It resolves the template by ID from the built-in catalog and validates its category, preview path, format, duration, and content safety before applying the creative structure.

## CLI

List templates:

```bash
sudo zmovie-ctl hyperframes
```

Filter them:

```bash
sudo zmovie-ctl hyperframes --category comparison
sudo zmovie-ctl hyperframes --query affiliate
```

Generate a storyboard using a template:

```bash
sudo zmovie-ctl content \
  --topic 'Launch zMovie as a creator production platform' \
  --template showcase-clean \
  --brand ZeaZDev \
  --audience 'video creators and creative teams' \
  --goal 'product launch and conversion' \
  --call-to-action 'Create, render and publish with zMovie' \
  --duration 15 \
  --aspect-ratio 9:16
```

## Makefile

```bash
make hyperframes

make content \
  TOPIC='Launch zMovie as a creator production platform' \
  TEMPLATE=showcase-clean
```

## Safety boundary

Hyperframes is a **creative structure layer**, not a renderer. It does not bypass zMovie production gates. A generated storyboard must still pass QC and the selected render provider must be production-ready before One-click Production can continue.

Template guidance is prepended to the effective content brief and the operator brief is bounded so maximum-length input cannot truncate the template safety constraints. Unknown template IDs fail closed.
