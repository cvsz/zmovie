from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Project, Scene, Shot


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    scene_id: str = ""
    shot_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "scene_id": self.scene_id,
            "shot_id": self.shot_id,
        }


REQUIRED_PROMPT_MARKERS = (
    "CONTINUITY",
    "CHARACTER BIBLE LOCK",
    "TARGET DURATION",
)


def inspect_shot(scene: Scene, shot: Shot) -> list[Finding]:
    findings: list[Finding] = []
    if shot.duration_seconds not in {5, 10, 20}:
        findings.append(Finding("warning", "duration.nonstandard", f"Shot duration {shot.duration_seconds}s is outside preferred 5/10/20-second provider presets.", scene.id, shot.id))
    if len(shot.prompt.strip()) < 300:
        findings.append(Finding("error", "prompt.too_short", "Prompt is too short for production continuity control.", scene.id, shot.id))
    upper = shot.prompt.upper()
    for marker in REQUIRED_PROMPT_MARKERS:
        if marker not in upper:
            findings.append(Finding("warning", "prompt.missing_lock", f"Prompt does not contain {marker}.", scene.id, shot.id))
    if not shot.negative_prompt.strip():
        findings.append(Finding("error", "negative.empty", "Negative prompt is empty.", scene.id, shot.id))
    if not shot.continuity_in.strip() or not shot.continuity_out.strip():
        findings.append(Finding("warning", "continuity.weak", "Shot should define both continuity-in and continuity-out state.", scene.id, shot.id))
    if not shot.summary.strip():
        findings.append(Finding("error", "shot.no_summary", "Shot summary is empty.", scene.id, shot.id))
    return findings


def inspect_project(project: Project) -> dict[str, Any]:
    findings: list[Finding] = []
    if not project.concept.strip():
        findings.append(Finding("error", "project.no_concept", "Project concept is empty."))
    if not project.characters:
        findings.append(Finding("warning", "project.no_characters", "Project has no character bible."))
    if not project.scenes:
        findings.append(Finding("error", "project.no_scenes", "Project has no scenes."))
    total_duration = 0
    shot_ids: set[str] = set()
    for scene in project.scenes:
        expected = 1
        for shot in sorted(scene.shots, key=lambda item: item.order_index):
            total_duration += shot.duration_seconds
            if shot.id in shot_ids:
                findings.append(Finding("error", "shot.duplicate_id", "Duplicate shot ID detected.", scene.id, shot.id))
            shot_ids.add(shot.id)
            if shot.order_index != expected:
                findings.append(Finding("warning", "shot.order_gap", f"Expected shot order {expected}, got {shot.order_index}.", scene.id, shot.id))
            expected += 1
            findings.extend(inspect_shot(scene, shot))
    if project.target_duration_seconds and abs(total_duration - project.target_duration_seconds) > max(20, project.target_duration_seconds * 0.25):
        findings.append(Finding("warning", "duration.project_mismatch", f"Storyboard totals {total_duration}s vs target {project.target_duration_seconds}s."))
    errors = sum(1 for item in findings if item.severity == "error")
    warnings = sum(1 for item in findings if item.severity == "warning")
    score = max(0, 100 - errors * 20 - warnings * 5)
    return {
        "score": score,
        "passed": errors == 0,
        "errors": errors,
        "warnings": warnings,
        "total_duration_seconds": total_duration,
        "findings": [item.to_dict() for item in findings],
    }


def director_notes(project: Project) -> list[str]:
    notes = [
        "Maintain motivated camera movement: every pan, orbit, dolly, and reframing should follow character intent or action geography.",
        "Protect screen direction and eyelines across adjacent shots unless a deliberate axis break is explicitly motivated.",
        "Carry wardrobe state, debris, injuries, prop positions, wetness, smoke, and lighting direction forward through temporally continuous scenes.",
        "Prioritize readable silhouette and contact frames over excessive camera shake during fast action.",
    ]
    if project.genre.lower() in {"action", "thriller"}:
        notes.append("Build action in escalation waves: anticipation → contact → recoil → recovery → larger environmental consequence → decisive payoff.")
    if "photoreal" in project.visual_style.lower():
        notes.append("Favor practical-light motivation, natural exposure rolloff, lens-consistent depth of field, plausible motion blur, and grounded surface response.")
    return notes
