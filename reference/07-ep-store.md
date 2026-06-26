# EP-store (v2) — the append-only relation layer

> **Status: canonical.** The EP point IS the unit of canon — it lives as a row in the
> `ep` table of `clone.db`, reached only through the contour. There is no separate
> `evidence.jsonl` or `cognitive-model.md`; the "brain" is `render brain` over these rows.
> Grounding is unchanged: every EP carries `text` + `backing` + a deep-link, and CHAT-mode
> live-grounding re-opens the real source. This doc specifies the EP **shape** (a row in the
> `ep` table) and the **append-only delta cycle** — all through the contour: `context`
> (pressure) → `smoke` (dry-run) → `import` (append). The old file-based scripts (`ep_*.py`,
> `.Ep.md` vectors, `entities.jsonl`) are retired; their semantics now live in the contour
> over the table.

## What it is

Any piece of an author's thinking is stored as an **extract point (EP)** — an
N-dimensional relation between meaningful entities:

```
[head] -(relation)-> [tail] | dim:val | dim:val …
```

This is the same shape the belief graph already used (`belief → because → consequence`),
made first-class, machine-parseable, and **append-only** so the clone can grow source
by source without a full rebuild.

Three levels (markdown-light — no graph DB, per the skill's minimalism):

```
GROUP  ──contains──>  VECTOR  ──contains──>  EP (points)
(grp column)         (vector column)        (one row each)
```

- **Group** (`grp`) — a broad region. Approximates a theme. Holds no EPs directly.
- **Vector** (`vector`) — a cluster whose name approximates the EPs inside it. Only vectors hold EPs.
- **EP** — one row: a relation (`subject –relation→ object`) + grounded `text`, evidence `backing`, confidence, and time.

The EP-store is **the `ep` table**: the accumulated, append-only graph for the author.

## Why it earns its place (vs just `cognitive-model.md`)

- **Incremental updates.** A new source becomes a *delta* reconciled against the `ep` table,
  not a reason to re-derive the whole model.
- **Entity discipline.** One canonical id per node ⇒ sources actually connect; no
  `Higgsfield` / `Higgsfield AI` / `HF` fragmentation.
- **Confidence from data.** Repeated signals accumulate; **density complements** the
  hand-assigned `H/M/L` and the existing "3+ independent sources" rule.
- **Append-only ⇒ free provenance & rollback.** No destructive edits, ever.

`render brain` is the human-readable, single-read view of these rows; the belief graph is a
**render** of the `ep` table, not a parallel hand-maintained copy.

---

## Where it lives — the `ep` table (no files)

There is no `ep/` folder, no `.Ep.md` vectors, no `entities.jsonl`. An EP is a **row** in the
`ep` table of `clone.db` (schema in `scripts/schema.sql`): **group** → `grp`, **vector** →
`vector`, the triple → `subject`/`relation`/`object`, the grounded extract → `text`, plus
`backing` / `t_start` / `deeplink` / `confidence` / `as_of`. A delta is a transient `.jsonl`
(one EP per line) staged for `smoke` → `import`; nothing persists outside the table.

## The EP shape (one delta line → one row)

A delta line is a JSON object; on import it becomes a row. The conceptual EP:

```
[distribution] -(beats)-> [product] | because:products die unshipped | backing:e0007 | conf:H | as_of:2025
   subject       relation   object      text / dimension                 backing       confidence  as_of
   routed by the `grp` + `vector` fields (a new grp/vector is created implicitly on import)
```

| Field | Meaning |
|---|---|
| `[head] -(rel)-> [tail]` | the triple (required, first field) |
| `k:v` (free) | a **dimension** — any qualifier: `because`, `when`, `value`, `condition`, … |
| `backing:e0007,e0012` | **required** — evidence ids this EP rests on (the grounding bridge) |
| `conf:H\|M\|L` | confidence (same scale as cognitive-model) |
| `as_of:2025` | time tag (recency wins at query) |
| `density` | **JIT** — count of EPs sharing this `subject+relation` in the vector; computed by `render brain`, never stored |
| `grp` / `vector` | placement — `import` appends to that vector, creating it (and the group) implicitly if new |
| `thesis`/`kind` | `kind` marks the EP type (belief/stance/procedure/…); a stance is an author **opinion**, not a bare fact |

**Hard rule: no EP without grounding (`backing`/`deeplink`/`t_start`).** An ungrounded EP is
forbidden — it would let the graph drift from the person (the exact failure the minimalism
principle warns against). `smoke` rejects ungrounded EPs before `import`.

## Entities

- One **canonical id** per node, **kebab-case ASCII** (single naming convention for
  the whole store): `viktor-savin`, `higgsfield`, `go-to-market`.
- Entities are the **distinct `subject`/`object` values in the `ep` table** — no separate
  registry. `context` lists them as the canonical set to reuse; `smoke` flags a delta entity
  not seen before so the LLM folds it onto an existing one (or keeps it if truly new).

---

## The delta cycle (how a new source enters the `ep` table)

All through the contour (`loop.py`) — no separate file scripts:

```
raw source
  │
  ▼  (1) EXTRACT under pressure          ← LLM, fed the base's context
  │      `loop.py <slug> context`  dumps known entities + the vector map, so the delta
  │      is written in the base's language (reuse entities/vectors; new vector only if
  │      truly new). Output: a delta .jsonl — one EP per line, each grounded
  │      (`text` + `backing`/`deeplink`) and routed (`grp`/`vector`).
  ▼  (2) SMOKE                            ← deterministic, READ-ONLY, writes nothing
  │      `loop.py <slug> smoke <delta.jsonl>`
  │      reports: ungrounded EPs, bad kind/conf, id collisions, dangling source,
  │      route-vs-new-vector, new entities, + a merge preview. Exit 0 = clean. Fix & re-smoke.
  ▼  (3) IMPORT (= merge)                 ← validation-on-write, APPEND-ONLY
         `loop.py <slug> import <delta.jsonl>`
         inserts EP rows (a new `grp/vector` is created implicitly); the table only grows;
         bad rows rejected with a reason → log.
```

Entity normalization is handled by **pressure** (`context` surfaces canonical entities to
reuse) + **smoke** (warns when a delta entity wasn't seen before — fold it or keep it if
truly new). **Density is JIT** — the count of EPs sharing a `subject+relation` in a vector,
computed by `render brain`, never stored.

### Routing rule (step 1, the LLM's only judgement call)

For each EP, decide where it lands — gravity toward what exists, no forcing:

```
close to an existing vector's centroid?     -> route:<that vector>          (most EPs)
fits the group's theme but no single vector? -> new-vector:<group>/<name>
genuinely new domain?                        -> new-vector:<new-group>/<name>
```

Never force an EP into a vector it doesn't semantically belong to — a clean new vector
beats a polluted old one.

### Append-only invariants (enforced by `import`, checked by `smoke`)

- the `ep` table supports exactly two operations: **ADD-EP** and **CREATE-VECTOR**.
- **No delete, no overwrite, no de-dup.** Similar signals accumulate; `density` rises.
- Conflicts (same head+rel, different tail) **coexist**; recency wins at query time
  (consistent with the skill's recency rule and the cognitive-model's "Open tensions").
- `replace` and all edits happen on the **delta buffer only** — never on the `ep` table.

---

## Command contracts (the LLM needs only these I/O shapes)

The contour commands are the whole interface — the LLM only needs what to feed in.

| Command | In → Out |
|---|---|
| `loop.py <slug> context` | the `ep` table → entity list + vector map (extraction pressure) |
| `loop.py <slug> smoke <delta.jsonl>` | delta + table → report + exit code (read-only, writes nothing) |
| `loop.py <slug> import <delta.jsonl>` | clean delta → appended into the `ep` table (validation → log) |

(Entity folding/rename is handled at extraction time under `context` pressure and flagged by
`smoke`; there is no separate normalize/replace step.)

## Build & CHAT integration

- **BUILD (Phase 4):** extract each source's belief-graph edges / heuristics / stances as EP
  rows and `import` them — that *is* the brain. The belief-graph view is `render brain`. See
  `03-cognitive-model.md`.
- **Update the clone:** run the delta cycle above (`context → smoke → import`) instead of a
  full rebuild. See `04-clone-runtime.md`.
- **CHAT:** to gather priors for an answer, query the EP-store **by entity** (the
  registry maps entity → vectors), pull the relevant EPs, then ground their `backing`
  evidence ids live exactly as today. EP is the index; evidence stays the ground truth.
