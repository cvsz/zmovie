from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import edge_tts

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
DEFAULT_TTS_VOICE = "th-TH-PremwadeeNeural"
DEFAULT_TTS_RATE = "-20%"
DEFAULT_VOICE_START_SECONDS = 1.2
DEFAULT_MUSIC_GAIN = 0.04
DEFAULT_VOICEOVER = (
    "พบกับ ซีมูฟวี่ จาก ซีแซดเดฟ ระบบผลิตวิดีโอแบบเซลฟ์โฮสต์ "
    "ตั้งแต่ไอเดีย สตอรี่บอร์ด เรนเดอร์ ตรวจคุณภาพ และตัดต่อ "
    "ก่อนตรวจทาน อนุมัติ และเผยแพร่ผ่าน บิลิบิลิ ครีเอเตอร์ เซ็นเตอร์ "
    "สร้าง เรนเดอร์ เผยแพร่"
)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _font_path() -> str:
    fc_match = shutil.which("fc-match")
    if not fc_match:
        return ""
    proc = subprocess.run(
        [fc_match, "-f", "%{file}\n", "sans"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    candidate = (proc.stdout or "").splitlines()[0].strip() if proc.stdout else ""
    return candidate if candidate and Path(candidate).is_file() else ""


def _local_tts_engine() -> str:
    return shutil.which("espeak-ng") or shutil.which("espeak") or ""


async def _save_edge_tts(output: Path, text: str, voice_id: str) -> None:
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_id,
        rate=DEFAULT_TTS_RATE,
        pitch="+0Hz",
        volume="+0%",
    )
    await communicate.save(str(output))


def _edge_tts(output: Path, text: str, voice_id: str) -> bool:
    output.unlink(missing_ok=True)
    try:
        asyncio.run(_save_edge_tts(output, text, voice_id))
    except Exception:
        output.unlink(missing_ok=True)
        return False
    return output.is_file() and output.stat().st_size > 1024


def _local_tts(output: Path, text: str) -> tuple[bool, str]:
    engine = _local_tts_engine()
    if not engine:
        return False, ""
    proc = subprocess.run(
        [engine, "-v", "th", "-s", "128", "-p", "46", "-a", "180", "-w", str(output), text],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.returncode == 0 and output.is_file() and output.stat().st_size > 1024, Path(engine).name


def _render_voiceover(workdir: Path, text: str) -> dict[str, Any]:
    provider = os.getenv("ZMOVIE_TTS_PROVIDER", "edge").strip().lower()
    voice = os.getenv("ZMOVIE_TTS_VOICE", DEFAULT_TTS_VOICE).strip() or DEFAULT_TTS_VOICE
    allow_local = _env_bool("ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK", False)

    if provider not in {"edge", "auto", "local"}:
        raise RuntimeError(f"unsupported ZMOVIE_TTS_PROVIDER: {provider}")

    if provider in {"edge", "auto"}:
        edge_path = workdir / "voiceover.mp3"
        if _edge_tts(edge_path, text, voice):
            return {
                "generated": True,
                "provider": "edge-tts",
                "voice": voice,
                "language": "th-TH",
                "path": str(edge_path),
            }
        if provider == "edge" and not allow_local:
            raise RuntimeError(
                "Edge neural TTS failed through the maintained edge-tts client; production render stopped. "
                "Verify outbound HTTPS/DNS from the production runtime or explicitly opt into the local fallback with "
                "ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK=true."
            )

    if provider == "local" or allow_local:
        local_path = workdir / "voiceover.wav"
        generated, engine = _local_tts(local_path, text)
        if generated:
            return {
                "generated": True,
                "provider": engine,
                "voice": "th",
                "language": "th-TH",
                "path": str(local_path),
            }

    raise RuntimeError("No intelligible voice-over provider is available for production rendering")


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


def _probe_media(ffprobe: str, output: Path) -> dict[str, Any]:
    probe = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration,size",
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
    streams = data.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    fmt = data.get("format") or {}
    return {
        "codec": str(video.get("codec_name") or ""),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frame_rate": str(video.get("r_frame_rate") or ""),
        "duration_seconds": float(fmt.get("duration") or 0),
        "size_bytes": int(fmt.get("size") or output.stat().st_size),
        "audio_codec": str(audio.get("codec_name") or ""),
        "audio_sample_rate": int(audio.get("sample_rate") or 0),
        "audio_channels": int(audio.get("channels") or 0),
    }


def _render_launch_video(output: Path, *, duration: int = DEFAULT_DURATION) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg and ffprobe are required to create the launch candidate")

    duration = max(24, min(int(duration), 60))
    output.parent.mkdir(parents=True, exist_ok=True)
    font = _font_path()
    voice_delay_ms = max(0, round(DEFAULT_VOICE_START_SECONDS * 1000))

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

    soundtrack = (
        "aevalsrc=(0.75+0.25*sin(2*PI*0.25*t))*"
        "(0.050*sin(2*PI*110*t)+0.025*sin(2*PI*220*t)+0.018*sin(2*PI*329.63*t)+0.012*sin(2*PI*440*t))"
        f":s=48000:d={duration}"
    )

    with tempfile.TemporaryDirectory(prefix="zmovie-ad-audio-") as tmp:
        voiceover = _render_voiceover(Path(tmp), DEFAULT_VOICEOVER)
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
            soundtrack,
            "-i",
            voiceover["path"],
        ]

        filters = [
            f"[0:v]{','.join(vf)}[vout]",
            (
                "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                f"volume={DEFAULT_MUSIC_GAIN},afade=t=in:st=0:d=0.8,afade=t=out:st={max(duration - 1.2, 1)}:d=1.0[music]"
            ),
            (
                "[2:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                "highpass=f=80,lowpass=f=12000,acompressor=threshold=0.12:ratio=3:attack=5:release=80,"
                f"adelay={voice_delay_ms}|{voice_delay_ms},volume=1.75,apad=whole_dur={duration},"
                f"atrim=duration={duration},asplit=2[voice_sc][voice_mix]"
            ),
            "[music][voice_sc]sidechaincompress=threshold=0.012:ratio=14:attack=8:release=420[ducked]",
            "[ducked][voice_mix]amix=inputs=2:duration=longest:dropout_transition=2[mixed]",
            f"[mixed]loudnorm=I=-15:TP=-1.5:LRA=9,apad=whole_dur={duration},atrim=duration={duration}[aout]",
        ]

        command.extend(
            [
                "-filter_complex",
                ";".join(filters),
                "-map",
                "[vout]",
                "-map",
                "[aout]",
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
                "192k",
                "-ar",
                "48000",
                "-t",
                str(duration),
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
        proc = subprocess.run(command, capture_output=True, text=True, timeout=600, check=False)
        if proc.returncode != 0 or not output.is_file():
            raise RuntimeError(f"launch video render failed: {proc.stderr[-1600:]}")

        probe = _probe_media(ffprobe, output)
        if abs(float(probe["duration_seconds"]) - float(duration)) > 0.15:
            raise RuntimeError(
                f"launch video duration mismatch: expected {duration}s, got {probe['duration_seconds']:.3f}s"
            )
        probe.update(
            {
                "font_rendered": bool(font),
                "soundtrack_generated": True,
                "soundtrack_source": "ffmpeg_synth",
                "voiceover_generated": True,
                "voiceover_provider": str(voiceover["provider"]),
                "voiceover_voice": str(voiceover["voice"]),
                "voiceover_language": str(voiceover["language"]),
                "voiceover_text": DEFAULT_VOICEOVER,
                "tts_rate": DEFAULT_TTS_RATE,
                "voice_first_mix": True,
                "voice_start_seconds": DEFAULT_VOICE_START_SECONDS,
                "music_gain": DEFAULT_MUSIC_GAIN,
                "voice_gain": 1.75,
                "target_duration_seconds": duration,
                "duration_locked": True,
                "audio_mastering": "loudnorm I=-15 TP=-1.5 LRA=9",
            }
        )
        return probe


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
            "Real managed full-ad publication candidate with Thai neural voice-over and voice-first mastering. "
            "Visuals use local FFmpeg motion graphics, not an AI-model video render. Review campaign wording, preview, "
            "audio, and publication metadata before approval."
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
