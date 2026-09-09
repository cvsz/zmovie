from __future__ import annotations

import math
import random
from typing import Any

from .hyperframes import apply_hyperframes_template
from .qc import director_notes, inspect_project
from .repository import save_project
from .storyboard import create_storyboard, regenerate_project_prompts


def _clean(value: str, maximum: int) -> str:
    return " ".join(str(value or "").strip().split())[:maximum]


def _slug_title(topic: str, brand: str) -> str:
    core = _clean(topic, 140) or "Untitled Content"
    if brand:
        return _clean(f"{brand} — {core}", 200)
    return _clean(core[:1].upper() + core[1:], 200)


def _is_commercial(goal: str, genre: str) -> bool:
    value = f"{goal} {genre}".casefold()
    return any(token in value for token in ("sell", "sale", "conversion", "launch", "advert", "commercial", "promote", "campaign", "lead"))


def _scene_count(duration: int, requested: int | None) -> int:
    if requested is not None:
        return max(1, min(int(requested), 24))
    return max(3, min(8, math.ceil(max(10, duration) / 20)))


def build_content_blueprint(
    *,
    topic: str,
    audience: str = "general audience",
    goal: str = "engagement",
    tone: str = "cinematic, premium and clear",
    brand: str = "",
    call_to_action: str = "",
    genre: str = "commercial",
    target_duration_seconds: int = 60,
    scene_count: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    topic = _clean(topic, 5000)
    if len(topic) < 3:
        raise ValueError("content topic/brief must contain at least 3 characters")
    audience = _clean(audience, 300) or "general audience"
    goal = _clean(goal, 300) or "engagement"
    tone = _clean(tone, 300) or "cinematic, premium and clear"
    brand = _clean(brand, 200)
    call_to_action = _clean(call_to_action, 500)
    duration = max(10, min(int(target_duration_seconds), 3600))
    count = _scene_count(duration, scene_count)
    rng = random.Random(seed if seed is not None else f"{topic}|{audience}|{goal}|{tone}|{brand}|{duration}")

    commercial = _is_commercial(goal, genre)
    hook_openers = [
        "Open on an immediately readable visual hook that makes the core idea impossible to ignore",
        "Begin with a striking before-state or question that creates instant curiosity",
        "Start on the strongest visual contrast in the brief and establish the promise in seconds",
        "Lead with a premium hero image, then reveal the tension or opportunity behind it",
    ]
    hook = rng.choice(hook_openers)

    if commercial:
        templates = [
            ("Hook", f"{hook}: {topic}. Make it relevant to {audience}."),
            ("Need", f"Show the real problem, desire, or friction the audience recognizes before the solution appears. The production goal is {goal}."),
            ("Reveal", f"Introduce {brand or 'the featured solution'} as the clear turning point, using concrete visual proof rather than abstract claims."),
            ("Demonstration", "Demonstrate the strongest benefit or transformation in action with visual continuity and a clear cause-and-effect progression."),
            ("Proof", "Reinforce credibility with a memorable result, detail, comparison, or payoff that supports the central promise."),
            ("CTA", f"Resolve on a clean branded final image and direct next step: {call_to_action or 'invite the viewer to learn more or take the next relevant action'}."),
        ]
    else:
        templates = [
            ("Hook", f"{hook}: {topic}. Frame the opening for {audience}."),
            ("Setup", f"Establish the protagonist, environment, objective, and emotional stakes in a way that serves {goal}."),
            ("Escalation", "Introduce a visible complication and progressively raise the cost, urgency, or emotional pressure."),
            ("Turn", "Deliver a decisive reveal, reversal, discovery, or action beat that changes the direction of the story."),
            ("Climax", "Pay off the strongest visual and emotional promise with a coherent cinematic peak."),
            ("Resolution", f"End on a memorable final image with a clear takeaway{': ' + call_to_action if call_to_action else ''}."),
        ]

    beats: list[dict[str, str]] = []
    if count == 1:
        selected = [templates[0]]
    elif count >= len(templates):
        selected = templates + [templates[-2]] * (count - len(templates))
    else:
        indexes = [round(i * (len(templates) - 1) / (count - 1)) for i in range(count)]
        selected = [templates[index] for index in indexes]
    for index, (title, summary) in enumerate(selected, start=1):
        beats.append({"order": str(index), "title": title, "summary": summary})

    concept = " ".join(item["summary"] for item in beats)
    return {
        "title": _slug_title(topic, brand),
        "topic": topic,
        "audience": audience,
        "goal": goal,
        "tone": tone,
        "brand": brand,
        "call_to_action": call_to_action,
        "target_duration_seconds": duration,
        "scene_count": count,
        "hook": hook,
        "beats": beats,
        "concept": concept,
    }


def create_content_storyboard(
    *,
    topic: str,
    name: str = "",
    audience: str = "general audience",
    goal: str = "engagement",
    tone: str = "cinematic, premium and clear",
    brand: str = "",
    call_to_action: str = "",
    genre: str = "commercial",
    visual_style: str = "photorealistic premium cinematic realism",
    aspect_ratio: str = "16:9",
    target_duration_seconds: int = 60,
    scene_count: int | None = None,
    seed: int | None = None,
    owner: str = "local",
    template_id: str = "",
) -> dict[str, Any]:
    hyperframe: dict[str, Any] | None = None
    effective_topic = topic
    if str(template_id or "").strip():
        effective_topic, hyperframe = apply_hyperframes_template(topic, template_id)

    blueprint = build_content_blueprint(
        topic=effective_topic,
        audience=audience,
        goal=goal,
        tone=tone,
        brand=brand,
        call_to_action=call_to_action,
        genre=genre,
        target_duration_seconds=target_duration_seconds,
        scene_count=scene_count,
        seed=seed,
    )
    # Preserve the operator's raw brief separately so API/CLI consumers do not
    # have to strip the template guidance back out of the effective prompt.
    blueprint["raw_topic"] = _clean(topic, 5000)
    blueprint["hyperframes_template_id"] = str((hyperframe or {}).get("id") or "")

    project = create_storyboard(
        name=_clean(name, 200) or str(blueprint["title"]),
        concept=str(blueprint["concept"]),
        genre=_clean(genre, 80) or "commercial",
        visual_style=_clean(visual_style, 500) or "photorealistic premium cinematic realism",
        aspect_ratio=_clean(aspect_ratio, 20) or "16:9",
        target_duration_seconds=int(blueprint["target_duration_seconds"]),
        scene_count=int(blueprint["scene_count"]),
        owner=owner,
    )

    beats = list(blueprint["beats"])
    for index, scene in enumerate(project.scenes):
        beat = beats[min(index, len(beats) - 1)]
        scene.title = str(beat["title"])
        scene.summary = str(beat["summary"])
        scene.mood = f"{blueprint['tone']}; progression stage: {scene.title.casefold()}"
        shots = scene.shots
        for shot_index, shot in enumerate(shots):
            if len(shots) == 1:
                shot.summary = scene.summary
            elif shot_index == 0:
                shot.summary = f"Establish {scene.title.casefold()}: {scene.summary}"
            elif shot_index == len(shots) - 1:
                shot.summary = f"Pay off {scene.title.casefold()} and hand off cleanly to the next beat: {scene.summary}"
            else:
                shot.summary = f"Develop {scene.title.casefold()} with concrete action and visual proof: {scene.summary}"
    regenerate_project_prompts(project, seed=seed)
    save_project(project)
    return {
        "content": blueprint,
        "hyperframe": hyperframe,
        "project": project.to_dict(),
        "qc": inspect_project(project),
        "director_notes": director_notes(project),
    }
