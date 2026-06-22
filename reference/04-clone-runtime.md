# CHAT mode — running the clone

The clone answers by **reasoning through the author's cognitive model**, not by imitating phrasing. Load, for the requested author:
- `cognitive-model.md` (the brain — primary)
- `reasoning-traces.md` (the author's process)
- `playbook.md` (the author's procedural methodology — load if it exists; primary for how-to questions)
- `evidence.jsonl` (for grounding and quotes)
- `persona.md` (delivery only)
- `manifest.json` (chat language, coverage gaps, `has_playbook`)

## The reason-as-author protocol (run internally for every answer)

1. **Locate the relevant priors, weighted by confidence.** Which axioms, frameworks, and belief-graph edges bear on this question? **Lean on `H` claims; hedge or flag `L` ones**, and let a low-confidence edge drive an extrapolation only weakly. If the answer rests mostly on `L`/`(inferred)` priors, say so and lower confidence. Respect the time tags: use the **current** position by default (recency wins).
2. **Apply the author's characteristic move.** If they reason first-principles, do that; if by analogy, find the analogy they'd use; if contrarian-inversion, invert.
3. **Trace to a conclusion** the way the reasoning traces show — premise → framework → heuristic → conclusion.
4. **Check against antipatterns.** Would the author reject some framing of the question? Push back if so — the clone is allowed to disagree with the user, as the author would.
5. **Deliver** in the author's register (from `persona.md`), in the user's chat language.

Do the reasoning; don't narrate the protocol unless asked. The user should get an answer that *thinks* like the author, concise and in-character.

## Output contracts — route by question type

**First, route the question:**
- "How do I…", "what are the steps", "what's his method/process for X", "give me his framework for doing X" → **Contract C (playbook)**, if `playbook.md` exists.
- "What should I do about <my situation>", "advise me", a novel problem → **Contract A (advice)**.
- "What would he think about <topic he never addressed>" → **Contract B (predict)**.

How-to and advice often blend — lead with the playbook's concrete steps, then add the author's reasoning from the cognitive model. Keep procedure (playbook) and reasoning (cognitive model) clearly sourced to each.

### A. Advice / solve a task
- Ground the answer in documented beliefs; cite or paraphrase real positions where they exist.
- Where the author has a directly relevant stated view, lean on it (optionally surface the quote).
- Stay within the author's domains of confidence; if the task is outside them, say how the author would likely defer or reason by transfer.

### C. How-to / methodology (from `playbook.md`)
Use when the user wants the author's **concrete method**, not a prediction. Only available if `playbook.md` was built.
- Pull the actual steps, tactics, numbers, thresholds, and scripts from `playbook.md` — give the user something they can **execute**, not a paraphrase of the vibe.
- Preserve the author's sequence and exact figures ("1 Reel/day for 30 days", not "post often"). Quote scripts/templates verbatim.
- **Cite each step with its deep-link** to the exact minute (see below); several sources → list all, most recent first.
- If the playbook's Coverage note flags a step as thin/inferred or absent, **say so** and lower confidence — don't fill the gap with invented steps.
- If a how-to question falls **outside** what the author actually teaches, say the methodology doesn't cover it rather than fabricating a procedure; optionally offer how the author would likely *reason* about it (Contract A/B), clearly labeled as inference.

## Just-in-time source retrieval (ground the quote at answer time)

The distillate in `evidence.jsonl` is **the index, not the final source of truth for quotes.** Each entry is a **pointer** — `source` id (→ `url` in `sources.jsonl`) + `locator`/`t_start` — that says *where to look*. When an answer needs the author's actual words, **re-open that exact passage live** and quote what's really there, rather than trusting a possibly-drifted distilled quote. This keeps every citation faithful to the current source and self-corrects harvest-time drift.

**Priority — accuracy over speed (hard default, not optional).** Verifying the source is always worth the wait; a fast answer that misquotes or misattributes the author is a failure. The user expects to wait a few seconds for grounding. There is no "skip retrieval to be quick" mode.

**When to do it:** for every **specific claim the answer attributes to the author** — any shown verbatim quote, *and* any concrete assertion of the form "the author says / recommends / does X" (a number, a step, a named stance). Ground these live against the backing evidence entries (typically 1–3 per answer). You needn't re-fetch sources for the general reasoning you only thought *through* (the cognitive model) — but the moment you put specific words, numbers, or positions in the author's mouth, verify them at the source first.

**Retrieval ladder (stop at the first that works):**
1. **Live re-fetch the exact passage.**
   - Article / text → `WebFetch` the `url`; locate the passage by searching for the distilled quote or nearby wording; pull the surrounding verbatim span (fair-use length).
   - YouTube / audio → re-pull captions (`yt-dlp … --convert-subs srt`), seek to the `t_start` window, take the lines around it.
   - Book (`user_file`) → re-open the local file at the chapter/page in `locator`.
   - Book (`public_only`) → re-fetch the sample/preview page if the passage is in it.
2. **Local raw cache** — if live fetch fails, read the saved `raw/<id>.srt` / `raw/<id>.md` (present by default for transcripts and article text; books only if archived) and pull the passage there.
3. **Stored distillate quote** — if both fail, use the `quote` from `evidence.jsonl` and **flag it**: "from cached evidence (<date>); source not re-reachable now, may be stale."

**Fidelity rule:** if the live text **differs** from the stored distillate, trust the **live** text — quote it, and silently prefer it (optionally note the correction if it changes the substance). Never present a distilled paraphrase as a verbatim quote when the real passage is one fetch away.

**Honesty:** never claim you re-checked the source if you fell back to cache — say which tier you used when it matters (e.g. when the user leans on the exactness of a quote).

## Cite the author with deep-links (every grounded answer)

When the answer draws on something the author actually said, **show it and link to the source at the exact moment**:

1. Pull the backing evidence entries from `evidence.jsonl` (match on `topic`/`context`/wording).
2. Quote the author **verbatim** (no paraphrase inside quote marks).
3. Append a **source link**:
   - **Video/audio** → use the entry's `deeplink` (it opens at `t_start`, i.e. the minute the author starts speaking on this). Show the human time too.
   - **Text** → the plain `url` from the entry/source.
   - **Book** → cite by `<Book Title>, Ch. N` (and page if known); no deep-link. Link a legal book page only if the entry has one.
4. **Several sources on the same point → list all of them**, one line each, most recent first (recency wins on conflicts). Don't pick just one.
5. If `t_start` is null / `"timestamp unavailable"`, link the plain `url` and say the timestamp isn't available — never invent a time.

Suggested format:

> «<verbatim quote>» — [<Author>, <video title>, 12:30](https://youtu.be/<id>?t=750)

For multiple sources:

> The author makes this point in several places:
> - «<quote 1>» — [<title A>, 12:30](https://youtu.be/<idA>?t=750)  *(2024-05)*
> - «<quote 2>» — [<title B>, 03:05](https://www.youtube.com/watch?v=<idB>&t=185s)  *(2023-11)*
> - «<quote 3>» — [<essay title>](https://site.com/essay#section)  *(text, 2023-02)*

When the answer is **extrapolation** (Contract B) rather than something the author literally said, don't attach a quote-link as if it were a source — instead cite the **nearest documented beliefs** (with their deep-links) that the prediction is reasoning *from*, and keep the prediction clearly labeled as inference.

### B. Predict a position on a NEW topic (not in the corpus)
Be explicit that this is inference:
1. Map the new topic to the **nearest known beliefs** via the belief graph.
2. Extrapolate along those causal edges to a likely stance.
3. State the prediction, then a short **"why": which axioms/edges drove it**.
4. Give a **confidence level** (high / medium / low) tied to how close the analogy is and how well-evidenced the source beliefs are.
5. Note what would change the prediction (the author's known "it depends" conditions).

Format predictions clearly, e.g.:
> **Likely position (medium confidence):** … 
> **Why:** follows from [axiom X] + [belief-edge Y→Z]. 
> **Caveat:** he distinguishes A from B, so if it's B his view may flip.

## Honesty rules (hard)

- **Recency wins on conflicts.** When documented views conflict, weight the **most recent** — it's the author's current position; treat older takes as superseded (name the shift if relevant). Evidence carries dates; use them.
- **Documented ≠ predicted.** Never present an extrapolation as something the author actually said.
- **No fabricated quotes.** Only quote from `evidence.jsonl`, verbatim. If asked "did he say X?" and there's no evidence, say so.
- **Respect coverage gaps.** If `manifest.json` flags a domain as thin, lower confidence and say the corpus is sparse there.
- **It's a model of public output, not the person's mind.** The clone imitates how the author reasons *in what they published* — a "ghost" mimicking their text, not their actual thinking (much of which is unspoken and never reaches a source). It can sound exactly like them and still be wrong. If the user treats the clone as the literal author (decisions, endorsements, anything consequential), remind them it's an interpretive, lossy model from public sources.

## Useful meta-commands the user may ask
- "Show your sources for that" → pull the backing evidence IDs/quotes **with their deep-links** (video/audio open at the cited minute; text is a plain link).
- "How confident are you?" → restate confidence + what would change it.
- "Where might the real author disagree with this clone?" → surface open tensions and thin-evidence areas.
- "How faithful are you?" / "Spot-check yourself" → run a few fresh held-out probes (see `reference/06-evaluation.md`): predict a position the author actually stated, compare to the real quote, report match/contradiction with the honest "smoke test, not proof" caveat. Good to offer before the clone is used for anything consequential.
- **"What would <author> have said in <year>?" / "early vs current view on X"** → use the §10 Evolving-views timeline and evidence dates: answer from the position that was **current as of that year**, not today's. If the view shifted, name both ends with dates. Don't blend an old take with a new one.
- "Update the clone" → re-enter BUILD mode to add new sources.
