# zMovie

`zMovie` is a reusable cinematic prompt generator for AI video workflows, with an initial focus on Wan 3.0-style 20-second continuous action long takes.

## Included

- Production-ready Wan 3.0 master action prompt specification.
- Randomized cinematic variables for setting, character styling, attacker archetype, choreography, camera, lighting, destruction, and ending.
- Deterministic generation with `--seed`.
- Plain text or JSON output.
- Python standard library only (no third-party dependencies).

## Quick start

```bash
python zmovie.py
```

Generate three prompts:

```bash
python zmovie.py --count 3
```

Generate reproducibly:

```bash
python zmovie.py --seed 42
```

Emit JSON:

```bash
python zmovie.py --seed 42 --json
```

Save output to a file:

```bash
python zmovie.py --count 10 > prompts.txt
```

## Prompt timing model

Each generated video prompt follows a 20-second uninterrupted long-take structure:

| Time | Beat |
|---|---|
| 0:00–0:03 | Character introduction + threat appears |
| 0:03–0:06 | First exchange |
| 0:06–0:09 | Reversal / escalation |
| 0:09–0:12 | Environmental impact |
| 0:12–0:16 | Peak continuous combat |
| 0:16–0:18 | Decisive finishing move |
| 0:18–0:20 | Composed cinematic ending |

## Master specification

See [`prompts/WAN3_MASTER_ACTION_GENERATOR.md`](prompts/WAN3_MASTER_ACTION_GENERATOR.md).

## Design goals

- One continuous shot with no cuts.
- Strong temporal and character continuity.
- Readable but relentless choreography.
- Physically believable weight, momentum, collisions, cloth, hair, and debris.
- Clear contrast between elegant visual styling and high-intensity action.
- Reusable randomization rather than a single fixed scene.

## License

Use and adapt for your own zMovie workflows.
