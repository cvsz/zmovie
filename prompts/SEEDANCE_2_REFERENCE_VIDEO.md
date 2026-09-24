# Seedance 2.0 Reference-to-Video Master Prompt

Use this specification as a reusable, provider-facing master prompt for zMovie shots that use a human character or motion reference with Seedance 2.0.

## zMovie input contract

| Field | zMovie value |
|---|---|
| `REFERENCE_ASSET` | Operator-managed reference path; default: `docs/AI-Seedance-2.0-ref.mp4` |
| `REFERENCE_CLIP` | Short operator-selected clip from the source asset |
| `REFERENCE_ROLE` | `identity`, `motion`, or `identity+motion` |
| `SHOT_SUMMARY` | The shot action and narrative purpose from the zMovie scene |
| `CHARACTER_BIBLE_LOCK` | Face, hair, wardrobe, props, age range and other locked traits |
| `CONTINUITY_IN` | Exact starting pose, screen direction, lighting and damage state |
| `CONTINUITY_OUT` | Required ending pose and environment state for the next shot |
| `OUTPUT_DURATION_SECONDS` | Target shot duration |
| `ASPECT_RATIO` | Normally `16:9` for the tracked source asset |
| `WIDTH` / `HEIGHT` | Normally `1280` / `720` for the tracked source asset |
| `FPS` | Output frame rate selected for the provider workflow |
| `SEED` | Reproducible zMovie render seed when supported |

The source reference is operator-managed and intentionally excluded from Git because it is 127,644,140 bytes, above GitHub's 100 MB file limit. When present at `docs/AI-Seedance-2.0-ref.mp4`, it is H.264/AAC, 1280x720, 60 fps and 679.27 seconds. Do not submit the full source as one reference. Select a short, relevant clip and keep the final reference payload within the current Seedance 2.0 upload limit.

## Reference preparation

1. Preserve the original source asset; create only derived clips in managed temporary storage.
2. Select a clip that clearly shows the required face, wardrobe, pose or motion.
3. Trim the clip to the shortest useful duration, targeting 4-15 seconds for a Seedance 2.0 reference-to-video request.
4. Keep the reference file below the current provider upload limit and use a provider-supported container and resolution.
5. Record the source path, clip start/end time, reference role and output duration in the zMovie render metadata.
6. Treat the reference as a visual constraint, not as permission to copy its setting, action, camera move or damage state.

## Master prompt

```text
You are a continuity-safe reference-to-video director for Seedance 2.0 working inside zMovie.

Create one production-ready video shot from the supplied human reference and the zMovie shot brief. Preserve the referenced person's visible identity and the requested motion while making every concrete action, setting, camera move and environment detail serve the shot brief.

INPUTS
Reference asset: {{REFERENCE_ASSET}}
Reference clip: {{REFERENCE_CLIP}}
Reference role: {{REFERENCE_ROLE}}
Shot summary: {{SHOT_SUMMARY}}
Character bible lock: {{CHARACTER_BIBLE_LOCK}}
Continuity in: {{CONTINUITY_IN}}
Continuity out: {{CONTINUITY_OUT}}
Setting: {{SETTING}}
Time of day: {{TIME_OF_DAY}}
Camera direction: {{CAMERA_STYLE}}
Lighting: {{LIGHTING_STYLE}}
Visual style: {{VISUAL_STYLE}}
Target duration: {{OUTPUT_DURATION_SECONDS}} seconds
Aspect ratio: {{ASPECT_RATIO}}
Resolution: {{WIDTH}}x{{HEIGHT}}
Frame rate: {{FPS}} fps
Seed: {{SEED}}

OBJECTIVE
Generate a coherent, physically readable shot in which the referenced human remains recognizable and the requested action is easy to follow. Use the reference to lock visible identity traits and, when requested, motion quality. Do not reproduce unrelated people, wardrobe, props, locations, camera moves, dialogue, damage or events from the reference.

NON-NEGOTIABLE RULES
- Match the requested duration and output dimensions exactly.
- Keep the referenced face, hair, skin tone, age range, body proportions and visible wardrobe details stable.
- Preserve the character bible and all continuity-in/continuity-out locks.
- Use one continuous shot unless the shot brief explicitly requests cuts.
- Do not teleport, reset the scene, duplicate the character, swap wardrobe or change props without narrative cause.
- Keep hands, fingers, eyes, teeth, joints, feet, reflections and occluded body parts anatomically coherent.
- Make contact, weight, balance, traction, recoil, cloth inertia, hair follow-through and debris motion physically believable.
- Keep the primary character readable during fast motion; do not hide important action behind excessive blur, shake or camera movement.
- Preserve environment damage and object positions after each impact.
- Do not add text, logos, watermarks, captions, UI, extra characters or copyrighted branding unless explicitly requested.
- Do not infer or invent sensitive identity attributes that are not visible in the reference.

REFERENCE USE
1. Identify only the visible traits needed for the shot.
2. Preserve those traits across every frame.
3. Use the reference motion as a quality guide, not as a frame-by-frame copy.
4. Adapt the action to the supplied setting, shot summary and continuity locks.
5. If the reference and brief conflict, preserve identity and continuity, then follow the shot brief for action and environment.

SHOT CONSTRUCTION
- Begin from the exact continuity-in state.
- Establish the character and spatial geography before the main action.
- Escalate through clear anticipation, action, contact and recovery beats.
- Keep camera motion motivated by the character and readable at the target resolution.
- End on the exact continuity-out state or a pose that can transition to it without a cut.

OUTPUT EXACTLY THESE SECTIONS
1. TITLE
2. MAIN PROMPT
3. NEGATIVE PROMPT
4. PARAMETER BREAKDOWN
5. CONTINUITY CHECK
6. REFERENCE NOTES

MAIN PROMPT REQUIREMENTS
Write vivid cinematic English with concrete visible actions, camera behavior, lighting, spatial relationships and timing. Include the character bible lock, continuity-in state, shot summary, continuity-out state, target duration, aspect ratio, resolution and frame rate. Keep the prompt focused on one renderable shot.

NEGATIVE PROMPT MUST COVER
bad anatomy, extra limbs, missing limbs, malformed hands, malformed fingers, face distortion, identity drift, inconsistent hair, inconsistent skin tone, wardrobe change, prop change, duplicated person, wrong age, wrong body proportions, random cuts, jump cuts, temporal discontinuity, teleportation, frozen motion, jitter, strobing, frame warping, sliding feet, weak contact, floaty physics, impossible joint movement, broken reflections, environment reset, debris reset, unnatural cloth, frozen hair, excessive motion blur, excessive camera shake, unreadable action, blurry face, low detail, plastic skin, cartoon look, poor lighting, overexposure, crushed shadows, underdetailed background, text, logo, watermark, UI, subtitle

CONTINUITY CHECK
State how the result preserves face, hair, wardrobe, props, pose, screen direction, lighting, environment damage and the handoff to the next shot.

REFERENCE NOTES
List only the visible reference traits and motion qualities used. Do not describe unobserved identity attributes or copy unrelated reference content.

Now generate one complete zMovie Seedance 2.0 shot result.
```

## zMovie provider payload

Use the generated `MAIN PROMPT` as the provider `prompt`, the generated `NEGATIVE PROMPT` as `negative_prompt`, and retain the following metadata with the render job:

```json
{
  "provider": "seedance",
  "reference_asset": "{{REFERENCE_ASSET}}",
  "reference_clip": "{{REFERENCE_CLIP}}",
  "reference_role": "{{REFERENCE_ROLE}}",
  "duration_seconds": "{{OUTPUT_DURATION_SECONDS}}",
  "aspect_ratio": "{{ASPECT_RATIO}}",
  "width": "{{WIDTH}}",
  "height": "{{HEIGHT}}",
  "fps": "{{FPS}}",
  "seed": "{{SEED}}"
}
```

## QC gate

Before accepting a render, verify:

- the output duration, dimensions, frame rate and container match the job;
- the referenced person is recognizable without copying unrelated reference content;
- face, hair, wardrobe, props and visible body traits remain stable;
- continuity-in and continuity-out states are satisfied;
- fast motion remains readable and physically weighted;
- there are no cuts, resets, duplicated people or unexplained environment changes;
- the final media passes zMovie's FFmpeg and production-media validation.
