"""Decides privacy / schedule for an upload.

Public publishing needs BOTH switches:
  1. config/channel.yaml  publishing.public_publishing_enabled == true
  2. env PUBLIC_PUBLISHING_APPROVED == "yes"  (repo variable in GitHub Actions)
Anything else uploads PRIVATE with no schedule.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping

IST = timezone(timedelta(hours=5, minutes=30))
MIN_LEAD = timedelta(minutes=15)


def public_publishing_allowed(config: dict, env: Mapping[str, str]) -> bool:
    cfg_on = (config.get("publishing") or {}).get("public_publishing_enabled") is True
    env_on = env.get("PUBLIC_PUBLISHING_APPROVED", "") == "yes"
    return cfg_on and env_on


def decide(config: dict, env: Mapping[str, str], video_date: str, now: datetime | None = None) -> dict:
    """Return {"privacy": "private", "publish_at": <RFC3339 UTC or None>, "reason": str}.

    YouTube schedules a video by uploading it private with status.publishAt set.
    """
    if not public_publishing_allowed(config, env):
        return {"privacy": "private", "publish_at": None, "reason": "public publishing not approved (needs both switches)"}

    now = now or datetime.now(timezone.utc)
    hh, mm = (config["publishing"]["publish_time_ist"]).split(":")
    y, mo, d = (int(x) for x in video_date.split("-"))
    when = datetime(y, mo, d, int(hh), int(mm), tzinfo=IST)
    if when - now < MIN_LEAD:
        return {"privacy": "private", "publish_at": None, "reason": f"publish slot {when.isoformat()} already passed; kept private"}
    publish_at = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"privacy": "private", "publish_at": publish_at, "reason": f"scheduled public at {when.isoformat()}"}
