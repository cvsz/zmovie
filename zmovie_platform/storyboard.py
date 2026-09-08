from __future__ import annotations

import math
import random
import re
import uuid
from typing import Any

from zmovie import NEGATIVE_PROMPT, generate

from .models import CharacterBible, Project, Scene, Shot


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def build_character_lock(characters: list[CharacterBible]) -> str:
    if not characters:
        return "Maintain strict identity, wardrobe, hair, scale, and facial continuity for every recurring character."
    blocks = []
    for c in characters:
        blocks.append(
            f"{c.name} ({c.role}): appearance={c.appearance or 'consistent with established identity'}; "
            f"hair={c.hair or 'locked'}; wardrobe={c.wardrobe or 'locked'}; personality={c.personality or 'consistent'}; "
            f"movement/fight style={c.fighting_style or 'physically coherent'}; continuity={c.continuity_notes or 'preserve exactly'}."
        )
    return "CHARACTER BIBLE LOCK: " + " ".join(blocks)


def build_shot_prompt(project: Project, scene: Scene, shot: Shot, *, seed: int | None = None) -> tuple[str, str]:
    rng = random.Random(seed if seed is not None else f"{project.id}:{scene.id}:{shot.id}")
    base = generate(rng)
    base_prompt = str(base["main_prompt"])
    lock = build_character_lock(project.characters)
    continuity = (
        f"CONTINUITY IN: {shot.continuity_in or scene.continuity_notes or 'begin from the exact established spatial state'}. "
        f"CONTINUITY OUT: {shot.continuity_out or 'end on a stable state that can match the next shot'}."
    )
    instruction = (
        f"PROJECT: {project.name}. GENRE: {project.genre}. GLOBAL VISUAL STYLE: {project.visual_style}. "
        f"ASPECT RATIO: {project.aspect_ratio}. SCENE {scene.order_index}: {scene.title}. "
        f"LOCATION: {scene.location or 'cinematic location consistent with story'}. TIME: {scene.time_of_day}. MOOD: {scene.mood}. "
        f"SHOT {shot.order_index}: {shot.summary}. TARGET DURATION: {shot.duration_seconds} seconds. "
        f"{lock} {continuity} "
        "Treat the following generated choreography/cinematography language as a style and motion reference; adapt every concrete action and environment detail so it serves this shot summary and does not contradict the project bible. "
        f"REFERENCE LANGUAGE: {base_prompt}"
    )
    negative = f"{NEGATIVE_PROMPT}, identity drift between shots, wardrobe reset, damage reset, spatial discontinuity, inconsistent prop position"
    return instruction, negative


def create_storyboard(
    *,
    name: str,
    concept: str,
    genre: str = "action",
    visual_style: str = "photorealistic premium cinematic realism",
    aspect_ratio: str = "16:9",
    target_duration_seconds: int = 60,
    scene_count: int | None = None,
    owner: str = "local",
) -> Project:
    target_duration_seconds = max(10, min(int(target_duration_seconds), 3600))
    if scene_count is None:
        scene_count = max(1, min(12, math.ceil(target_duration_seconds / 60)))
    scene_count = max(1, min(int(scene_count), 24))
    project = Project(
        id=_uid("prj"),
        name=name.strip() or "Untitled zMovie",
        concept=concept.strip(),
        genre=genre,
        visual_style=visual_style,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=target_duration_seconds,
        owner=owner,
    )
    # A useful default lead makes the generated project immediately renderable while remaining editable.
    project.characters.append(
        CharacterBible(
            id=_uid("char"),
            name="Lead",
            role="protagonist",
            appearance="distinctive face with stable eye color, facial proportions, age, skin texture, and natural makeup",
            hair="consistent hairstyle and color across every scene",
            wardrobe="scene-appropriate signature wardrobe with exact color and material continuity inside each sequence",
            personality="calm, purposeful, emotionally readable",
            fighting_style="precise physically believable movement when action occurs",
            continuity_notes="Never change identity, body proportions, core wardrobe palette, or signature accessories without an explicit story transition.",
        )
    )
    beats = _sentences(concept)
    if not beats:
        beats = ["Establish the protagonist and central objective", "Escalate the conflict", "Resolve with a strong final image"]
    scene_duration = max(10, math.ceil(target_duration_seconds / scene_count))
    shot_duration = 20 if scene_duration >= 20 else 10
    for i in range(scene_count):
        beat = beats[min(i, len(beats) - 1)]
        scene = Scene(
            id=_uid("scn"),
            project_id=project.id,
            order_index=i + 1,
            title=f"Scene {i + 1}",
            summary=beat,
            location="cinematic environment derived from the concept",
            time_of_day="night" if genre.lower() in {"action", "thriller", "noir"} else "day",
            mood="escalating cinematic tension" if i < scene_count - 1 else "decisive cinematic resolution",
            continuity_notes="Preserve character identity, wardrobe state, props, injuries, environmental damage, lighting direction, and screen geography from the prior scene when temporally continuous.",
        )
        shots_per_scene = max(1, math.ceil(scene_duration / shot_duration))
        for j in range(shots_per_scene):
            order = j + 1
            if order == 1:
                summary = f"Establish and advance this beat: {beat}"
            elif order == shots_per_scene:
                summary = f"Deliver the strongest escalation or payoff for: {beat}"
            else:
                summary = f"Develop the action, performance, and visual progression of: {beat}"
            shot = Shot(
                id=_uid("shot"),
                scene_id=scene.id,
                order_index=order,
                duration_seconds=shot_duration,
                summary=summary,
                continuity_in="Match the final character pose, screen direction, lighting, wardrobe, prop and damage state from the previous shot.",
                continuity_out="Finish on a readable pose and environment state designed for seamless continuation.",
            )
            shot.prompt, shot.negative_prompt = build_shot_prompt(project, scene, shot)
            scene.shots.append(shot)
        project.scenes.append(scene)
    return project


def regenerate_project_prompts(project: Project, seed: int | None = None) -> Project:
    for scene in project.scenes:
        for shot in scene.shots:
            local_seed = None if seed is None else seed + scene.order_index * 1000 + shot.order_index
            shot.prompt, shot.negative_prompt = build_shot_prompt(project, scene, shot, seed=local_seed)
    return project


def production_manifest(project: Project) -> dict[str, Any]:
    return {
        "schema": "zmovie.production-manifest/v1",
        "project": project.to_dict(),
        "render_order": [
            {
                "scene": scene.order_index,
                "shot": shot.order_index,
                "shot_id": shot.id,
                "duration_seconds": shot.duration_seconds,
                "provider": shot.provider,
                "prompt": shot.prompt,
                "negative_prompt": shot.negative_prompt,
            }
            for scene in project.scenes
            for shot in scene.shots
        ],
    }
