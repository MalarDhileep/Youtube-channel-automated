# Learn Everything: automated YouTube Shorts

Practical AI tools and AI learning tips for students and working professionals, plus education-only
stock-market basics. Tamil voice-over, English on-screen text, 1080x1920 Shorts of 45-60 seconds.

- `CLAUDE.md`: runbook for the daily Claude task that writes content.
- `content/`: `PLAN.md` and one folder per Short (`script.json` + `metadata.json`).
- `pipeline/`: validate, Tamil voice (edge-tts), scene cards (Pillow), video (FFmpeg), QA, YouTube upload, ledger, status.
- `config/channel.yaml`: settings. The `publishing` section is owner-only.
- `.github/workflows/produce.yml`: builds and uploads. Private by default.
- `STATUS.md` / `state/ledger.json`: dashboard and the never-upload-twice ledger.

## Local use

```
pip install -r requirements.txt
python -m pytest -q
python -m pipeline.run validate content/2026-11-03-a
python -m pipeline.run build content/2026-11-03-a   # needs ffmpeg on PATH
```

## One-time setup

1. Create a Google Cloud OAuth client (Desktop app) with the YouTube Data API v3 enabled.
2. Run `python scripts/get_refresh_token.py` locally and copy the printed refresh token.
3. Add the repo secrets `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

## Going public (deliberately two switches)

Videos are uploaded **private**. They are scheduled public at `publish_time_ist` only when
`publishing.public_publishing_enabled: true` in `config/channel.yaml` **and** the repo variable
`PUBLIC_PUBLISHING_APPROVED` equals `yes`.
