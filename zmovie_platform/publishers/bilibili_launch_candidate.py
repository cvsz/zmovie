from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
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
DEFAULT_TTS_VOICE = "en-US-AriaNeural"
DEFAULT_VOICEOVER = (
    "Meet zMovie by ZeaZDev. From concept and storyboarding to rendering, quality control, and FFmpeg assembly, "
    "zMovie keeps your creator production workflow self-hosted and under control. Review, approve, and publish "
    "through Bilibili Creator Center. Create. Render. Publish. zMovie by ZeaZDev."
)
EDGE_TRANSLATOR_URL = "https://www.bing.com/translator"
EDGE_TTS_URL = "https://www.bing.com/tfettts?isVertical=1&&IG=1&IID=translator.5023&SFX=1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
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


def _local_tts_engine() -> str:
    return shutil.which("espeak-ng") or shutil.which("espeak") or ""


def _edge_token() -> tuple[str, str, str]:
    request = urllib.request.Request(
        EDGE_TRANSLATOR_URL,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        cookies = [value.split(";", 1)[0] for value in (response.headers.get_all("Set-Cookie") or [])]
        page = response.read().decode("utf-8", errors="replace")
    match = re.search(r"params_AbusePreventionHelper\s*=\s*\[([^,]+),([^,]+),", page)
    if not match:
        raise RuntimeError("Edge TTS token could not be parsed")
    key = match.group(1).strip().strip("\"'")
    token = match.group(2).strip().strip("\"'")
    return key, token, "; ".join(cookies)


def _edge_tts(output: Path, text: str, voice_id: str) -> bool:
    for attempt in range(2):
        try:
            key, token, cookie = _edge_token()
            parts = voice_id.split("-")
            xml_lang = "-".join(parts[:2]) if len(parts) >= 2 else "en-US"
            escaped_text = html.escape(text, quote=True)
            ssml = (
                f"<speak version='1.0' xml:lang='{xml_lang}'>"
                f"<voice xml:lang='{xml_lang}' name='{html.escape(voice_id, quote=True)}'>"
                f"<prosody rate='0.00%'>{escaped_text}</prosody></voice></speak>"
            )
            body = urllib.parse.urlencode({"ssml": ssml, "token": token, "key": key}).encode("utf-8")
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "*/*",
                "Origin": "https://www.bing.com",
                "Referer": EDGE_TRANSLATOR_URL,
                "User-Agent": USER_AGENT,
            }
            if cookie:
                headers["Cookie"] = cookie
            request = urllib.request.Request(EDGE_TTS_URL, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            if len(payload) < 1024:
                raise RuntimeError("Edge TTS returned empty audio")
            output.write_bytes(payload)
            return True
        except urllib.error.HTTPError as exc:
            if exc.code not in {403, 429} or attempt == 1:
                break
        except (OSError, RuntimeError, urllib.error.URLError):
            break
    return False


def _local_tts(output: Path, text: str) -> tuple[bool, str]:
    engine = _local_tts_engine()
    if not engine:
        return False, ""
    proc = subprocess.run(
        [engine, "-v", "en-us", "-s", "148", "-p", "46", "-a", "165", "-w", str(output), text],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proc.returncode == 0 and output.is_file() and output.stat().st_size > 1024, Path(engine).name


def _render_voiceover(workdir: Path, text: str) -> dict[str, Any]:
    provider = os.getenv("ZMOVIE_TTS_PROVIDER", "edge").strip().lower()
    voice = os.getenv("ZMOVIE_TTS_VOICE", DEFAULT_TTS_VOICE).strip() or DEFAULT_TTS_VOICE

    if provider in {"edge", "auto"}:
        edge_path = workdir / "voiceover.mp3"
        if _edge_tts(edge_path, text, voice):
            return {"generated": True, "provider": "edge-tts", "voice": voice, "path": str(edge_path)}
        if provider == "edge":
            provider = "local"

    if provider in {"local", "auto"}:
        local_path = workdir / "voiceover.wav"
        generated, engine = _local_tts(local_path, text)
        if generated:
            return {"generated": True, "provider": engine, "voice": "en-us", "path": str(local_path)}

    return {"generated": False, "provider": "none", "voice": "", "path": ""}


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
        ]
        if voiceover["generated"]:
            command.extend(["-i", voiceover["path"]])

        filters = [
            f"[0:v]{','.join(vf)}[vout]",
            "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"volume=0.18,afade=t=in:st=0:d=0.8,afade=t=out:st={max(duration - 1.2, 1)}:d=1.0[music]",
        ]
        if voiceover["generated"]:
            filters.extend(
                [
                    "[2:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                    "adelay=650|650,volume=1.15,asplit=2[voice_sc][voice_mix]",
                    "[music][voice_sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=300[ducked]",
                    "[ducked][voice_mix]amix=inputs=2:duration=first:dropout_transition=2,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
                ]
            )
        else:
            filters.append("[music]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")

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
                "160k",
                "-ar",
                "48000",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
        proc = subprocess.run(command, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0 or not output.is_file():
            raise RuntimeError(f"launch video render failed: {proc.stderr[-1600:]}")

        probe = _probe_media(ffprobe, output)
        probe.update(
            {
                "font_rendered": bool(font),
                "soundtrack_generated": True,
                "soundtrack_source": "ffmpeg_synth",
                "voiceover_generated": bool(voiceover["generated"]),
                "voiceover_provider": str(voiceover["provider"]),
                "voiceover_voice": str(voiceover["voice"]),
                "audio_mastering": "loudnorm I=-16 TP=-1.5 LRA=11",
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
            "Real managed full-ad publication candidate with generated soundtrack and voice-over where available. "
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
