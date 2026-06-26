# Phase 4c — Faithfulness check (held-out)

A cheap, honest sanity test: does the clone actually reproduce the author's real positions, or has the cognitive model drifted into confident-but-wrong fabrication? Runs after the model + playbook are built, before finalize.

> **Why this exists:** an LLM has "jagged intelligence" — it can sound exactly right and be wrong. A clone built from a lossy abstraction is exactly where that bites. This check makes the failure *visible* instead of trusting fluency. It is a **smoke test, not proof** — small-N and gameable. Treat a pass as "no obvious drift found," never as "verified accurate." **Never tune the model to pass it** (that's training on the test set); if a probe fails, fix the *model*, don't delete the probe.

## Method — hold out, predict, compare

1. **Pick 5–10 probes.** Choose evidence entries where the author states a **clear, specific, checkable position** (a `belief` / `stance` / `prediction` / `procedure` with a concrete claim). Spread them across the author's main domains. These real quotes are the **ground truth**.
2. **Hold each one out.** For a probe, temporarily set aside that evidence entry *and* any near-duplicates of it, so the answer isn't sitting in front of you.
3. **Predict cold.** Using only the rest of the cognitive model (+ remaining evidence), answer the probe's eliciting question *as the clone* — reason it through, don't peek at the held-out quote.
4. **Compare to ground truth.** Score the prediction against what the author actually said:
   - **match** — same position and substantially the same reasoning,
   - **partial** — right direction, missing or off on a key qualifier,
   - **miss** — model had nothing useful / punted,
   - **contradiction** — model confidently asserted the *opposite* of the author. ← the dangerous one; weight it heavily.
5. **Score & surface.** Report the rate (e.g. "7/10 match, 2 partial, 1 contradiction") with the contradicting/missed probes shown in full, so the user sees *where* the clone is unreliable.

## What the result means (calibration, not a grade)

- **Contradictions are the signal that matters** — they reveal where the model invents a position the author doesn't hold. Investigate each: usually an over-reached EP relation or a recency/conflict that was mis-resolved. Fix the EP (tighten or remove the offending relation), then re-probe.
- **Misses in a domain** usually mean **thin coverage** there → lower the clone's confidence in that domain (note it in `config.json` coverage gaps), don't paper over it.
- **A high match rate is not a guarantee** — it only covers the probes you happened to pick. Say so in the summary.
- Domains that score badly here should directly **lower confidence** in CHAT mode for that area.

## Output

- A **faithfulness log** in `runs/<id>/` — the probes, each held-out question, the clone's cold prediction, the real EP `text`, and the verdict; plus the headline score and a one-line honest caveat. (A log of an operation, not a stored prose file.)
- `config.json` — any domains flagged low-confidence from the result.
- Build summary — one line: `Faithfulness (smoke test): 7/10 match, 1 contradiction (see the run log). Indicative only.`

## In CHAT mode

The user can ask **"how faithful is this clone?"** or **"spot-check yourself"** at any time → run a few fresh held-out probes live and report the result with the same honest caveat. Also a good move before the clone is used for anything that matters.
