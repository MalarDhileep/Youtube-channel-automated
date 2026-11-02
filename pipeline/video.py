"""Assemble scene cards + voice-over into a vertical Short with FFmpeg."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .voice import audio_duration


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=cwd, capture_output=True, text=True)


def scene_clip(card: Path, audio: Path, out: Path, cfg: dict, index: int) -> float:
    """One animated clip: slow zoom (alternating in/out) with fades, length = voice + pad."""
    w, h, fps = cfg["video"]["width"], cfg["video"]["height"], cfg["video"]["fps"]
    dur = audio_duration(audio) + cfg["video"]["scene_pad_seconds"]
    zoom = "min(1+0.0006*on,1.12)" if index % 2 else "max(1.12-0.0006*on,1)"
    vf = (
        f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={fps},"
        f"fade=t=in:st=0:d=0.25,fade=t=out:st={dur - 0.25:.3f}:d=0.25,format=yuv420p"
    )
    _run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(card), "-i", str(audio),
        "-vf", vf, "-af", "apad,aresample=44100", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-crf", str(cfg["video"]["crf"]), "-preset", "medium", "-r", str(fps),
        "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "44100", str(out),
    ])
    return dur


def concat(clips: list[Path], out: Path) -> None:
    listing = out.parent / "clips.txt"
    listing.write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listing.name,
          "-c", "copy", "-movflags", "+faststart", str(out.resolve())], cwd=out.parent)
