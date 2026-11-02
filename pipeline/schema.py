"""Validation of a content folder (script.json + metadata.json)."""
from __future__ import annotations

import json
import re
from pathlib import Path

CATEGORIES = {"ai-tools", "ai-learning", "stock-basics"}
TAMIL_RE = re.compile(r"[஀-௿]")
FOLDER_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z])$")
URL_RE = re.compile(r"^https?://\S+$")

# Education-only: no advice, no hype, no clickbait promises.
ADVICE_RE = re.compile(
    r"\b(buy|sell|target price|stop[- ]?loss|multibagger|guaranteed|"
    r"sure[- ]?shot|risk[- ]?free|double your money|get rich)\b",
    re.I,
)
CLICKBAIT_RE = re.compile(r"(guaranteed|100%|you won't believe|shocking|secret trick)", re.I)

MIN_SCENES, MAX_SCENES = 5, 10
MIN_EST, MAX_EST = 45, 60
TITLE_MAX = 90


def folder_date(folder: Path) -> str:
    m = FOLDER_RE.match(Path(folder).name)
    return m.group(1) if m else ""


def load(folder: Path) -> tuple[dict, dict]:
    folder = Path(folder)
    script = json.loads((folder / "script.json").read_text(encoding="utf-8"))
    meta = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    return script, meta


def _english_text(script: dict, meta: dict) -> list[str]:
    texts = [meta.get("title", ""), meta.get("description", ""), (meta.get("thumbnail") or {}).get("text", "")]
    texts += [s.get("on_screen_text", "") for s in script.get("scenes", [])]
    return texts


def validate_data(folder_name: str, script: dict, meta: dict) -> list[str]:
    """Return a list of error strings (empty = valid)."""
    errors: list[str] = []
    m = FOLDER_RE.match(folder_name)
    if not m:
        errors.append(f"folder name '{folder_name}' must look like YYYY-MM-DD-a")

    for key in ("id", "category", "scenes"):
        if key not in script:
            errors.append(f"script.json missing '{key}'")
    for key in ("title", "description", "tags", "category", "sources", "thumbnail"):
        if key not in meta:
            errors.append(f"metadata.json missing '{key}'")
    if errors:
        return errors

    if m and script["id"] != folder_name:
        errors.append(f"script id '{script['id']}' != folder name '{folder_name}'")
    if script["category"] not in CATEGORIES:
        errors.append(f"category must be one of {sorted(CATEGORIES)}")
    if meta["category"] != script["category"]:
        errors.append("metadata category differs from script category")

    title = meta["title"]
    if not title or len(title) > TITLE_MAX:
        errors.append(f"title must be 1-{TITLE_MAX} chars")
    if TAMIL_RE.search(title):
        errors.append("title must be English")
    if CLICKBAIT_RE.search(title):
        errors.append("title looks like clickbait / makes guarantees")
    if not isinstance(meta["tags"], list) or not meta["tags"]:
        errors.append("tags must be a non-empty list")
    elif sum(len(t) for t in meta["tags"]) > 450:
        errors.append("tags exceed 450 characters in total")

    sources = meta["sources"]
    if not isinstance(sources, list) or not sources:
        errors.append("at least one source is required (never invent facts)")
    else:
        for i, s in enumerate(sources):
            if not (isinstance(s, dict) and s.get("title") and URL_RE.match(str(s.get("url", "")))):
                errors.append(f"sources[{i}] needs 'title' and an http(s) 'url'")

    thumb = meta["thumbnail"]
    if not (isinstance(thumb, dict) and thumb.get("text")):
        errors.append("thumbnail.text is required")
    else:
        if len(thumb["text"]) > 40:
            errors.append("thumbnail.text must be <= 40 chars")
        if TAMIL_RE.search(thumb["text"]):
            errors.append("thumbnail text must be English")

    scenes = script["scenes"]
    if not isinstance(scenes, list) or not (MIN_SCENES <= len(scenes) <= MAX_SCENES):
        errors.append(f"need {MIN_SCENES}-{MAX_SCENES} scenes")
        return errors

    total = 0.0
    for i, sc in enumerate(scenes, 1):
        where = f"scene {i}"
        narr, text = sc.get("narration_ta", ""), sc.get("on_screen_text", "")
        dur = sc.get("duration_sec")
        if not narr or not TAMIL_RE.search(narr):
            errors.append(f"{where}: narration_ta must be Tamil text")
        if not text:
            errors.append(f"{where}: on_screen_text is required")
        elif TAMIL_RE.search(text):
            errors.append(f"{where}: on_screen_text must be English")
        elif len(text) > 90:
            errors.append(f"{where}: on_screen_text must be <= 90 chars")
        if not isinstance(dur, (int, float)) or isinstance(dur, bool) or not (2 <= dur <= 15):
            errors.append(f"{where}: duration_sec must be a number between 2 and 15")
        else:
            total += dur
    if not (MIN_EST <= total <= MAX_EST):
        errors.append(f"sum of duration_sec is {total:g}; must be {MIN_EST}-{MAX_EST}")

    if ADVICE_RE.search(" ".join(_english_text(script, meta))):
        errors.append("contains buy/sell advice or hype wording; content must be education-only")

    if script["category"] == "stock-basics":
        if "SEBI" not in scenes[-1].get("on_screen_text", ""):
            errors.append("stock-basics: last scene on_screen_text must contain the SEBI disclaimer")
        if "SEBI" not in meta["description"]:
            errors.append("stock-basics: description must contain the SEBI disclaimer")
    return errors


def validate_folder(folder: Path) -> list[str]:
    folder = Path(folder)
    for name in ("script.json", "metadata.json"):
        if not (folder / name).is_file():
            return [f"{folder}: missing {name}"]
    try:
        script, meta = load(folder)
    except json.JSONDecodeError as e:
        return [f"{folder}: invalid JSON: {e}"]
    return validate_data(folder.name, script, meta)
