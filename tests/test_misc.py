from datetime import datetime, timezone
from pathlib import Path

from pipeline import qa, schema, status
from pipeline.config import load_config

ROOT = Path(__file__).resolve().parent.parent


def info(w=1080, h=1920, duration=52.0, audio=True):
    streams = [{"codec_type": "video", "width": w, "height": h}]
    if audio:
        streams.append({"codec_type": "audio"})
    return {"streams": streams, "format": {"duration": str(duration)}}


def test_qa_accepts_good_video():
    assert qa.check_probe(info(), load_config(), 5_000_000) == []


def test_qa_rejects_bad_videos():
    cfg = load_config()
    assert qa.check_probe(info(w=1920, h=1080), cfg, 1)
    assert qa.check_probe(info(duration=30), cfg, 1)
    assert qa.check_probe(info(duration=75), cfg, 1)
    assert qa.check_probe(info(audio=False), cfg, 1)


def test_status_lists_uploaded_and_pending():
    folders = status.content_folders(ROOT / "content")
    now = datetime(2026, 11, 2, tzinfo=timezone.utc)
    pending = status.render(folders, {"videos": {}}, now)
    assert "2026-11-03-a" in pending and "pending" in pending
    done = status.render(folders, {"videos": {"2026-11-03-a": {"youtube_id": "abc", "privacy": "private"}}}, now)
    assert "https://youtu.be/abc" in done and "1 of 1" in done


def test_no_secrets_committed():
    markers = ["GOC" + "SPX-", ".apps.google" + "usercontent.com", "1/" + "/0"]
    skip = {".git", "build", "__pycache__", ".pytest_cache"}
    for p in ROOT.rglob("*"):
        if not p.is_file() or skip & set(p.parts) or p.suffix in {".png", ".jpg", ".mp4", ".mp3"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in markers:
            assert m not in text, f"possible secret marker {m!r} in {p}"
