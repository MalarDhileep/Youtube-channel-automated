from datetime import datetime, timezone

import pytest
import yaml

from pipeline.config import CONFIG_PATH
from pipeline.publishing import decide, public_publishing_allowed

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


def cfg(enabled):
    return {"publishing": {"public_publishing_enabled": enabled, "publish_time_ist": "18:00"}}


@pytest.mark.parametrize("config_on", [True, False])
@pytest.mark.parametrize("env_val", ["yes", "no", "", "YES", "true", None])
def test_public_needs_both_switches(config_on, env_val):
    env = {} if env_val is None else {"PUBLIC_PUBLISHING_APPROVED": env_val}
    expected = config_on and env_val == "yes"
    assert public_publishing_allowed(cfg(config_on), env) is expected
    result = decide(cfg(config_on), env, "2026-11-03", now=NOW)
    assert result["privacy"] == "private"  # scheduled videos are uploaded private + publishAt
    assert (result["publish_at"] is not None) is expected


def test_default_repo_config_keeps_public_publishing_off():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["publishing"]["public_publishing_enabled"] is False
    assert config["publishing"]["publish_time_ist"] == "18:00"


def test_publish_at_is_1800_ist_in_utc():
    result = decide(cfg(True), {"PUBLIC_PUBLISHING_APPROVED": "yes"}, "2026-11-03", now=NOW)
    assert result["publish_at"] == "2026-11-03T12:30:00Z"


def test_passed_slot_stays_private_unscheduled():
    late = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc)
    result = decide(cfg(True), {"PUBLIC_PUBLISHING_APPROVED": "yes"}, "2026-11-03", now=late)
    assert result["privacy"] == "private" and result["publish_at"] is None
