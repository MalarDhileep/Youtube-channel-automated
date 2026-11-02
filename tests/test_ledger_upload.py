from pathlib import Path

import pytest

from pipeline import ledger, schema
from pipeline import run as run_mod
from pipeline import upload as up
from pipeline.config import load_config

EXAMPLE = Path(__file__).resolve().parent.parent / "content" / "2026-11-03-a"


def test_ledger_refuses_second_record(tmp_path):
    path = tmp_path / "ledger.json"
    led = ledger.load(path)
    ledger.record(led, "2026-11-03-a", {"youtube_id": "abc"}, path)
    assert ledger.is_uploaded(ledger.load(path), "2026-11-03-a")
    with pytest.raises(ValueError):
        ledger.record(led, "2026-11-03-a", {"youtube_id": "def"}, path)


def test_run_upload_skips_when_in_ledger(monkeypatch):
    called = []
    monkeypatch.setattr(up, "upload_video", lambda *a, **k: called.append(1) or "x")
    led = {"videos": {"2026-11-03-a": {"youtube_id": "abc"}}}
    run_mod.upload(EXAMPLE, load_config(), Path("v.mp4"), Path("t.jpg"), led)
    assert called == []


def test_run_upload_records_in_ledger_and_defaults_private(monkeypatch, tmp_path):
    monkeypatch.delenv("PUBLIC_PUBLISHING_APPROVED", raising=False)
    monkeypatch.setattr(ledger, "LEDGER_PATH", tmp_path / "ledger.json")
    seen = {}

    def fake_upload(video, thumb, body, on_inserted=None):
        seen["body"] = body
        on_inserted("vid123")
        return "vid123"

    monkeypatch.setattr(up, "upload_video", fake_upload)
    led = {"videos": {}}
    run_mod.upload(EXAMPLE, load_config(), Path("v.mp4"), Path("t.jpg"), led)
    assert seen["body"]["status"]["privacyStatus"] == "private"
    assert "publishAt" not in seen["body"]["status"]
    assert led["videos"]["2026-11-03-a"]["youtube_id"] == "vid123"


def test_body_discloses_synthetic_voice_and_includes_sources():
    script, meta = schema.load(EXAMPLE)
    body = up.build_body(meta, script, load_config(), {"privacy": "private", "publish_at": "2026-11-03T12:30:00Z"})
    assert body["status"]["containsSyntheticMedia"] is True
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == "2026-11-03T12:30:00Z"
    assert "https://notebook.google/" in body["snippet"]["description"]
    assert "#Shorts" in body["snippet"]["description"]
