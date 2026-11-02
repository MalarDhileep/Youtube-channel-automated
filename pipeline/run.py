"""CLI: python -m pipeline.run <validate|build|upload|produce|status> ..."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from . import ledger as ledger_mod
from . import schema, status
from .config import BUILD_DIR, CONTENT_DIR, load_config
from .publishing import IST, decide


def today_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def cmd_validate(folders: list[Path]) -> int:
    if not folders:
        folders = status.content_folders()
    bad = 0
    for f in folders:
        errors = schema.validate_folder(f)
        if errors:
            bad += 1
            print(f"FAIL {f.name}")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"ok   {f.name}")
    return 1 if bad else 0


def build(folder: Path, cfg: dict) -> tuple[Path, Path]:
    """Voice, cards, clips, final video, thumbnail, QA. Returns (video, thumbnail)."""
    from . import cards, qa, video, voice

    script, meta = schema.load(folder)
    out = BUILD_DIR / folder.name
    out.mkdir(parents=True, exist_ok=True)
    scenes = script["scenes"]

    audio = voice.synthesize_scenes(scenes, cfg, out / "audio")
    footer = cfg["disclaimers"]["sebi"] if script["category"] == "stock-basics" else ""
    clips = []
    for i, (sc, a) in enumerate(zip(scenes, audio), 1):
        card = out / "cards" / f"scene_{i:02d}.png"
        cards.render_card(sc, i, len(scenes), script["category"], cfg, card, footer)
        clip = out / "clips" / f"scene_{i:02d}.mp4"
        clip.parent.mkdir(exist_ok=True)
        video.scene_clip(card, a, clip, cfg, i)
        clips.append(clip)
    final = out / "clips" / "video.mp4"
    video.concat(clips, final)

    thumb = out / "thumbnail.jpg"
    cards.render_thumbnail(meta["thumbnail"]["text"], script["category"], cfg["channel"]["name"], thumb)

    errors = qa.check_outputs(final, thumb, cfg)
    if errors:
        raise RuntimeError("QA failed: " + "; ".join(errors))
    return final, thumb


def upload(folder: Path, cfg: dict, video_path: Path, thumb: Path, led: dict) -> None:
    from . import upload as up

    if ledger_mod.is_uploaded(led, folder.name):
        print(f"skip {folder.name}: already in ledger")
        return
    script, meta = schema.load(folder)
    decision = decide(cfg, os.environ, schema.folder_date(folder))
    print(f"{folder.name}: privacy={decision['privacy']} ({decision['reason']})")
    body = up.build_body(meta, script, cfg, decision)

    def remember(video_id: str) -> None:
        ledger_mod.record(led, folder.name, {
            "youtube_id": video_id,
            "privacy": decision["privacy"],
            "publish_at": decision["publish_at"],
            "content_hash": ledger_mod.content_hash(folder),
            "uploaded_at": datetime.now(IST).isoformat(timespec="seconds"),
        })

    video_id = up.upload_video(video_path, thumb, body, on_inserted=remember)
    print(f"uploaded {folder.name} -> https://youtu.be/{video_id}")


def select_folders(date: str | None, pending: bool, led: dict) -> list[Path]:
    folders = status.content_folders()
    if date:
        return [f for f in folders if schema.folder_date(f) == date]
    if pending:
        today = today_ist()
        return [f for f in folders if schema.folder_date(f) <= today and not ledger_mod.is_uploaded(led, f.name)]
    return []


def cmd_produce(date: str | None, pending: bool, dry_run: bool) -> int:
    cfg = load_config()
    led = ledger_mod.load()
    folders = select_folders(date, pending, led)
    if not folders:
        print("nothing to produce")
    failed = 0
    for f in folders:
        if ledger_mod.is_uploaded(led, f.name):
            print(f"skip {f.name}: already uploaded")
            continue
        try:
            errors = schema.validate_folder(f)
            if errors:
                raise RuntimeError("validation failed: " + "; ".join(errors))
            video_path, thumb = build(f, cfg)
            if dry_run:
                print(f"dry run: built {video_path}, not uploading")
            else:
                upload(f, cfg, video_path, thumb, led)
        except Exception as e:
            failed += 1
            print(f"ERROR {f.name}: {e}", file=sys.stderr)
    status.write()
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pipeline.run")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="validate content folders (default: all)")
    v.add_argument("folders", nargs="*", type=Path)
    b = sub.add_parser("build", help="build video + thumbnail for one folder (no upload)")
    b.add_argument("folder", type=Path)
    pr = sub.add_parser("produce", help="validate, build and upload")
    pr.add_argument("--date", help="YYYY-MM-DD: produce every folder of that date")
    pr.add_argument("--pending", action="store_true", help="produce folders dated today (IST) or earlier not yet uploaded")
    pr.add_argument("--dry-run", action="store_true", help="build but do not upload")
    sub.add_parser("status", help="regenerate STATUS.md")
    args = p.parse_args(argv)

    if args.cmd == "validate":
        return cmd_validate(args.folders)
    if args.cmd == "build":
        errors = schema.validate_folder(args.folder)
        if errors:
            print("\n".join(errors))
            return 1
        print(build(args.folder, load_config())[0])
        return 0
    if args.cmd == "produce":
        if not (args.date or args.pending):
            p.error("produce needs --date or --pending")
        return cmd_produce(args.date, args.pending, args.dry_run)
    status.write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
