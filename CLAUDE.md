# Runbook: daily content task for "Learn Everything"

Channel: practical AI tools and AI learning tips for students and working professionals, plus
education-only stock-market basics. Voice-over: Tamil (ta-IN). All on-screen text, titles,
descriptions and thumbnail text: English. Format: vertical 1080x1920 Shorts, 45-60 seconds.

A scheduled Claude task runs this once a day. The GitHub Actions pipeline (`.github/workflows/produce.yml`)
then builds and uploads the videos. You only write content and push it.

## Daily steps

1. **Pick the date.** Write for tomorrow in IST (`D`). Create `content/D-a/` and `content/D-b/`.
   If `content/PLAN.md` has topics for `D`, use them; otherwise choose from the plan's categories.
2. **Research.** Use web search/fetch to read the official page, docs or announcement for each topic.
   Check that the tool/feature still exists under that name today. Names and features change.
3. **Write each Short** as two files in its folder:
   - `script.json`: `id` (= folder name), `date`, `category`, `language: "ta-IN"`, and 5-10 `scenes`.
     Each scene has `narration_ta` (Tamil), `on_screen_text` (English, at most 90 characters)
     and `duration_sec` (2-15). The `duration_sec` values must sum to 45-60.
   - `metadata.json`: `title` (English, at most 90 characters), `description`, `tags`, `category`,
     `sources` (at least one `{title, url}` you actually read) and `thumbnail.text` (English, at most 40 characters).
   - See `content/2026-11-03-a/` for a complete example.
   - Structure: a hook in scene 1, one idea per scene, a practical takeaway, a short close.
     Keep Tamil narration to roughly 12-18 words per 6-7 second scene.
4. **Validate.** Run `python -m pipeline.run validate content/D-a content/D-b` and fix every error.
   Run `python -m pytest -q` if you touched anything under `pipeline/`.
5. **Commit and push to `main`** (message: `content: D shorts a and b`). Add only `content/` files.
   Pushing content does not publish anything on its own. See "What happens after you push".

## Rules (non-negotiable)

- **Never invent facts.** Every claim must be supported by a source you read this session and listed in
  `metadata.json` `sources`. If you cannot verify something, leave it out or word it as general
  ("AI can make mistakes"). Never invent statistics, prices, quotes, release dates or feature lists.
- **No misleading titles or thumbnails.** The title and thumbnail must describe what the video delivers. No
  guarantees, no "shocking", no "secret", no fake urgency, no results promised.
- **Stock-market content is education only.** Explain concepts (what an index is, what a mutual fund NAV
  means, why diversification exists). Never say to buy, sell or hold anything, never name price targets, never
  predict markets, never present a specific stock as a good or bad choice. The last scene's on-screen text and
  the description must contain a SEBI disclaimer, for example:
  "Education only. Not investment advice. I am not a SEBI registered advisor."
- **AI voice is disclosed** automatically by the uploader (`containsSyntheticMedia`). Don't remove it.
- **Don't copy** text, images or scripts from other creators or sites. Write original wording.
- **Never edit the `publishing` section of `config/channel.yaml`.** Only the channel owner changes it.
  Don't change the `PUBLIC_PUBLISHING_APPROVED` repo variable either.
- **Never write secrets** (OAuth client ID/secret, refresh tokens, API keys) into any file, commit or log.
- Don't edit `state/ledger.json` or `STATUS.md` by hand. The pipeline owns them.
- Don't re-create or modify a folder that is already in `state/ledger.json` (already uploaded).

## What happens after you push

- `produce.yml` runs on pushes to `content/**`, daily at 00:05 IST, and manually.
- Pushes and the daily run process content dated today (IST) or earlier that is not yet in the ledger.
  Content dated in the future waits for its day, or for a manual run with that date.
- Videos upload **private** by default. They are scheduled public at `publish_time_ist` only when BOTH
  `publishing.public_publishing_enabled: true` in `config/channel.yaml` AND the repo variable
  `PUBLIC_PUBLISHING_APPROVED` is `yes`.
- The workflow commits `state/ledger.json` and `STATUS.md` back to `main`. Pull before you push.

## Commands

```
python -m pipeline.run validate [folders...]     # schema + policy checks (default: all content)
python -m pipeline.run build content/D-a         # voice, video, thumbnail, QA (needs ffmpeg)
python -m pipeline.run produce --date D --dry-run
python -m pipeline.run status                    # regenerate STATUS.md
python -m pytest -q
```
