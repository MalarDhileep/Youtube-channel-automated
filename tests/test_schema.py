import copy
from pathlib import Path

from pipeline import schema

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "content" / "2026-11-03-a"


def load_example():
    script, meta = schema.load(EXAMPLE)
    return copy.deepcopy(script), copy.deepcopy(meta)


def errors_for(script, meta, name="2026-11-03-a"):
    return schema.validate_data(name, script, meta)


def test_example_is_valid():
    assert schema.validate_folder(EXAMPLE) == []


def test_on_screen_text_must_be_english():
    script, meta = load_example()
    script["scenes"][0]["on_screen_text"] = "படிக்க நிறைய"
    assert any("must be English" in e for e in errors_for(script, meta))


def test_narration_must_be_tamil():
    script, meta = load_example()
    script["scenes"][0]["narration_ta"] = "English only narration"
    assert any("must be Tamil" in e for e in errors_for(script, meta))


def test_duration_sum_must_fit_shorts_window():
    script, meta = load_example()
    script["scenes"][0]["duration_sec"] = 15
    script["scenes"][1]["duration_sec"] = 15
    assert any("sum of duration_sec" in e for e in errors_for(script, meta))


def test_sources_required():
    script, meta = load_example()
    meta["sources"] = []
    assert any("source" in e for e in errors_for(script, meta))


def test_advice_wording_rejected():
    script, meta = load_example()
    script["scenes"][1]["on_screen_text"] = "Buy this stock now"
    assert any("education-only" in e for e in errors_for(script, meta))


def test_clickbait_title_rejected():
    script, meta = load_example()
    meta["title"] = "Guaranteed results with AI"
    assert any("clickbait" in e for e in errors_for(script, meta))


def test_stock_basics_needs_sebi_disclaimer():
    script, meta = load_example()
    script["category"] = meta["category"] = "stock-basics"
    errs = errors_for(script, meta)
    assert any("SEBI" in e for e in errs)

    script["scenes"][-1]["on_screen_text"] = "Education only. Not SEBI advice."
    meta["description"] += "\nNot investment advice. Not a SEBI registered advisor."
    assert errors_for(script, meta) == []


def test_folder_name_must_match_id():
    script, meta = load_example()
    assert any("folder name" in e for e in errors_for(script, meta, name="bad-name"))
