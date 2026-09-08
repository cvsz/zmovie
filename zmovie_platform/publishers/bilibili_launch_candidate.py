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

DEFAULT_NAME = "ZeaZDev × Bilibili — Full Ads Production"
DEFAULT_CONCEPT = (
    "A full-length creator-publishing advertisement for zMovie by ZeaZDev, presented as a ZeaZDev × Bilibili "
    "campaign creative. It highlights concept development, storyboarding, rendering, QC, FFmpeg assembly, "
    "controlled approval, and publishing through Bilibili Creator Center. Campaign branding does not imply "
    "an official partnership, sponsorship, or endorsement by Bilibili."
)
DEFAULT_DURATION = 30


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
        .replace(",", r"\,")
    )


def _drawtext(
    font_expr: str,
    text: str,
    *,
    fontsize: int,
    y: str,
    start: float,
    end: float,
) -> str:
    return (
        "drawtext="
        f"fontfile='{font_expr}':"
        f"text='{_escape_drawtext(text)}':"
        f"fontsize={fontsize}:fontcolor=white:"
        "x=(w-text_w)/2:"
        f"y={y}:"
        "shadowcolor=black@0.75:shadowx=3:shadowy=3:"
        f"enable='between(t,{start},{end})'"
    )


def _render_launch_video(output: Path, *, duration: int = DEFAULT_DURATION) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe are required to create the launch candidate")

    duration = max(24, min(int(duration), 60))
    output.parent.mkdir(parents=True, exist_ok=True)
    font = _font_path()

    vf = [
        "scale=1280:720",
        "format=yuv420p",
        "boxblur=10:2",
        "eq=contrast=1.08:saturation=1.12",
        "fade=t=in:st=0:d=0.6",
        f"fade=t=out:st={max(duration - 1, 1)}:d=0.8",
    ]
    if font:
        font_expr = _escape_drawtext(font)
        # Timed advertising beats. Text is deliberately generated in-process so
        # the output remains deterministic and does not require third-party media.
        vf.extend(
            [
                _drawtext(font_expr, "ZeaZDev × Bilibili", fontsize=76, y="h*0.27", start=0.4, end=4.5),
                _drawtext(font_expr, "Full Ads Production", fontsize=40, y="h*0.46", start=0.7, end=4.5),
                _drawtext(font_expr, "Creator Publishing Campaign", fontsize=28, y="h*0.59", start=1.0, end=4.5),
                _drawtext(font_expr, "FROM IDEA TO STORYBOARD", fontsize=52, y="h*0.34", start=4.5, end=9.0),
                _drawtext(font_expr, "Concept • Character Bible • Shot Planning", fontsize=30, y="h*0.52", start=4.8, end=9.0),
                _drawtext(font_expr, "RENDER • QC • ASSEMBLE", fontsize=54, y="h*0.34", start=9.0, end=14.5),
                _drawtext(font_expr, "Deterministic workflow • FFmpeg delivery", fontsize=30, y="h*0.52", start=9.3, end=14.5),
                _drawtext(font_expr, "SELF-HOSTED CREATOR PIPELINE", fontsize=48, y="h*0.34", start=14.5, end=20.0),
                _drawtext(font_expr, "Private runtime • Managed assets • Production controls", fontsize=28, y="h*0.52", start=14.8, end=20.0),
                _drawtext(font_expr, "REVIEW • APPROVE • PUBLISH", fontsize=52, y="h*0.34", start=20.0, end=25.2),
                _drawtext(font_expr, "Controlled publishing through Bilibili Creator Center", fontsize=28, y="h*0.52", start=20.3, end=25.2),
                _drawtext(font_expr, "zMovie by ZeaZDev", fontsize=66, y="h*0.30", start=25.2, end=float(duration) - 0.3),
                _drawtext(font_expr, "zmovie.zeaz.dev", fontsize=34, y="h*0.50", start=25.4, end=float(duration) - 0.3),
                _drawtext(font_expr, "Create • Render • Publish", fontsize=28, y="h*0.61", start=25.6, end=float(duration) - 0.3),
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


def create_launch_candidate(
    *,
    name: str = DEFAULT_NAME,
    concept: str = DEFAULT_CONCEPT,
    duration: int = DEFAULT_DURATION,
) -> dict[str, Any]:
    duration = max(24, min(int(duration), 60))
    project = create_storyboard(
        name=name,
        concept=concept,
        genre="technology advertising",
        visual_style="premium cinematic technology advertisement with clean motion graphics and strong campaign typography",
        aspect_ratio="16:9",
        target_duration_seconds=duration,
        scene_count=1,
        owner="zmovie-production",
    )
    save_project(project)

    output = MEDIA_ROOT.expanduser().resolve() / project.id / "final.mp4"
    probe = _render_launch_video(output, duration=duration)
    asset = add_asset(
        project.id,
        "final",
        "ZeaZDev × Bilibili full ads production",
        str(output),
        {
            "source": "ffmpeg_launch_candidate",
            "production_candidate": True,
            "campaign": "ZeaZDev × Bilibili",
            "campaign_type": "creator_publishing_ad",
            "official_partnership_claimed": False,
            "ai_model_rendered": False,
            "disclosure": (
                "Advertising visual generated locally with FFmpeg motion graphics; not produced by an AI video model. "
                "ZeaZDev × Bilibili is campaign creative wording for publishing via Bilibili Creator Center and does not "
                "represent an official partnership, sponsorship, or endorsement."
            ),
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
            "Real managed full-ad publication candidate. Generated locally with FFmpeg motion graphics, not an AI-model "
            "video render. Review campaign wording, preview, and publication metadata before approval."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a real non-mock full-ad asset for controlled Bilibili publication")
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--concept", default=DEFAULT_CONCEPT)
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    args = parser.parse_args(argv)
    try:
        print(
            json.dumps(
                create_launch_candidate(name=args.name, concept=args.concept, duration=args.duration),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(f"Bilibili launch candidate error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
