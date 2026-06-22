# mind-clone — build a clone of how an author thinks

A self-contained [Claude Code](https://claude.com/claude-code) **skill** that builds a *cognitive model* of a real author/thinker from their public content, saves it as a local database in your project, and then answers questions, gives advice, and predicts positions **the way that person would think** — by reasoning through their actual mental models, not by imitating their tone.

> It's an interpretive model built from **public** sources — not the real person. Predictions are labeled and confidence-rated. Quotes are never fabricated.

## What it does

1. **Exhaustive discovery** — sweeps the web for everything public: articles, YouTube, podcasts, radio, talks, interviews, threads, papers — across name variants and affiliations.
2. **Source table** — shows you a reviewable table (`Date · Type · Source · Summary · URL`) before doing the heavy work, so you approve/prune what goes into the database.
3. **Harvest (extract-on-the-fly)** — reads each source once and saves the *distillate* (dated, attributed quotes/chunks), not gigabytes of raw text. Fast by default: existing text + captions/transcripts only, **no slow ASR**. Sources with no subtitles are listed in a table and you decide whether to run `whisper` on them. **Books** are processed chapter by chapter (from a copy you legally own, or public material about them — never pirated) and collapse into the same compact distillate. **Transcripts and article text are saved locally by default** (they're tiny — tens of MB even for a 300-video channel — and they power deep-links and live-grounding); only **full books** are the exception, kept just as distillate unless you opt in with `--archive-raw`.
4. **Cognitive model** — mines the corpus for the author's axioms, frameworks, causal belief graph, decision heuristics, antipatterns, and reconstructed reasoning traces.
5. **Playbook** (when the author teaches a method) — extracts the concrete, step-by-step methodology: ordered steps, tactics, checklists, numbers/thresholds, recommended tools, and verbatim scripts — each linked to the exact minute of the source.
6. **Clone chat** — answers how-to questions from the playbook, gives advice / solves tasks in the author's manner, and predicts their stance on new topics with stated confidence and reasoning. Grounded answers **quote the author and deep-link to the exact minute** they said it (several links if several sources cover it; a plain link for text). The saved evidence is an **index**: for the sources actually backing an answer, the clone re-opens them **live** to quote the real passage (falling back to a local raw cache, then the stored quote), so citations stay faithful to the source instead of a possibly-drifted summary.

## Install

```bash
# the skill
npx skills add mrgnfndr-dr/mind-clone -g -y
# or drop the skill folder into ~/.claude/skills/mind-clone

# (optional) the slash commands — copy them into your commands dir
cp mind-clone/commands/mind-clone-ask.md   ~/.claude/commands/mind-clone-ask.md
cp mind-clone/commands/mind-clone-build.md ~/.claude/commands/mind-clone-build.md
```

## Use

Two ways to invoke — both work:

```
# by meaning (auto-trigger)
> build a mind-clone of Alex Mashrabov
> what would Alex Mashrabov think about <new topic>?

# by slash command (two commands, ask listed first)
> /mind-clone-ask Alex Mashrabov what about pricing?   # chat with a clone
> /mind-clone-build Alex Mashrabov                      # build a clone
```

On first use it asks which language you'd like to talk in, then always replies in that language. The saved database stays in English so each clone is portable.

## Requirements

- **Built-in only** for the core: web search + fetch (text scraping) need no setup.
- **Optional, free** for richer harvest (auto-detected, with graceful fallback):
  - [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — YouTube/podcast captions & audio (`pip install yt-dlp`)
  - [`whisper`](https://github.com/openai/whisper) + `ffmpeg` — transcribe audio with no transcript (`pip install openai-whisper`)

Run `bash scripts/check_tools.sh` to see what's available.

## Where your data goes

Everything is saved under your current project, not inside the skill:

```
clones/<author-slug>/
  manifest.json        build metadata, name variants, chat language, coverage gaps
  sources.jsonl        canonical source registry
  sources.md           human-readable source table
  evidence.jsonl       dated, attributed quotes/chunks with timestamps + deep-links (the distillate — always)
  raw/<id>.md          full clean text per source — saved by default (books excepted)
  raw/<id>.srt         full timecoded transcript (audio/video) — saved by default; lets any passage be deep-linked
  cognitive-model.md   the brain
  reasoning-traces.md  worked reconstructions of the author's reasoning
  playbook.md          the author's procedural methodology — only if they teach one
  persona.md           bio, domains, voice notes
```

## How it's built

`SKILL.md` orchestrates; detailed methodology lives in `reference/` (loaded on demand) and output shapes in `templates/`. It borrows proven ideas: persisted evidence base + source registry (à la deep-research pipelines), signal-vs-noise pattern extraction (à la style-extraction skills), multi-modal name-variant sweeps (OSINT discovery), and a causal belief graph for extrapolation.

## Ethics

Public data only; not a surveillance tool. The clone is a model, not the person. See [`reference/ethics.md`](reference/ethics.md).

## License

[MIT](LICENSE).
