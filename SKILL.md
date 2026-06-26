---
name: mind-clone
description: Build and talk to an AI "mind clone" of a real public author — a model of how they think, built from their public content, that reasons in the author's own frameworks and cites them with deep-links to the exact source moment. Use when the user wants to clone someone's mind/thinking from their public content (articles, YouTube, podcasts, talks, interviews), get advice "in the thinking of" a specific person, extract that person's step-by-step method or playbook, or predict what a named person would think about a topic. Triggers on "clone <person>", "mind-clone <person>", "build a clone of", "think like <person>", "what would <person> say/think about", "turn <person> into an AI", "create a digital clone of someone's mind". Self-contained: relies only on built-in tools plus optional free CLIs (yt-dlp, whisper).
---

# mind-clone — a clone of how an author thinks, from public content

This skill builds a **cognitive model** ("mind clone") of a real author from their public footprint, persists everything as a local database in the user's project, and then answers questions, gives advice, and predicts positions **the way that author would think** — not by imitating their tone, but by reasoning through their actual mental models.

The clone is an **interpretive model built from public sources**, not the real person. It must always label predictions as predictions and never fabricate quotes. See `reference/ethics.md`.

---

## Two modes — route first

On invocation, decide which mode applies:

| Signal | Mode | Go to |
|---|---|---|
| "Build / create a clone of X", no clone exists yet for X | **BUILD** | Pipeline below |
| A clone folder already exists and the user asks a question, wants advice, or "what would X think about…" | **CHAT** | `reference/04-clone-runtime.md` |
| Unclear | Ask: build a new clone, or talk to an existing one? List clones found in `./clones/`. |

Check `./clones/` (in the current working directory) for existing clones before deciding.

---

## Step 0 — Language protocol (always first, both modes)

1. On the **first interaction of a session**, ask the user which language they want to converse in (offer the language their message is in + English).
2. Store the choice in the clone's `manifest.json` (`"chat_language"`). On later sessions, read it and skip the question.
3. **Always converse in the user's chosen language.**
4. **All persisted artifacts** (the database, cognitive model, source tables, this skill's files) are written in **English** regardless of chat language — so the clone is portable and shareable. Translate to the user's language only in the live conversation.
5. **In CHAT mode, the author's quotes display in the user's language too** — lead with a faithful translation, but **always keep the verbatim original alongside** (the deep-link verifies the original). Never present a translation alone as a verbatim quote. See `reference/language.md` → "Quoting the author in CHAT mode".

Full rules: `reference/language.md`.

---

## BUILD pipeline (5 phases)

Run phases in order. Each writes to `./clones/<author-slug>/`. Load the linked reference at the start of each phase. Tell the user what you're doing between phases; don't run silently for minutes.

### Phase 1 — DISCOVERY (exhaustive search)
Load **`reference/01-discovery.md`**.
Enumerate name variants and affiliations, then run a multi-modal web sweep (articles, YouTube, podcasts, radio, talks, interviews, social, papers). Goal: find *everything* public, not the top 10 links. Deduplicate into a source registry.
→ writes `sources.jsonl`

### Phase 2 — SOURCE TABLE (review gate)
Load **`templates/sources-table.md`**.
Present the user a table of every source found: **Date · Type · Source · Summary · URL**. This is the review checkpoint — the user can prune, add, or approve before the expensive harvest. Mirror the table to disk.
→ writes `sources.md`, shows table in chat

### Phase 3 — HARVEST (extract-on-the-fly)
Load **`reference/02-harvest.md`**.
Default is **fast**: read each source once and extract the distillate into `evidence.jsonl` — dated, attributed quotes + cognitive signal — **and save the raw transcript/text to `raw/` by default** (text is cheap — tens of MB even for a big channel — and it powers deep-links + CHAT-mode live-grounding fallback). **Capture timestamps** (`t_start` in seconds + a ready `deeplink`) for every audio/video quote so the clone can later cite the author verbatim and link to the exact minute; text quotes store the plain URL. Use existing text/captions/transcripts only (fast); **no slow ASR by default**. Articles via WebFetch, YouTube via yt-dlp captions.
- Sources with **no subtitles/transcript** → collect them, **show the user a table** (Type · Title · Source · Duration · URL) and **ask** whether to run whisper (slow). Note that a few missing files rarely shift the reasoning model. Run whisper only on opt-in (all / selected).
- **Books** → processed **chapter by chapter** (extract-on-the-fly, so volume is fine — the book collapses into distilled evidence, not stored whole). Use a user-supplied legally-owned file or public material only; cite by chapter/page (no deep-link). Often the richest playbook source. Never pirate.
- **Raw transcripts/text are saved by default** (`raw/<id>.srt` + `raw/<id>.md`); no flag needed. **Books are the one exception** — only the per-chapter distillate is kept by default (size + copyright); `--archive-raw` opts into keeping more book text.
- **Report every gap — never leave a silent one.**
- **Load into the table store:** after emitting `evidence.jsonl`, run
  `python <skill>/scripts/clone.py import .` (validates on write — bad `kind`/FK rejected) then
  `python <skill>/scripts/manifest.py .` to (re)generate `MANIFEST.md`. From here on, the data is
  queried through `clone.py`, never read raw.
→ writes `evidence.jsonl` + `raw/<id>.srt`/`raw/<id>.md` (books excepted), then `clone.db` + `MANIFEST.md`

### Phase 4 — COGNITIVE MODEL (the brain)
Load **`reference/03-cognitive-model.md`** and **`templates/cognitive-model.md`**.
Mine the harvested corpus **via `clone.py`** (`stats --by kind` for shape, `query`/`fts` for
themes — don't dump the whole table) for: worldview axioms, mental models/frameworks, causal beliefs (belief→cause→consequence graph), decision heuristics, strong stances, antipatterns (what they reject & why), domains of confidence, characteristic reasoning moves, and evolving views. Reconstruct concrete **reasoning traces** showing *how* the author got from premise to conclusion. Separate documented patterns from noise; cite evidence IDs for every claim. **Keep the model lean** — a thin, well-cited index over the evidence, not an elaborate theory; the heavy lifting happens at answer time via retrieval + live-grounding, so prefer letting the clone retrieve a raw quote over inventing unsupported structure. **Tag every entry with a confidence weight (`H/M/L`) and, when a view is time-bound, an `as of <year>` / evolving-view timeline** — so the clone leans on strong claims, hedges weak ones, and answers "as of when?" correctly.
→ writes `cognitive-model.md`, `reasoning-traces.md`, `persona.md`

> **EP-store (optional v2, additive).** With `--ep`, also emit the belief-graph edges into an append-only relation layer under `ep/` (entities + vectors grouped in folders, every EP grounded with `backing:` evidence ids). The belief-graph section of `cognitive-model.md` then becomes a *render* of `ep/`, and later sources update the clone incrementally (a reconciled *delta*) instead of a full rebuild. Off by default — old clones are unaffected. Spec + commands: **`reference/07-ep-store.md`**.

### Phase 4b — PLAYBOOK (procedural methodology, when the author teaches one)
Load **`reference/05-playbook.md`** and **`templates/playbook.md`**.
If the corpus contains how-to / instructional content, extract the author's **concrete methodology**: ordered steps, tactics, checklists, numbers/thresholds, recommended tools, verbatim scripts/templates, and "don't do this" mistakes — each cited with evidence IDs + a deep-link to the exact minute. This is *what to do* (vs Phase 4's *how the author thinks*); the two cross-link. If the author is a pure thinker with **no** prescribed methodology, skip this and record "no methodology found" in coverage gaps.
→ writes `playbook.md` (when applicable)

### Phase 4c — FAITHFULNESS CHECK (held-out smoke test)
Load **`reference/06-evaluation.md`**.
Hold out 5–10 evidence entries where the author states a clear, checkable position; for each, predict the answer *cold* from the rest of the model and compare to the real quote. Score match / partial / miss / **contradiction** (the dangerous one). This makes drift visible instead of trusting fluency — but it's a **smoke test, not proof** (small-N, gameable; never tune the model to pass it). Failing probes → fix the model (tighten/remove the over-reached inference), or lower confidence for thin domains.
→ writes `evaluation.md`

### Phase 5 — FINALIZE
Write `manifest.json` (author, slug, name variants, counts, chat_language, build date, coverage gaps, `has_playbook`, `faithfulness`). Ensure `clone.db` + `MANIFEST.md` are built and in sync (`clone.py validate .`, `manifest.py . --verify`). Give the user a build summary: # sources by type, # quotes, whether a playbook was built, the faithfulness result (with its "indicative only" caveat), coverage gaps, and how to start chatting with the clone.
→ writes `manifest.json`

---

## CHAT mode

Load **`reference/04-clone-runtime.md`**.
Load `cognitive-model.md`, `reasoning-traces.md`, `MANIFEST.md` (and `playbook.md` if it exists) for the requested author — **never the whole evidence table**. Reason *through* the author's models, and pull only the relevant evidence slice via `clone.py` (`query`/`fts`/`get`) per the two-role retrieve→analyze loop. The table is the **index**: for the 1–3 sources actually backing an answer, the clone re-opens the source **live** to quote the real passage (ladder: live fetch → `raw/` cache → stored quote via `clone.py get`), so citations stay faithful and self-correct any harvest drift. Three output contracts:
- **How-to / "give me the steps" / "what's his method for X"** → answer from `playbook.md`: the author's concrete steps, tactics, numbers, and scripts, **cited verbatim with deep-links to the exact minute** (multiple links if several sources cover it; plain URL for text).
- **Advice / solve a task** → reason in the author's frameworks, ground in documented beliefs, and **cite the author verbatim with a deep-link to the exact minute**.
- **Predict a position on a new topic** → map the topic to nearest known beliefs via the belief graph, extrapolate, and **state confidence + which beliefs drove the prediction**, clearly labeled as inference vs documented.

---

## Database layout (per author, in the user's project)

The canonical store is a **SQLite table store** (`clone.db`). The `*.jsonl` files are the
**harvest emit / interchange format** — the LLM writes rows as JSONL, then `clone.py import`
validates and loads them into `clone.db` (validation-on-write: CHECK enums, FK, NOT NULL).
**The LLM never reads `clone.db` or the raw `*.jsonl` directly** — it reads `MANIFEST.md`
(the contract) and pulls slices via `scripts/clone.py`. See `ARCHITECTURE.md` for the invariants.

```
clones/<author-slug>/
  clone.db               CANONICAL truth — SQLite: sources + evidence tables, FTS5, CHECK/FK enforced
  MANIFEST.md            the LLM↔table contract — GENERATED from clone.db (fields, enums, commands, recipes)
  manifest.json          build metadata, name variants, chat_language, coverage gaps
  sources.jsonl          source registry — emit/interchange format, imported into clone.db
  evidence.jsonl         distillate — emit/interchange format, imported into clone.db
  sources.md             human-readable source table
  ep/                    append-only relation layer (v2, only with --ep): entities.jsonl + <group>/<vector>.Ep.md
  raw/<id>.md            full clean text per source — saved by default (books excepted)
  raw/<id>.srt           full timecoded transcript (audio/video) — saved by default; makes any passage deep-linkable
  cognitive-model.md     the brain: axioms, frameworks, belief graph, heuristics, antipatterns
  reasoning-traces.md    worked reconstructions of the author's reasoning
  playbook.md            the author's procedural methodology: steps, tactics, numbers, scripts  (only if the author teaches one)
  evaluation.md          held-out faithfulness smoke test: probes, cold predictions, real quotes, score
  persona.md             bio, domains, voice notes (supports the brain, secondary)
  runs/<id>/             per-intent retrieve→analyze artifacts (intent.md, retrieval.md, choice.md)
```

All paths are relative to the **user's current working directory**, so the clone DB ships with the user's project, not inside this skill. `clone.db` is the working store; commit a `clone.sql` (`sqlite3 clone.db .dump`) as a diffable mirror if version-controlling clones.

---

## Guardrails

- **No fabrication.** Every quote in `evidence.jsonl` must be real and traceable to a source. Never invent citations. If you don't have evidence, say so.
- **Label inference.** Documented view ≠ predicted view. Predictions must be marked and confidence-rated.
- **Report gaps, never hide them.** If a source couldn't be transcribed or a topic isn't covered, state it.
- **Public data only; this is a model, not the person.** See `reference/ethics.md`.
- **Think, don't mimic.** The value is reproducing *reasoning*, not parroting catchphrases.
