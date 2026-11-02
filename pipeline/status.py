"""STATUS.md dashboard generated from content folders + ledger."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import ledger as ledger_mod
from . import schema
from .config import CONTENT_DIR, STATUS_PATH


def content_folders(content_dir: Path | None = None) -> list[Path]:
    base = content_dir or CONTENT_DIR
    return sorted(p for p in base.iterdir() if p.is_dir() and schema.FOLDER_RE.match(p.name)) if base.is_dir() else []


def render(folders: list[Path], ledger: dict, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    lines = [
        "# Pipeline status",
        "",
        f"_Updated {now.strftime('%Y-%m-%d %H:%M')} UTC_",
        "",
        "| Folder | Title | Category | Valid | Upload | Privacy | Scheduled (UTC) | Link |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f in folders:
        errors = schema.validate_folder(f)
        title, category = "", ""
        if (f / "metadata.json").is_file():
            try:
                _, meta = schema.load(f)
                title, category = meta.get("title", ""), meta.get("category", "")
            except Exception:
                pass
        entry = ledger.get("videos", {}).get(f.name)
        valid = "yes" if not errors else f"NO ({len(errors)})"
        if entry:
            link = f"https://youtu.be/{entry['youtube_id']}"
            row = [f.name, title, category, valid, "uploaded", entry.get("privacy", ""), entry.get("publish_at") or "-", link]
        else:
            row = [f.name, title, category, valid, "pending", "-", "-", "-"]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in row) + " |")
    done = sum(1 for f in folders if f.name in ledger.get("videos", {}))
    lines += ["", f"**{done} of {len(folders)} videos uploaded.**", ""]
    return "\n".join(lines)


def write(path: Path | None = None) -> None:
    text = render(content_folders(), ledger_mod.load())
    (path or STATUS_PATH).write_text(text, encoding="utf-8")
