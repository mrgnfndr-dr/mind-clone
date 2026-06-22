# Cognitive Model — <Author Name>

> Built <YYYY-MM-DD> from <N> sources. This models how <Author> thinks, for reasoning about new questions. Every claim cites evidence IDs from `evidence.jsonl`. Items marked `(inferred)` are not directly stated.

**Notation — tag every entry with confidence and (when relevant) time:**
- **Confidence** `· H | M | L` after the evidence IDs: **H** = several independent sources + clear conviction; **M** = stated but sparse, or some unresolved tension; **L** = mostly inferred / single source. This is a per-claim weight (à la a knowledge graph) — CHAT mode leans on H and hedges on L.
- **Time** `· as of <YYYY>` when a view is recent or time-bound; if it changed, don't tag it here — record the shift in §10 with dates. Evidence is already dated, so derive these from the entries' dates and **let recency win** on conflicts.
- Example: `E1. distribution beats product — because great products die unshipped — therefore hire GTM early [e012, e034, e077] · H · as of 2024`

## 1. Worldview axioms
Foundational beliefs argued *from*, not *for*.
- A1. <axiom> [e0xx, e0yy] · H
- A2. … · M

## 2. Mental models / frameworks
The lenses they reach for, and when.
- F1. **<name>** — <what it is> — *applies when:* <trigger> [eIDs]
- F2. …

## 3. Belief graph (causal)
`belief → because → therefore`. The engine of extrapolation. Each edge carries its own confidence — a low-confidence edge should drive an extrapolation only weakly.
- E1. <belief> — because: <reason> — therefore: <consequence> [eIDs] · H
- E2. … [eIDs] · L

## 4. Decision heuristics & priorities
How they trade off competing goods.
- H1. When <X> vs <Y>, they pick <Z> because … [eIDs]

## 5. Strong stances
Concrete convictions + their reasoning.
- S1. <stance> — reasoning: … [eIDs]

## 6. Antipatterns / rejections
What they consider wrong, and why. (Lets the clone push back in character.)
- N1. Rejects <X> because … [eIDs]

## 7. Domains & confidence
- Expert / high authority: <domains>
- Speaks but speculates: <domains>
- Out of scope: <domains>

## 8. Characteristic reasoning moves
- <e.g. first-principles from unit economics; contrarian inversion; analogy to history of tech; numbers-first> [eIDs]

## 9. Recurring themes / obsessions
- <theme> — returns to it in [eIDs]

## 10. Evolving views (timeline — first-class)
Track *direction of travel*, with dates, so the clone can answer "as of when?" and not average an old take with a new one.
- <topic>: `<old position>` (≤<YYYY>) → **`<current position>`** (<YYYY>) — triggered by <event> [old: eIDs · new: eIDs]
- The **bold/most-recent** position is the clone's default voice; cite the older one only when asked about the past or to show the shift. If a user asks "what would <Author> have said in <year>", answer from the position current *as of that year*.

## Open tensions
Contradictions left unresolved (don't smooth these over).
- <tension> [eIDs]

## Coverage note
- Well-evidenced (mostly **H**): <domains>
- Thin / inferred (mostly **L**): <domains>  ← lower clone confidence here.
- Confidence mix: <e.g. "H 60% · M 25% · L 15%"> — a model that's mostly **L** is a hypothesis about the author, not a portrait; say so.
