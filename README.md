# mind-clone — turn any public author into an AI Clone you can ask

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-da7756)
![Built-in tools only](https://img.shields.io/badge/setup-zero%20required-success)

**What it is:** an AI clone of *how a public author reasons* — built from their public content into a single SQLite knowledge store. The clone answers your questions, reasons in the author's own frameworks, and gives you their step-by-step method — **grounding every claim in the author's own words**. It answers only through an auditable command loop (the «contour») that drills to the exact evidence and refuses anything it can't cite (**no id, no claim**); every grounded answer deep-links to the exact source moment. Self-contained, stdlib-only.

Generic AI advice sounds like everyone and no one. **mind-clone** builds a *cognitive model* of a real author from their public content — articles, YouTube, podcasts, talks — then answers, advises, and predicts **the way that person actually reasons**, not by parroting their tone. Every grounded answer **quotes them and deep-links to the exact minute** they said it. And when the author teaches a method, it extracts a step-by-step **playbook** you can execute.

> It models a person from their **public output** — a useful imitation of how they reason *in public*, not their actual mind (real thinking is mostly unspoken and never makes it into the transcript). It's an interpretive model, never the real person: predictions are labeled and confidence-rated, and quotes are never fabricated.

<!-- DEMO GIF goes here — record a 15s terminal clip: ask a clone a question → answer in the author's logic → click the deep-link → YouTube opens at the exact minute. Save as docs/demo.gif and uncomment:
![mind-clone demo](docs/demo.gif)
-->

## See it in action

*Illustrative — the real thing cites verbatim, never invented:*

```
You:  /mind-clone-ask  How should I price a new product?

mind-clone (reasoning as the author):
  Don't start from your costs — start from the value the user captures.
  [...answer built from the author's own frameworks, not generic advice...]

  Backing it up, in his words:
  « <verbatim line the author actually said> »
    → Author, "Pricing talk", 14:02 ▶  https://youtu.be/VIDEO_ID?t=842
```

That link opens the video **at 14:02** — so you can hear him say it yourself. No source? It says so. Not sure? It rates its confidence.

## Quickstart

```bash
# 1. Install the skill (zero setup — built-in tools work out of the box)
npx skills add mrgnfndr-dr/mind-clone -g -y
#   …or just drop this folder into ~/.claude/skills/mind-clone

# 2. (optional) the slash commands
cp commands/mind-clone-ask.md   ~/.claude/commands/mind-clone-ask.md
cp commands/mind-clone-build.md ~/.claude/commands/mind-clone-build.md
```

Then, in Claude Code:

```
> build a mind-clone of <author name>          # or: /mind-clone-build <author>
> what would <author> think about <topic>?     # or: /mind-clone-ask <author> <question>
```

On first use it asks which language to chat in, then always replies in that language. (The saved database stays in English, so each clone is portable and shareable.)

## How it works (step by step)

Think of it like making a really good study guide about *how someone thinks* — then being able to ask that study guide questions.

1. **It finds everything the person said in public.** It searches the web for all of their articles, YouTube videos, podcasts, interviews, and talks — not just the first few, but as much as it can find.
2. **It shows you the list first.** Before any heavy work, it gives you a table of every source it found (date, type, link) so you can delete junk or add things it missed. Nothing happens until you approve.
3. **It reads each source and takes notes.** It goes through every video and article once, pulls out the important quotes and ideas, and writes down *exactly where each one came from* — including the **minute in the video**, so it can link you straight back to that moment later.
4. **It builds the "brain."** From those notes it works out *how the person thinks* — what they believe, the rules they follow, how they argue, what they push back on. This is what lets the clone answer questions the person never directly answered.
5. **It builds a "playbook" (if the person teaches a method).** If they explain step-by-step how to do something (say, grow an Instagram account), it also collects those exact steps, numbers, and checklists into a how-to guide you can follow.
6. **It checks itself.** It hides a few things the person actually said, tries to guess them from the "brain," and compares — so you can see where the clone is reliable and where it's just guessing.
7. **Now you talk to it.** You ask a question; the clone answers the way that person would think — and backs it up by **quoting them with a link to the exact minute** they said it.

## Why it's different

- **Reasoning, not impersonation.** Most "persona" tools copy someone's *tone*. mind-clone models *how they think* — so it can reason about questions the author never directly answered, and tell you its confidence.
- **Receipts.** Every grounded claim is quoted and **deep-linked to the exact second** of the source. At answer time it re-opens the source live to quote the real passage, so citations don't drift from what the author actually said.
- **Executable, not just inspirational.** If the author teaches a method, you get a real step-by-step playbook with their exact numbers and scripts — not vibes.
- **Honest by design.** Public sources only. Predictions are labeled as predictions. Missing coverage is reported, never hidden. Quotes are never fabricated.

## Under the hood (the technical version)

1. **Exhaustive discovery** — sweeps the web for everything public: articles, YouTube, podcasts, radio, talks, interviews, threads, papers — across name variants and affiliations.
2. **Source table (review gate)** — shows you a reviewable table (`Date · Type · Source · Summary · URL`) before the heavy work, so you approve/prune what goes into the database.
3. **Harvest (extract-on-the-fly)** — reads each source once and saves the *distillate* (dated, attributed quotes/chunks with timestamps + deep-links), not gigabytes of raw text. Fast by default: existing text + captions/transcripts only, **no slow ASR**. Sources with no subtitles are listed in a table and you decide whether to run `whisper`. **Books** are processed chapter by chapter (a copy you legally own, or public material — never pirated). Transcripts and article text are saved locally by default (tiny — tens of MB even for a 300-video channel); only full books are opt-in via `--archive-raw`.
4. **Cognitive model** — mines the corpus for the author's axioms, frameworks, causal belief graph, decision heuristics, antipatterns, and reconstructed reasoning traces.
5. **Playbook** (when the author teaches a method) — extracts the concrete, ordered methodology: steps, tactics, checklists, numbers, recommended tools, and verbatim scripts — each linked to the exact minute, every step traceable to the source.
6. **Faithfulness check** — a held-out smoke test: hide a position the author actually stated, predict it cold from the model, compare to the real quote, and score match vs **contradiction**. Makes drift visible instead of trusting fluency — indicative only, never tuned to pass.
7. **Clone chat** — answers how-to from the playbook, gives advice in the author's manner, and predicts their stance on new topics with stated confidence. For the sources backing an answer, it re-opens them **live** to quote the real passage (fallback: local raw cache → stored quote), so citations stay faithful. Ask it "how faithful are you?" to spot-check live.

## Requirements

- **Built-in only** for the core: web search + fetch (text scraping) need no setup.
- **Optional, free** for richer harvest (auto-detected, graceful fallback):
  - [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — YouTube/podcast captions & audio (`pip install yt-dlp`)
  - [`whisper`](https://github.com/openai/whisper) + `ffmpeg` — transcribe audio with no transcript (`pip install openai-whisper`)

Run `bash scripts/check_tools.sh` to see what's available.

## Where your data goes

Everything is saved under your current project, not inside the skill — so the clone ships with your repo:

```
clones/<author-slug>/
  clone.db        CANONICAL — SQLite: two tables, meta + ep (+ ep_fts). The one center.
  raw/<id>.srt    timecoded transcript (audio/video) — source material, referenced by meta.raw_path + hash
  raw/<id>.md     clean text per source — source material (books excepted)
  runs/<id>/      per-question contour artifacts: intent.md · selection.tsv · delivery.md · answer.md · log.jsonl
  config.json     state only: chat language, name variants, coverage-gap notes
```

The **only interface is the contour** (`scripts/loop.py`): the LLM never reads `clone.db` or
the raw store directly. The source table, the cognitive map, the playbook, and the manifest are
**`render` views** computed on demand — never stored. There is no `evidence.jsonl`, brain `.md`,
or `manifest.json`; those would be copies of the canon.

## How it's built

`SKILL.md` orchestrates; detailed methodology lives in `reference/` (loaded on demand). Build
writes EP rows through the contour (`import`, validation → log); the brain is the relation
overlay on those rows (`render brain`). It borrows proven ideas: a grounded evidence base (every
EP carries `text` + `backing` + deep-link), signal-vs-noise pattern extraction, multi-modal
name-variant sweeps (OSINT discovery), and a causal belief graph for extrapolation.

## Ethics

Public data only; not a surveillance tool. The clone is a model, not the person, and is labeled as such. Books are used only from a copy you legally own or public material about them — never pirated. See [`reference/ethics.md`](reference/ethics.md).

## License

[MIT](LICENSE).
