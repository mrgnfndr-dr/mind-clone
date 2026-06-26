# Phase 4b — Playbook (procedural methodology)

Sibling to Phase 4. Where `cognitive-model.md` captures **how the author thinks**, the playbook captures **what the author tells people to do** — the concrete, step-by-step methodology they teach. Build it when the corpus contains how-to / instructional content.

Input: the corpus via the contour (`loop.py`: `fts`/`map`/`get`) + `raw/*` (re-read transcripts so step-level detail — exact numbers, sequences, verbatim scripts — survives). Output: **`kind:"procedure"` EP points** (each step/number/script a grounded EP with deep-link); surfaced by **`render playbook`**, not a stored `playbook.md`.

**Re-mine the raw transcripts.** Distillation in Phase 3 optimizes for *reasoning*, so it can drop the exact numbers, sequences, and verbatim scripts a playbook lives on. Transcripts/text are saved to `raw/` by default, so **re-read `raw/<id>.srt` / `raw/<id>.md` for procedural detail** the distillate missed, and pull the precise `t_start` for any step from the `.srt` so every step gets an exact-minute deep-link. **Books** are the exception — only their distillate is kept by default; if a book wasn't archived, work from its evidence-table rows (`clone.py get`/`fts`) and **note in the Coverage section that the book's step-level coverage is limited to distilled evidence**.

## When to build it (and when to skip)

- **Build it** when the author *teaches a procedure* — courses, tutorials, "here's how I do X", step lists, tactics, numbers, templates. (e.g. an Instagram-growth coach, a sales trainer, a fitness method.)
- **Skip it** (and say so in the build summary) when the author is a pure thinker/commentator with no prescribed methodology — there's nothing procedural to extract, and a fabricated playbook would be worse than none. Note in `manifest.json` `coverage_gaps` that no methodology was found.
- A corpus can support **both** a rich cognitive model *and* a rich playbook — that's the normal case for teachers. Build both; cross-link them.
- **A book, if present, is usually the single best playbook source** — it's where authors lay out their method most completely and in order. Lean on `kind:"procedure"` evidence harvested from it; cite by chapter/page (books have no deep-link — see `02-harvest.md` → Books).

## Playbook vs cognitive model — keep them distinct

| | Playbook | Cognitive model |
|---|---|---|
| Answers | "**How** do I do X?" | "**Why** / what would the author think about X?" |
| Content | steps, tactics, checklists, numbers, scripts | axioms, frameworks, belief graph, heuristics |
| Mode of use | execute the method | reason like the author on novel questions |
| When CHAT uses it | how-to, "give me the steps", "what's his method for…" | advice on new situations, predictions, "why does he believe…" |

Don't duplicate: if something is a *reason* ("distribution beats product because…"), it belongs in the cognitive model; if it's an *instruction* ("post a Reel daily for the first 30 days"), it belongs in the playbook. When a step has a reason, put the step here and **link** to the belief in `cognitive-model.md` rather than re-explaining it.

## Fidelity first — the playbook must match the author's actual method

The cardinal failure mode: a playbook that *reads* plausible but has drifted from what the author actually teaches — invented steps, a re-ordered sequence presented as theirs, generic best-practice silently mixed in, or your connective tissue passed off as their method. That's worse than a thin playbook, because it's confidently wrong and the user can't tell. Guard against it:

- **Every step traces to the text.** Each step, number, and rule carries evidence IDs + locator (Ch./p. or deep-link). A step with no backing citation does not go in the playbook — it goes in your head as a question, not on the page.
- **Mark what's yours vs the author's.** If the author gives steps but no explicit order, the order is `(inferred sequence)`. If you bridge two steps with a connection the author never states, mark that `(inferred)`. The reader must always be able to see where the author stops and your reconstruction starts.
- **No imported best-practice.** Do not complete the author's method with generic domain knowledge (what "everyone" does for Instagram growth). If the author doesn't say it, it isn't in their playbook — note the gap instead.
- **Preserve their conditions and caveats.** Methods have "do X *only if* Y" qualifiers. Dropping the condition turns a careful method into a wrong absolute. Capture the caveat with the step.
- **Self-check before finalizing:** for each section, ask "could the author open this page and recognize it as *their* method, in their order, with their numbers?" If any step would make them say "I never said that / not in that order," fix or flag it.
- **Quote-anchor the spine.** For each major step, keep at least one short verbatim line from the author next to your structured version — so the user can read the structure *and* verify it against the author's own words in one glance.

## Extraction discipline

1. **Concrete over abstract.** The playbook's value is specificity. Capture exact numbers, frequencies, thresholds, tool names, and verbatim templates/scripts. "Post consistently" is weak; "post 1 Reel/day for 30 days, hook in the first 3 seconds" is the playbook.
2. **Preserve the author's own sequence.** If they give an explicit order, keep it. If you reconstruct an order, mark it `(inferred sequence)`.
3. **Cite every step with a deep-link.** Each step, tactic, number, and script must carry its evidence IDs and, for audio/video, a `deeplink` to the exact minute (see `02-harvest.md` → Timestamps & deep-links). Several sources for the same step → list them all, most recent first.
4. **Recency wins.** Methods evolve — if the author taught X in 2022 and X′ in 2025, the **current** method is X′; note the change, don't average. Date every step.
5. **No fabricated steps.** If the author never specifies a step, don't invent it to make the method look complete. Mark genuine gaps in the Coverage note. A short, honest playbook beats a padded one.
6. **Quote scripts/templates verbatim.** Hooks, message templates, formulas, content structures the author hands out go in exactly, in quotes, with the source link.
7. **Capture "don't do this."** The author's stated mistakes/anti-tactics are as actionable as the positive steps — collect them in "Common mistakes."

## Quality bar

- A user should be able to **execute** the method from `playbook.md` alone — open it, follow the steps, click a deep-link when they want the author's exact words on any step.
- Every concrete number lands in the Section 5 quick-reference table for fast lookup.
- Honest Coverage note at the bottom: which steps are well-documented vs thin/inferred vs absent. This feeds confidence calibration in CHAT mode.
