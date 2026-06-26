# Phase 3 — Harvest (extract-on-the-fly)

Goal: in **one pass per source**, read it and extract the cognitive material directly — quotes, belief edges, reasoning, chunks — into the **distillate** (`evidence.jsonl`), and in the same pass save the raw transcript/text to `raw/`. The distillate is what feeds the cognitive model; the raw file is a cheap cache for deep-links and live-grounding. Do **not** bulk-dump raw text and *defer* extraction — extract as you read, in one pass; saving the raw file alongside is fine (it's not a separate dump-then-process step). Self-contained: built-in tools by default; slow ASR only on explicit user request.

## Default behavior (fast)

For each approved source, in a single read:
1. Obtain the **text** (cascade below).
2. Extract **evidence** straight into `evidence.jsonl` — verbatim quotes with `source` id + `locator` + `kind` (see schema below).
3. Note any cognitive signal (axiom, framework, belief edge, heuristic) for Phase 4. You may keep short **chunks** of high-signal passages in evidence as `kind:"chunk"`.
4. Set the source `status` in `sources.jsonl`.
5. **Save the raw transcript/text to `raw/`** (default — see below), then move on. (Don't bulk-dump *first*; the rule is one-pass — read, extract evidence, and write the raw file in the same pass.)

What's **always persisted by default** (small, fast, makes the clone provable & updatable, and powers deep-links + CHAT-mode live-grounding fallback):
- `evidence.jsonl` — the quotes/chunks you kept, traceable.
- (Phase 4) `cognitive-model.md`, `reasoning-traces.md`.
- **`raw/<id>.md`** — full **clean text** of each web/text & transcript source. Text is cheap (≈25–30 KB per 30-min video; tens of MB even for a 300-video channel), so we keep it by default — no flag needed.
- **`raw/<id>.srt`** (audio/video) — the full **timecoded** transcript, saved by default. This makes timestamps recoverable for *any* passage later (not just what you quoted on the first pass), lets Phase 4b mine the whole transcript for steps/numbers with exact-minute links, and serves as the **offline cache** for CHAT-mode live retrieval when a source later goes offline/paywalled.

**The one exception — books.** Full books are large *and* copyright-sensitive, so a whole book is **not** archived by default — only the per-chapter distillate in `evidence.jsonl`. `--archive-raw` opts into keeping more book text (within fair use). See "Books" below. For everything else, raw is saved automatically and `--archive-raw` is a no-op.

## Text-acquisition cascade (default = no slow ASR)

| Source type | How (fast path) | If unavailable |
|---|---|---|
| Article / interview / thread / profile | `WebFetch` → clean Markdown body | try cached/readable version; else mark `failed` |
| YouTube | `yt-dlp` captions (seconds, no video download) — **save the timecoded file** (always, by default): `yt-dlp --write-auto-subs --write-subs --sub-lang en --skip-download --convert-subs srt -o "raw/<id>.%(ext)s" "<url>"` → harvest from `raw/<id>.srt` and keep it (you need each passage's start time for deep-links — see "Timestamps & deep-links"). Also save the clean text as `raw/<id>.md`. Or fetch the transcript panel via `WebFetch`. | → goes to the **no-transcript list** (see below) |
| Podcast / radio | **prefer published transcript / show notes** via `WebFetch` | → **look for a YouTube/captioned mirror** (step below) → only then the **no-transcript list** |
| Book (`acquire:"user_file"`) | parse the user-supplied EPUB/PDF **chapter by chapter** (see "Books" below) | if the file can't be parsed, fall back to public-only |
| Book (`acquire:"public_only"`) | `WebFetch` sample chapters / Google Books preview / author's talks & summaries about it | mark coverage as partial; never pirate the full text |

Caption pull is fast — it's just subtitle text, not the media file. Run it for all YouTube/audio sources first.

### Audio with no transcript → look for a YouTube/captioned version FIRST
Before considering whisper for any audio-only podcast/radio episode, **check whether the same episode exists as a YouTube video (or other captioned upload)** — many podcasts publish a video mirror with auto-captions. Search: `<show name> <episode title> youtube`, the show's YouTube channel/playlist, and the guest's name + show. A reliable way to locate it is `yt-dlp` search itself, e.g. `yt-dlp "ytsearch5:<show> <guest>" --print "%(title)s | %(id)s"`, then `yt-dlp --list-subs <id>` to confirm captions. If found, pull captions via `yt-dlp` (fast, free) and harvest from there; cross-link the alt URL in the registry.

**If NO captioned version exists anywhere: do NOT auto-run whisper and do NOT silently skip.** The episode joins the **same no-transcript table shown to the user** (below), exactly like every other un-transcribable source, and the user decides per-source whether to run whisper. Whisper is *never* automatic — always user-chosen. Skipping audio without first checking for a captioned mirror is a coverage bug — it can silently drop whole topics the author only discussed there.

## No-transcript sources → table + ask before whisper

Some sources will have **no captions and no published transcript**. Do **not** silently skip them and do **not** auto-run whisper (it's slow: minutes per hour of audio). Instead:

1. Collect them into a list and **show the user a table**:

```
N sources have no subtitles/transcript. Transcribing them needs whisper (slow ASR — roughly real-time-ish per file). Want me to run it?

| # | Type | Title | Source / Outlet | Duration | URL |
|---|------|-------|-----------------|----------|-----|
| s007 | youtube | <video title> | <channel> | 38 min | https://… |
| s011 | podcast | <episode title> | <show> | 64 min | https://… |
```

2. Add this note: *"If there are only a few such files, skipping them won't meaningfully change the clone's reasoning model — the cognitive model is built from many sources, and a handful of missing ones rarely shifts it. Whisper matters most if these are high-signal (long interviews/episodes) or if there are many."*

3. **Ask explicitly** — give clear choices:
   - skip all (default, fast) — they stay logged as `not_transcribed`,
   - transcribe **all** with whisper,
   - transcribe **only selected** (user picks the high-value rows).

4. Only if the user opts in: check `whisper`/`ffmpeg` are installed (`scripts/check_tools.sh`); if missing, offer the one-line install or fall back to skipping. Then:
   `yt-dlp -x --audio-format mp3 -o "tmp/<id>.mp3" "<url>"` → `whisper "tmp/<id>.mp3" --model small --output_format srt` → save the result as `raw/<id>.srt` (timecoded, so whisper'd sources are deep-linkable too) **plus** `raw/<id>.md` for the clean text → extract evidence on the fly → **delete the temp audio** (the audio file is the only big artifact; the transcript stays). Saving the transcript is the default, same as captions. (The slow part is whisper itself, not saving — and whisper still runs only on the user's explicit opt-in.)

5. Whatever stays untranscribed is recorded in `manifest.json` under `coverage_gaps` and surfaced in the build summary — never hidden.

## Books — process by chapter, don't drown in volume

A book is large (often 50k–150k words), but the **extract-on-the-fly** principle handles it cleanly: you never load or store the whole book — you distill it. The result is a few hundred evidence entries, the same size regime as a prolific channel. Only the harvest *pass* is longer; the model and the clone are no heavier.

**How to harvest a book:**
1. **Split into chapters/sections.** For EPUB, each chapter is already a unit; for PDF, split on chapter headings. Process **one chapter at a time** — read it, extract evidence, move on. Never hold the entire book in context at once.
2. **Extract the distillate per chapter** exactly like any source: `kind:"reasoning"` for argument chains, `kind:"procedure"` for steps/numbers/scripts (books are often the richest playbook source — mine them hard for methodology), plus key beliefs and stances. Aim for the high-signal passages, not a chapter-by-chapter summary of everything.
   - **Read the chapter in full, but persist only the distillate.** Reading the whole chapter is necessary to capture a method's full sequence — but what lands in `evidence.jsonl` is a handful of `kind:"procedure"` entries (the step, its number/threshold, a **short** verbatim quote for key lines/scripts, locator `Ch./p.`), **not** the chapter text. A 120k-word book becomes a few hundred pointed extractions, never a stored copy. Quote verbatim only short, fair-use-sized fragments (a maxim, a script, a formula) — never reproduce whole chapters into the playbook or evidence.
3. **Locator = `Ch. N` / page / section** (e.g. `"Ch. 4, p. 112"`). Books have **no timestamp and no per-passage URL**, so:
   - `t_start`: null (omit).
   - `deeplink`: a link to a **legal** location for the book (publisher / Google Books page) if one exists, else just the book title — never a pirate link, never a fabricated page anchor.
   - In CHAT mode, cite as `«quote» — <Book Title>, Ch. 4` (text-style citation, no deep-link).
4. **Report progress** between chapters (e.g. "harvested 6/18 chapters") — a book takes a while; don't run silent for minutes.
5. **`public_only` books:** harvest only what's legitimately accessible (sample chapters, preview, summaries, the author's talks about the book). Flag in the source `summary` and in `manifest.json` `coverage_gaps` that the book is **partially covered**.

**`--archive-raw` + books:** keeping a full book's raw text is heavy and usually unnecessary — chapters are well-structured and re-readable from the user's file on demand. Default to **not** archiving the full book even under `--archive-raw` unless the user explicitly wants it; the per-chapter distillate in `evidence.jsonl` is what the model and playbook use.

## Evidence schema

```json
{"id":"e0007","source":"s003","date":"2024-03-15","topic":"hiring","kind":"belief|argument|heuristic|prediction|anecdote|reasoning|procedure|chunk","context":"<the question asked / what prompted this>","quote":"<verbatim, can be multi-sentence>","locator":"12:30 / para 4","t_start":750,"deeplink":"https://youtu.be/<id>?t=750","note":"EN translation if non-English; any extra context"}
```

- **`context` is required** — capture the **eliciting question or surrounding setup** (e.g. "Asked whether to train own models vs use APIs"). An isolated one-liner loses the question it answered; for a *mind* clone the Q→A pairing and the reasoning around it are worth more than the punchline. For interviews, record the interviewer's actual question.
- **Prefer reasoning over slogans.** When the author *explains why* (premise → because → therefore), capture the **whole multi-sentence passage** as one `kind:"reasoning"` entry — don't shred a chain into disconnected one-liners. Quotable maxims are fine too, but the chains are the high-value material (Phase 4 turns them into reasoning traces).
- **Verbatim only** for quotes; light `…` trimming ok; never paraphrase into a quote.
- `kind:"reasoning"` = a connected argument/chain. `kind:"chunk"` = a high-signal passage kept for later mining (lightweight stand-in for raw archiving).
- **`kind:"procedure"`** = concrete how-to material the author *prescribes* — a step, tactic, checklist item, threshold/number, recommended tool, or verbatim script/template. **Capture these whenever the author teaches a method**, even though they're not "reasoning": they're the raw material for `playbook.md`. Keep the exact numbers and verbatim scripts — "post 1 Reel/day, hook in 3s" is gold, don't smooth it into "post often". (For a pure thinker with no methodology, you'll have few or none — that's fine.)
  - **Keep the step in its method context.** Use `context` to record *where in the author's method this sits* (e.g. "step 3 of his launch sequence, after building the content bank") and any **condition/caveat** the author attaches ("only once you have 1k followers"). This is what keeps the later playbook faithful to the book's actual structure instead of a re-ordered, condition-stripped lookalike. Don't capture a step as a free-floating tip if the author embedded it in a sequence.
- `locator`: human-readable position — `MM:SS` (or `HH:MM:SS`) for audio/video, paragraph/section for text.
- **Each entry doubles as a retrieval pointer.** In CHAT mode the clone may re-open the source live to quote the *real* passage (not the stored distillate) — so `source` + `locator`/`t_start` must be **precise enough to re-find the passage** (a findable verbatim phrase in `quote`, an accurate timestamp, a real chapter/page). Treat the stored `quote` as a cache/index, not the final word; the live source wins on any conflict.
- **`t_start`** (audio/video only): start time of the quoted passage **in whole seconds**, taken from the SRT timecode of the passage's first line. This is what makes the citation jump to the right moment. Omit for text sources.
- **`deeplink`**: a ready-to-click URL that opens the source at `t_start`. Build it at harvest time from the source `url` + `t_start` per the format table below, so CHAT mode can cite without recomputing. For text sources, set it to the plain `url` (plus a `#anchor`/fragment if the page has one). See **Timestamps & deep-links**.

## Timestamps & deep-links (so the clone can cite the exact moment)

The point: when the clone later answers, it should be able to **quote the author verbatim and link to the exact minute** the author said it. That only works if you capture the start time *now*, during harvest.

For every audio/video evidence entry:
1. Read the SRT timecode of the **first subtitle line of the passage you're quoting** (the SRT format is `HH:MM:SS,mmm --> …`). Don't strip these — they're the whole point.
2. Convert that start time to **whole seconds** → `t_start` (e.g. `00:12:30` → `750`). Keep the human-readable form in `locator` too.
3. Build `deeplink` from the source `url` + `t_start` using the table below.

| Source URL form | Deep-link format (at `<sec>` seconds) | Example (`t_start=750`) |
|---|---|---|
| `youtube.com/watch?v=ID` | append `&t=<sec>s` | `https://www.youtube.com/watch?v=ID&t=750s` |
| `youtu.be/ID` | append `?t=<sec>` | `https://youtu.be/ID?t=750` |
| YouTube, `?`/`&` already present | append `&t=<sec>s` | `…&list=…&t=750s` |
| Vimeo `vimeo.com/ID` | append `#t=<sec>s` | `https://vimeo.com/ID#t=750s` |
| Spotify / Apple Podcasts episode | platform rarely honors a start param → use the plain episode `url` and put the timestamp in text (`at 12:30`) | `https://… (at 12:30)` |
| Other web audio/video player | try `#t=<sec>` (HTML5 media fragment); if the player ignores it, fall back to plain `url` + `(at MM:SS)` | — |
| **Text** (article/thread/paper) | **plain `url`** (add `#:~:text=<quote>` or a section `#anchor` if it helps land on the passage) | `https://site.com/essay#hiring` |
| **Book** | no timestamp/anchor — `deeplink` = legal book page (publisher/Google Books) or null; cite by `Ch./page` in text | `Atomic Habits, Ch. 4` |

Rules:
- **One evidence entry = one deep-link to its own start time.** When a topic is covered in **several sources**, each produces its own entry with its own `deeplink`; CHAT mode then cites **all** of them (see runtime).
- If you can't determine a reliable `t_start` (no timecodes survived), set `t_start` to null, keep the plain `url` in `deeplink`, and note `"timestamp unavailable"` — never fabricate a time.
- The timecoded SRT is saved to `raw/<id>.srt` **by default** (audio/video), so timestamps are recoverable for passages you didn't quote the first time — no flag needed.

> **Reasoning-fidelity note:** because default mode discards full transcripts, reasoning traces built later can only draw on what's in `evidence.jsonl`. If faithful, re-derivable reasoning chains matter for this clone, run with **`--archive-raw`** so Phase 4 (and future updates) can re-read full context instead of re-fetching. Flag any trace step that is your reconstruction (connecting separate beliefs) vs the author's explicit chain.

## Write into the store through the contour (end of harvest)

> **Terminology:** throughout this doc the "distillate" / "evidence" is the **EP-point delta** —
> a transient `.jsonl` (one EP per line: `meta_id, grp, vector, kind, text, t_start, deeplink,
> backing, …`, plus `_t:"meta"` rows for sources). It is **thrown away after import**; the
> canonical store is the `ep` + `meta` tables in `clone.db`.

The delta is the **emit format**, not the canonical store. Once harvest is done (or after each
incremental batch):

```
python -s <skill>/scripts/loop.py <slug> import <delta.jsonl>   # validation-on-write -> log
```

- `import` inserts into `clone.db` under CHECK-enum on `kind`, FK `ep.meta_id→meta.id`, NOT NULL,
  FTS5. Invalid rows (bad `kind`, dangling source, missing field) are **rejected with a reason and
  logged**, never silently dropped — fix them in the delta and re-import.
- From here, **all access is through the contour** (`loop.py`: drill-down read, `render`, `get`);
  nothing reads the raw table. There is no `MANIFEST.md` file — the contract is `render manifest`.
- See `ARCHITECTURE.md` for invariants.

## Quality gates
- Prefer **primary** + reasoning-rich sources (interviews, essays) over press blurbs.
- Aim for **3+ independent sources** behind any belief that will enter the model.
- After harvest, the `import` **log** is the coverage report: `loaded / rejected (+why)`. Plus a
  one-line note on `failed Y / not_transcribed Z`. Gaps go into `config.json`. Silent truncation is forbidden.
- Confirm the `import` log shows `rejected=0` (or every rejection explained and resolved).
