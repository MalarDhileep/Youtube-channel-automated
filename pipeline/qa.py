"""Quality checks on the finished video and thumbnail."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

MAX_VIDEO_BYTES = 256 * 1024 * 1024
MAX_THUMB_BYTES = 2 * 1024 * 1024


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def check_probe(info: dict, cfg: dict, size_bytes: int) -> list[str]:
    """Pure check of ffprobe output; returns error strings."""
    errors: list[str] = []
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not video:
        return ["no video stream"]
    if (video.get("width"), video.get("height")) != (cfg["video"]["width"], cfg["video"]["height"]):
        errors.append(f"resolution is {video.get('width')}x{video.get('height')}, expected "
                      f"{cfg['video']['width']}x{cfg['video']['height']}")
    if not audio:
        errors.append("no audio stream (voice-over missing)")
    duration = float(info.get("format", {}).get("duration", 0))
    if not (cfg["video"]["min_seconds"] <= duration <= cfg["video"]["max_seconds"]):
        errors.append(f"duration {duration:.1f}s outside {cfg['video']['min_seconds']}-{cfg['video']['max_seconds']}s")
    if size_bytes > MAX_VIDEO_BYTES:
        errors.append("video larger than 256 MB")
    return errors


def check_outputs(video: Path, thumb: Path, cfg: dict) -> list[str]:
    errors: list[str] = []
    if not video.is_file():
        return ["video file missing"]
    errors += check_probe(probe(video), cfg, video.stat().st_size)
    if not thumb.is_file():
        errors.append("thumbnail missing")
    elif thumb.stat().st_size > MAX_THUMB_BYTES:
        errors.append("thumbnail larger than 2 MB")
    return errors
