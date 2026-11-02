"""Paths and config loading."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "channel.yaml"
CONTENT_DIR = ROOT / "content"
STATE_DIR = ROOT / "state"
LEDGER_PATH = STATE_DIR / "ledger.json"
STATUS_PATH = ROOT / "STATUS.md"
BUILD_DIR = ROOT / "build"


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)
