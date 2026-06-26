# Phase 4 — Cognitive model (the brain)

This is the core of the skill. You are not summarizing *what the author said* — you are reconstructing *how the author thinks*, so the clone can reason about questions the author never addressed.

Input: `evidence.jsonl` + `raw/*`. Output: `cognitive-model.md`, `reasoning-traces.md`, `persona.md` (use `templates/cognitive-model.md` and `templates/persona.md` for structure).

## Principle: capture reasoning, not slogans

The model's job is to encode the author's **priors and reasoning machinery**, which the LLM then runs on new inputs. Voice/tone is secondary (it lives in `persona.md`). The brain lives in the structures below.

## Principle: minimalism — a lean index over evidence, not an elaborate theory

The cognitive model is a **thin, readable map** that points the LLM at the right priors — it is *not* a grand unified theory of the person. The heavy lifting at answer time is done by **retrieval + live-grounding against the raw sources** (see `04-clone-runtime.md`), not by this document. So:

- **Lean toward the evidence, away from invented structure.** Every axiom/edge/heuristic must earn its place with real citations. If you're tempted to add structure the sources don't clearly support, *don't* — leave it out and let retrieval surface the raw passage instead. An elaborate belief graph that isn't grounded is lossy and brittle; it drifts from the person and reads as confident-but-wrong.
- **Build the belief graph only as far as it buys extrapolation.** Its one job is reasoning about questions the author never addressed. Capture the edges that genuinely enable that; don't manufacture a dense graph for its own sake.
- **Thin is fine; padded is a bug.** A short model with sharp, well-evidenced entries beats a long one full of weakly-supported inferences. Cut anything you wouldn't stake a citation on.
- **Keep it forkable and single-read.** Someone should be able to read the whole file in one pass and start reasoning. Prefer one crisp example over exhaustive enumeration.

When in doubt between "add a clever inferred structure" and "let the clone retrieve the raw quote at answer time" — choose retrieval. The raw source is the ground truth; this file is just the index.

## What to extract (each item must cite evidence IDs)

1. **Worldview axioms** — foundational beliefs the author treats as given and argues *from*, not *for*. The deepest layer; everything else derives from these.
2. **Mental models / frameworks** — the recurring lenses they apply to problems (their thinking tools). Name each, state when they reach for it.
3. **Belief graph (causal beliefs)** — `belief → because → consequence` chains. This is what lets the clone extrapolate. Capture as explicit edges:
   - `B: "distribution beats product" — because: "great products die unshipped to users" — therefore: "hire for go-to-market early"`
   - **EP-store (v2, additive):** under `--ep`, these edges are *also* persisted as append-only extract points in `ep/` — `[distribution] -(beats)-> [product] | because:… | backing:[ids] | conf:H` — so updates are incremental and the same edge can accumulate signal across sources (density = confidence). The belief-graph here then reads as a **render** of `ep/`, not a second hand-maintained copy. Every EP must carry `backing:` evidence ids (no ungrounded EPs) — this keeps the relation layer a thin, grounded index, never the "elaborate graph that drifts" the minimalism principle warns against. Format + pipeline: `reference/07-ep-store.md`.
4. **Decision heuristics & priorities** — how they trade off competing goods (speed vs quality, focus vs optionality). The rules they use to *choose*.
5. **Strong stances** — concrete opinions they hold with conviction, each with the reasoning behind it and evidence IDs.
6. **Antipatterns / rejections** — what they consider wrong, and *why*. Often more diagnostic than what they endorse. The clone must be able to push back the way the author would.
7. **Domains & confidence calibration** — where they speak as an expert vs where they speculate. Bounds the clone's authority.
8. **Characteristic reasoning moves** — *how* they argue: first-principles? analogy? contrarian inversion? numbers-first? steelman-then-reject? This shapes the *process* of every clone answer.
9. **Recurring themes / obsessions** — what they keep returning to. Signals what they'll weight heavily.
10. **Evolving views** — where they changed their mind, and what triggered it. Lets the clone reason about direction of travel.

## Tag every entry: confidence + time

Borrowed from knowledge-graph best practices (per-node uncertainty weights + temporal evolution of views), but kept markdown-light — no graph DB.

- **Confidence weight `· H | M | L`** on every axiom, framework, belief edge, heuristic, and stance, after its evidence IDs. **H** = ≥3 independent sources + clear conviction; **M** = stated but sparse, or sits in an unresolved tension; **L** = mostly your inference / a single source. This makes the model's soft spots *visible per claim* instead of hiding them in prose — and CHAT mode uses it directly: lean on **H**, hedge/flag **L**, let a low-confidence belief drive an extrapolation only weakly. A confidence tag is **not** a substitute for the `(inferred)` mark — an inferred claim is `L` *and* `(inferred)`.
- **Time `· as of <YYYY>`** when a view is recent or time-bound. Evidence is already dated; derive the tag from the entry dates. If a view **changed**, don't just tag it — record the trajectory in §10 (Evolving views) as `old (≤YYYY) → current (YYYY)`, and let **recency win**: the current position is the clone's default, the old one is cited only for "what did they think back then" / to show the shift. This lets the clone answer **"as of when?"** instead of averaging a 2019 take with a 2026 one.

Don't inflate confidence to look authoritative — an honest `L` is worth more than a confident-but-wrong `H`. The faithfulness check (Phase 4c) will expose over-rated claims as contradictions.

## Discipline: signal vs noise (borrowed from style-extraction practice)

- Keep a pattern only if it appears across **multiple independent sources** or is stated with clear conviction. One-off remarks are not the brain.
- Distinguish a **considered position** from an offhand aside or a joke. Don't elevate noise to an axiom.
- Note **tensions/contradictions** rather than smoothing them over — real thinkers hold some. Record them under "Open tensions".
- **Recency wins.** When two well-evidenced positions conflict, the **more recent** one is the author's current view — people evolve. Date every entry. In "Evolving views" / "Open tensions", state which view is *current* and which is *superseded*, with dates. Don't average a 2021 take with a 2026 take as if equal.
- Every entry carries `[e0007, e0012]`-style backing. An entry with no evidence is a hypothesis — mark it `(inferred)` or drop it.

## Reasoning traces (`reasoning-traces.md`)

Pick 5–10 cases where a source shows the author reasoning to a conclusion. For each, reconstruct the **chain**, not just the conclusion:

```
Trace T3 — "Why hire generalists early" [e0012, e0019]
Trigger/question the author faced: ...
Step 1 (axiom invoked): early-stage = high uncertainty
Step 2 (framework): optionality > specialization under uncertainty
Step 3 (heuristic): hire people who can change roles
Conclusion: hire generalists first, specialists after PMF
Characteristic move: first-principles from the uncertainty premise
```

These teach the clone the author's *process*. They are the highest-value artifact for answering novel questions — invest in them.

**Mark provenance per step.** Where the author *explicitly* stated the chain, cite the evidence. Where you *connected* separate beliefs into a chain he didn't fully spell out, label that step `(reconstructed)`. A trace that is mostly reconstruction is a hypothesis about his reasoning, not a record of it — say so. Prefer building traces from `kind:"reasoning"` evidence (whole chains) over stitching one-liners.

## Persona (`persona.md`) — secondary

Short: bio, current/past roles, domains of expertise, audience, and a few voice notes (sentence rhythm, characteristic phrases, what they avoid). Keep it light — it colors delivery; the brain does the thinking.

## Output quality bar

- Designed for a single read: an agent should be able to internalize `cognitive-model.md` in one pass and start reasoning. Principle-first, with one sharp example each — not an exhaustive dump.
- Honest coverage note at the bottom: which domains are well-evidenced vs thin. This directly feeds confidence calibration in CHAT mode.
