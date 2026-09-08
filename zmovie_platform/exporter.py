from __future__ import annotations

import json
import zipfile
from pathlib import Path

from .models import Project
from .qc import director_notes, inspect_project
from .storyboard import production_manifest


def export_project(project: Project, root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    package_dir = root / project.id
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest = production_manifest(project)
    qc = inspect_project(project)
    notes = director_notes(project)
    (package_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "qc.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "director-notes.md").write_text("# Director Notes\n\n" + "\n".join(f"- {item}" for item in notes) + "\n", encoding="utf-8")
    prompts = []
    for scene in project.scenes:
        prompts.append(f"# Scene {scene.order_index}: {scene.title}\n")
        for shot in scene.shots:
            prompts.append(f"## Shot {shot.order_index} — {shot.duration_seconds}s\n\n{shot.prompt}\n\n### Negative Prompt\n\n{shot.negative_prompt}\n")
    (package_dir / "prompts.md").write_text("\n".join(prompts), encoding="utf-8")
    archive = root / f"{project.id}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in package_dir.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(package_dir))
    return archive
