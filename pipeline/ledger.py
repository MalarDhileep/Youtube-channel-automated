"""Upload ledger: guarantees a video is never uploaded twice."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import LEDGER_PATH


def load(path: Path | None = None) -> dict:
    path = path or LEDGER_PATH
    if not path.is_file():
        return {"videos": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save(ledger: dict, path: Path | None = None) -> None:
    path = path or LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_uploaded(ledger: dict, video_id: str) -> bool:
    return video_id in ledger.get("videos", {})


def record(ledger: dict, video_id: str, entry: dict, path: Path | None = None) -> None:
    """Add an entry and persist immediately so a crash cannot lose it."""
    if is_uploaded(ledger, video_id):
        raise ValueError(f"{video_id} is already in the ledger; refusing to overwrite")
    ledger.setdefault("videos", {})[video_id] = entry
    save(ledger, path)


def content_hash(folder: Path) -> str:
    h = hashlib.sha256()
    for name in ("script.json", "metadata.json"):
        h.update((Path(folder) / name).read_bytes())
    return h.hexdigest()[:16]
