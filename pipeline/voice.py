"""Tamil voice-over with edge-tts, one audio file per scene."""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


async def _synth(text: str, voice: str, rate: str, out: Path) -> None:
    import edge_tts

    await edge_tts.Communicate(text, voice, rate=rate).save(str(out))


def synthesize(text: str, voice: str, rate: str, out: Path) -> float:
    out.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synth(text, voice, rate, out))
    return audio_duration(out)


def _rate_str(percent: int) -> str:
    return f"{percent:+d}%"


def synthesize_scenes(scenes: list[dict], cfg: dict, out_dir: Path) -> list[Path]:
    """Synthesize every scene; speed up slightly if the total would exceed the max length."""
    voice = cfg["voice"]["name"]
    base = int(str(cfg["voice"].get("rate", "+0%")).rstrip("%"))
    cap = base + int(cfg["voice"].get("max_rate_boost_percent", 0))
    pad = cfg["video"]["scene_pad_seconds"]
    limit = cfg["video"]["max_seconds"]

    rate = base
    while True:
        paths, total = [], 0.0
        for i, sc in enumerate(scenes, 1):
            p = out_dir / f"scene_{i:02d}.mp3"
            total += synthesize(sc["narration_ta"], voice, _rate_str(rate), p) + pad
            paths.append(p)
        if total <= limit or rate >= cap:
            return paths
        rate = min(cap, rate + max(5, int((total / limit - 1) * 100) + 2))
