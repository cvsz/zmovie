from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..repository import add_asset, save_project
from ..storyboard import create_storyboard

MEDIA_ROOT = Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"))

DEFAULT_NAME = "zMovie Launch — AI Movie Production Platform"
DEFAULT_CONCEPT = (
    "A concise launch visual introducing zMovie as a self-hosted movie-production platform, "
    "highlighting project planning, rendering workflows, assembly, and creator-platform publishing."
)


def _font_path() -> str:
    fc_match = shutil.which("fc-match")
    if not fc_match:
        return ""
    proc = subprocess.run(
        [fc_match, "-f", "%{file}\n", "sans"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if proc.returncode != 0:
        return ""
    candidate = (proc.stdout or "").splitlines()[0].strip() if proc.stdout else ""
    return candidate if candidate and Path(candidate).is_file() else ""


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
    )


def _render_launch_video(output: Path, *, duration: int = 18) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe are required to create the launch candidate")

    duration = max(10, min(int(duration), 60))
    output.parent.mkdir(parents=True, exist_ok=True)
    font = _font_path()

    vf = [
        "scale=1280:720",
        "format=yuv420p",
        "boxblur=12:2",
        "fade=t=in:st=0:d=0.8",
        f"fade=t=out:st={max(duration - 1, 1)}:d=0.8",
    ]
    if font:
        font_expr = _escape_drawtext(font)
        vf.extend(
            [
                "drawtext="
                f"fontfile='{font_expr}':"
                "text='zMovie':"
                "fontsize=82:fontcolor=white:"
                "x=(w-text_w)/2:y=h*0.31:"
                "shadowcolor=black@0.7:shadowx=3:shadowy=3",
                "drawtext="
                f"fontfile='{font_expr}':"
                "text='Self-hosted AI Movie Production Platform':"
                "fontsize=38:fontcolor=white:"
                "x=(w-text_w)/2:y=h*0.48:"
                "shadowcolor=black@0.7:shadowx=2:shadowy=2",
                "drawtext="
                f"fontfile='{font_expr}':"
                "text='zmovie.zeaz.dev':"
                "fontsize=32:fontcolor=white:"
                "x=(w-text_w)/2:y=h*0.62:"
                "shadowcolor=black@0.7:shadowx=2:shadowy=2",
            ]
        )

    command = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=1280x720:rate=24:duration={duration}",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=48000:cl=stereo:d={duration}",
        "-vf",
        ",".join(vf),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not output.is_file():
        raise RuntimeError(f"launch video render failed: {proc.stderr[-1200:]}")

    probe = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate:format=duration,size",
            "-of",
            "json",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    data = json.loads(probe.stdout or "{}")
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}
    return {
        "codec": str(stream.get("codec_name") or ""),
        "width": int(stream.get("width") or 0),
        "height": int(stream.get("height") or 0),
        "frame_rate": str(stream.get("r_frame_rate") or ""),
        "duration_seconds": float(fmt.get("duration") or 0),
        "size_bytes": int(fmt.get("size") or output.stat().st_size),
        "font_rendered": bool(font),
    }


def create_launch_candidate(*, name: str = DEFAULT_NAME, concept: str = DEFAULT_CONCEPT, duration: int = 18) -> dict[str, Any]:
    project = create_storyboard(
        name=name,
        concept=concept,
        genre="technology",
        visual_style="clean cinematic product-launch visual with restrained motion graphics",
        aspect_ratio="16:9",
        target_duration_seconds=max(10, min(int(duration), 60)),
        scene_count=1,
        owner="zmovie-production",
    )
    save_project(project)

    output = MEDIA_ROOT.expanduser().resolve() / project.id / "final.mp4"
    probe = _render_launch_video(output, duration=duration)
    asset = add_asset(
        project.id,
        "final",
        "zMovie launch movie",
        str(output),
        {
            "source": "ffmpeg_launch_candidate",
            "production_candidate": True,
            "ai_model_rendered": False,
            "disclosure": "Visual generated locally with FFmpeg motion graphics; not produced by an AI video model.",
            **probe,
        },
    )
    return {
        "status": "created",
        "project_id": project.id,
        "name": project.name,
        "concept": project.concept,
        "final_asset": asset,
        "media": probe,
        "publication_note": (
            "This is a real managed final asset intended for controlled publisher validation. "
            "It is FFmpeg-generated motion graphics, not an AI-model video render. Review before publication."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a real non-mock zMovie launch asset for controlled Bilibili publication")
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--concept", default=DEFAULT_CONCEPT)
    parser.add_argument("--duration", type=int, default=18)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(create_launch_candidate(name=args.name, concept=args.concept, duration=args.duration), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Bilibili launch candidate error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
