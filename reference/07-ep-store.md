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
(folder)             (*.Ep.md file)         (one relation per line)
```

- **Group** — a folder of vectors. Approximates a broad region. **Holds no EPs directly.**
- **Vector** — one `.Ep.md` file whose **name approximates the cluster of EPs inside**
  (its `# centroid:` spells the approximation out). Only vectors hold EPs.
- **EP** — one relation, with its dimensions, evidence backing, confidence, and time.

The EP-store is **main_db**: the accumulated, append-only graph for the author.

## Why it earns its place (vs just `cognitive-model.md`)

- **Incremental updates.** A new source becomes a *delta* reconciled against main_db,
  not a reason to re-derive the whole model.
- **Entity discipline.** One canonical id per node ⇒ sources actually connect; no
  `Higgsfield` / `Higgsfield AI` / `HF` fragmentation.
- **Confidence from data.** Repeated signals accumulate; **density complements** the
  hand-assigned `H/M/L` and the existing "3+ independent sources" rule.
- **Append-only ⇒ free provenance & rollback.** No destructive edits, ever.

`cognitive-model.md` stays the human-readable, single-read brain; its belief-graph
section is a **render** of the EP-store, not a parallel hand-maintained copy.

---

## On-disk layout

```
clones/<slug>/
  evidence.jsonl                    # unchanged — grounding index, deep-links, live-fetch
  cognitive-model.md                # unchanged role — readable brain; belief graph = render of ep/
  ep/                               # main_db (append-only)
    entities.jsonl                  # canonical entity registry (canon + aliases + vectors)
    worldview/                      # a GROUP
      distribution-vs-product.Ep.md # a VECTOR
    business-ops/
      hiring-strategy.Ep.md
    _delta/                         # staging buffer (NOT a group — leading underscore)
      s042.Ep.md                    # one un-merged delta being checked
```

Anything under `ep/` whose path contains a part starting with `_` is **not** a group
(reserved: `_delta` staging). Vectors are `*.Ep.md`.

## The `.Ep.md` grammar (single source of truth: `scripts/ep_lib.py`)

Header (vector metadata):

```
# group: worldview
# vector: distribution-vs-product
# centroid: how distribution dominates product outcomes
# entities: distribution, product, go-to-market
```

One EP per line, pipe-delimited:

```
[distribution] -(beats)-> [product] | because:products die unshipped | backing:e0007,e0012 | conf:H | as_of:2025 | density:3 | thesis
```

| Field | Meaning |
|---|---|
| `[head] -(rel)-> [tail]` | the triple (required, first field) |
| `k:v` (free) | a **dimension** — any qualifier: `because`, `when`, `value`, `condition`, … |
| `backing:e0007,e0012` | **required** — evidence ids this EP rests on (the grounding bridge) |
| `conf:H\|M\|L` | confidence (same scale as cognitive-model) |
| `as_of:2025` | time tag (recency wins at query) |
| `density:N` | # of accumulated signals sharing this head+rel (set by merge) |
| `route:group/vector` | merge target — append to an **existing** vector |
| `new-vector:group/vector` | merge target — **create** this vector then append |
| `thesis` (flag) | marks an author **opinion**, not a bare fact |

**Hard rule: no EP without `backing:`.** An ungrounded EP is forbidden — it would let
the graph drift from the person (the exact failure the minimalism principle warns
against). `route`/`new-vector` are buffer-only routing hints; merge strips them.

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

- main_db supports exactly two operations: **ADD-EP** and **CREATE-VECTOR**.
- **No delete, no overwrite, no de-dup.** Similar signals accumulate; `density` rises.
- Conflicts (same head+rel, different tail) **coexist**; recency wins at query time
  (consistent with the skill's recency rule and the cognitive-model's "Open tensions").
- `replace` and all edits happen on the **delta buffer only** — never on main_db.

---

## Command contracts (the LLM needs only these I/O shapes)

The scripts are universal black boxes — the LLM doesn't need their internals or even
their language, only what to feed in. Each script's `--help` is its contract.

| Command | In → Out |
|---|---|
| `ep_context.py` | `ep/` → entity list + vector map (paste as extraction pressure) |
| `ep_normalize.py <delta> --write` | delta + registry → delta with canon entities |
| `ep_replace.py <delta> "from":"to" --write` | delta + pair(s) → delta with renamed entity |
| `ep_smoke.py <delta>` | delta + main_db → report + exit code (read-only) |
| `ep_merge.py <delta>` | clean delta → appended into main_db |

## Tests

`python tests/test_ep.py` — deterministic, no LLM. Covers format round-trip,
normalization, replacement, smoke checks (ungrounded/bad-route/clean), and
append-only merge incl. signal accumulation → density. Run it after any change to
`scripts/ep_*.py`.

## Build & CHAT integration (additive)

- **BUILD (Phase 4):** when `--ep` is set, after writing `cognitive-model.md`, emit the
  belief-graph edges as the initial main_db: one delta per source (or one bulk delta),
  routed into vectors, then merged. The belief-graph section of `cognitive-model.md`
  becomes a render of `ep/`. See `03-cognitive-model.md`.
- **Update the clone:** runs the delta cycle above instead of a full rebuild. See
  `04-clone-runtime.md`.
- **CHAT:** to gather priors for an answer, query the EP-store **by entity** (the
  registry maps entity → vectors), pull the relevant EPs, then ground their `backing`
  evidence ids live exactly as today. EP is the index; evidence stays the ground truth.
