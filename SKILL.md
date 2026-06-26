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
2. Store the choice in the clone's `config.json` (`"chat_language"`). On later sessions, read it and skip the question.
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
→ emits `meta` rows (a transient delta) → `loop.py <slug> import <delta.jsonl>` (validated on write → log)

### Phase 2 — SOURCE TABLE (review gate)
Load **`templates/sources-table.md`**.
Present the user a table of every source found: **Date · Type · Source · Summary · URL** via `loop.py <slug> render sources`. This is the review checkpoint — the user can prune, add, or approve before the expensive harvest.
→ `render sources` (JIT view from `meta`; nothing stored)

### Phase 3 — HARVEST (extract-on-the-fly)
Load **`reference/02-harvest.md`**.
Default is **fast**: read each source once and extract the distillate as **EP points** (a transient delta `.jsonl`, thrown away after `import`) — dated, attributed, grounded quotes (`text`) + their group/vector/relation — **and save the raw transcript/text to `raw/` by default** (text is cheap — tens of MB even for a big channel — and it powers deep-links + CHAT-mode live-grounding fallback). **Capture timestamps** (`t_start` in seconds + a ready `deeplink`) for every audio/video quote so the clone can later cite the author verbatim and link to the exact minute; text quotes store the plain URL. Use existing text/captions/transcripts only (fast); **no slow ASR by default**. Articles via WebFetch, YouTube via yt-dlp captions.
- Sources with **no subtitles/transcript** → collect them, **show the user a table** (Type · Title · Source · Duration · URL) and **ask** whether to run whisper (slow). Note that a few missing files rarely shift the reasoning model. Run whisper only on opt-in (all / selected).
- **Books** → processed **chapter by chapter** (extract-on-the-fly, so volume is fine — the book collapses into distilled evidence, not stored whole). Use a user-supplied legally-owned file or public material only; cite by chapter/page (no deep-link). Often the richest playbook source. Never pirate.
- **Raw transcripts/text are saved by default** (`raw/<id>.srt` + `raw/<id>.md`); no flag needed. **Books are the one exception** — only the per-chapter distillate is kept by default (size + copyright); `--archive-raw` opts into keeping more book text.
- **Report every gap — never leave a silent one.**
- **Write through the contour:** emit each source's EP points as a transient delta and run
  `loop.py <slug> import <delta.jsonl>` — validation-on-write (CHECK `kind` / FK `meta_id` /
  NOT NULL) rejects bad rows with a reason and **logs** loaded/rejected. The delta is throwaway;
  the canon is the `ep` table. From here the data is reached only through the contour.
→ `ep` rows in `clone.db` (via `import` → log) + `raw/<id>.srt`/`raw/<id>.md` (books excepted)

### Phase 4 — COGNITIVE MODEL (the brain)
Load **`reference/03-cognitive-model.md`** and **`templates/cognitive-model.md`**.
Mine the corpus **via the contour** (`fts` / `map` / `render brain` — never dump the whole
table) and enrich each EP point with its **relation overlay** (`subject –relation→ object`)
and its `group`/`vector` placement, so the belief graph, frameworks, heuristics, stances,
antipatterns, and reasoning chains are all just typed relations *on the EP points* — each
already grounded by its own `text` + `backing` + deep-link. **Keep it lean**: the relation
overlay is a thin index; the heavy lifting is answer-time retrieval + live-grounding. **Tag
each EP with a confidence weight (`H/M/L`) and, when time-bound, `as_of <year>`.** Refine
grouping/relations incrementally via the EP append-only pipeline (a reconciled *delta*), not
a full rebuild.
→ enriches `ep` rows (relation overlay + group/vector + confidence). The brain is
  `render brain`, not a stored file. Voice/register notes → `config.json`.

> **The EP model is the canon, not an add-on.** Axioms, frameworks, the belief graph,
> heuristics, traces — there is no separate `cognitive-model.md`; they are EP relations,
> queried by the contour and rendered on demand. Append-only refinement pipeline + format:
> **`reference/07-ep-store.md`**.

### Phase 4b — PLAYBOOK (procedural methodology, when the author teaches one)
Load **`reference/05-playbook.md`** and **`templates/playbook.md`**.
If the corpus contains how-to / instructional content, capture the author's **concrete methodology** as `kind:"procedure"` EP points: ordered steps, tactics, checklists, numbers/thresholds, recommended tools, verbatim scripts/templates, and "don't do this" mistakes — each grounded by its `text` + deep-link. This is *what to do* (vs Phase 4's *how the author thinks*). If the author is a pure thinker with **no** prescribed methodology, record "no methodology found" in coverage gaps.
→ `procedure`-kind `ep` rows; surfaced by `render playbook` (no stored file)

### Phase 4c — FAITHFULNESS CHECK (held-out smoke test)
Load **`reference/06-evaluation.md`**.
Hold out 5–10 EP points where the author states a clear, checkable position; for each, predict the answer *cold* through the contour and compare to the real `text`. Score match / partial / miss / **contradiction** (the dangerous one). This makes drift visible instead of trusting fluency — but it's a **smoke test, not proof** (small-N, gameable; never tune the model to pass it). Failing probes → fix the EP relations (tighten/remove the over-reached one), or lower confidence for thin domains.
→ a **faithfulness log** in `runs/<id>/` (probes, cold predictions, real text, verdicts), not stored prose

### Phase 5 — FINALIZE
Write only **state** to `config.json` (chat_language, name variants, coverage-gap notes — the few facts not derivable from the corpus). Everything countable comes from `render manifest` (sources by type, EP counts by kind, source window) — don't store it. Give the user a build summary from `render manifest` + the faithfulness log (with its "indicative only" caveat), coverage gaps, and how to start chatting (the `intent` command).
→ writes `config.json` (state only); counts/contract come from `render manifest`

---

## CHAT mode

Load **`reference/04-clone-runtime.md`**. The clone answers **only through the contour**
(`scripts/loop.py`) — never reading the table or raw store directly. Run the cycle:
`intent "<question>"` → `sources` → `map <src>` → `select <src> <vectors>` → `compile`
(repeat map/select across the 1–3 sources that bear on the question) → read
`runs/<id>/delivery.md` → write `runs/<id>/answer.md`, reasoning **as the author** over
**only the delivered EPs** → `verify` (rejects any cited id not in the delivery — no id, no
claim). Use `fts`/`get` for recall and `render brain` for the author's models. For the words
shown to the user, live-ground the 1–3 backing sources (live fetch → `raw/` cache → the EP
`text`). Three output contracts:
- **How-to / "give me the steps" / "what's his method for X"** → `render playbook` + the procedure-kind EPs delivered: concrete steps, numbers, scripts, **cited verbatim with deep-links to the exact minute**.
- **Advice / solve a task** → reason in the author's frameworks (`render brain`), ground in the delivered EPs, **cite the author verbatim with a deep-link to the exact minute**.
- **Predict a position on a new topic** → map the topic to nearest EP relations, extrapolate along them, and **state confidence + which EPs drove the prediction**, clearly labeled as inference vs documented.

---

## Store & interface (per author, in the user's project)

The canonical store is a **two-table SQLite database** (`clone.db`): `meta` (one row per
source — provenance + integrity hash) and `ep` (the author's content as semantic **EP
points**, group → vector → point; `text` = the grounded extract — the core — and
`subject/relation/object` = the relation overlay for extrapolation). **Everything else is
derived JIT and never stored** — the cognitive model, playbook, source table and the
manifest are `render` views, not files.

**The LLM never touches the DB or the shell directly. The only interface is the contour:**
`scripts/loop.py`. Every read is a drill-down command; every write is a validated `import`
that yields a log; representations come from `render`. See `ARCHITECTURE.md` for invariants
and `reference/04-clone-runtime.md` for the cycle.

```
clones/<author-slug>/
  clone.db        CANONICAL — SQLite: meta + ep (+ ep_fts), CHECK/FK/NOT-NULL enforced. The one center.
  raw/<id>.srt    timecoded transcript (audio/video) — source material, referenced by meta.raw_path + hash
  raw/<id>.md     clean text per source — source material (books excepted)
  runs/<id>/      per-intent contour artifacts: intent.md · selection.tsv · delivery.md · answer.md · log.jsonl
  config.json     STATE only: chat_language, name variants (the few facts not derivable from the corpus)
```

Derived **on demand** by `loop.py render` (printed, never stored): the source table, the
cognitive map (`render brain`), the playbook (`render playbook`), the contract (`render
manifest`). Build / import / verify operations emit **logs**, not duplicate files. There is
**no `evidence.jsonl`, no brain `.md`, no `manifest.json`** — those were copies of the canon.
All paths are relative to the user's working directory, so the clone ships with their project.

---

## Guardrails

- **No fabrication.** Every EP `text` in the `ep` table must be real and traceable to its source (`backing` + deep-link). Never invent citations. An answer may cite only EP ids delivered this run (`verify` enforces it). If you don't have an EP, say so.
- **Label inference.** Documented view ≠ predicted view. Predictions must be marked and confidence-rated.
- **Report gaps, never hide them.** If a source couldn't be transcribed or a topic isn't covered, state it.
- **Public data only; this is a model, not the person.** See `reference/ethics.md`.
- **Think, don't mimic.** The value is reproducing *reasoning*, not parroting catchphrases.
