"""YouTube Data API v3 upload. Credentials come only from environment variables."""
from __future__ import annotations

import os
from pathlib import Path

TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def build_description(meta: dict, script: dict, cfg: dict) -> str:
    parts = [meta["description"].strip(), ""]
    if meta.get("sources"):
        parts.append("Sources:")
        parts += [f"- {s['title']}: {s['url']}" for s in meta["sources"]]
        parts.append("")
    if script["category"] == "stock-basics" and cfg["disclaimers"]["sebi"] not in meta["description"]:
        parts += [cfg["disclaimers"]["sebi"], ""]
    parts += [cfg["disclaimers"]["ai_voice"], "#Shorts"]
    return "\n".join(parts)


def build_body(meta: dict, script: dict, cfg: dict, decision: dict) -> dict:
    tags = list(dict.fromkeys(meta["tags"] + cfg["channel"].get("default_tags", [])))
    status = {
        "privacyStatus": decision["privacy"],
        "selfDeclaredMadeForKids": bool(cfg["channel"].get("made_for_kids", False)),
        "containsSyntheticMedia": True,  # AI generated voice-over: disclose honestly
    }
    if decision.get("publish_at"):
        status["publishAt"] = decision["publish_at"]  # requires privacyStatus == private
    return {
        "snippet": {
            "title": meta["title"],
            "description": build_description(meta, script, cfg),
            "tags": tags,
            "categoryId": str(cfg["channel"]["category_id"]),
            "defaultLanguage": "en",
            "defaultAudioLanguage": "ta",
        },
        "status": status,
    }


def _service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(video: Path, thumb: Path, body: dict, on_inserted=None) -> str:
    """Upload and return the YouTube video id. `on_inserted(video_id)` runs right after insert."""
    from googleapiclient.http import MediaFileUpload

    yt = _service()
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = req.next_chunk()
    video_id = response["id"]
    if on_inserted:
        on_inserted(video_id)
    try:
        yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumb), mimetype="image/jpeg")).execute()
    except Exception as e:  # custom thumbnails need a verified channel; not fatal
        print(f"warning: thumbnail not set: {type(e).__name__}")
    return video_id
