#!/usr/bin/env python3
"""ep_smoke — dry-run a DELTA against main_db. Reports problems. Writes NOTHING.

CONTRACT (input/output only):
    in : a delta .Ep.md file  +  ep/ dir (main_db)  +  ep/entities.jsonl
    out : a report (stdout) + exit code (0 = clean, 1 = has errors)
    scope: read-only. Never merges, never edits anything.

    $ python ep_smoke.py ep/_delta/s042.Ep.md --ep-dir ep --registry ep/entities.jsonl

Checks (so you see problems BEFORE polluting main_db):
  ERROR  malformed EP line
  ERROR  EP with no `backing:` (ungrounded EP is forbidden — must point at evidence ids)
  ERROR  bad `conf:` (must be H|M|L)
  ERROR  EP with no target (needs `route:group/vector` or `new-vector:group/vector`)
  ERROR  route -> a vector that does NOT exist (use new-vector), or
         new-vector -> a vector that ALREADY exists (use route)
  WARN   entity not in registry and not kebab-case (normalize/replace first)
  INFO   conflict: same head+rel already in main_db with a different tail
         (kept anyway — append-only; both signals coexist, recency wins at query)
  INFO   merge preview: N add-to-existing / M new-vector / K new-group
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ep_entities import load_registry
from ep_lib import (
    parse_ep_line,
    load_vector,
    iter_vector_files,
    is_kebab,
    CONF_LEVELS,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("delta", help="path to the delta .Ep.md buffer file")
    ap.add_argument("--ep-dir", default="ep", help="main_db ep/ directory")
    ap.add_argument("--registry", default="ep/entities.jsonl", help="entities.jsonl path")
    args = ap.parse_args(argv)

    reg = load_registry(args.registry)

    # index of existing vectors and existing (head,rel)->tail claims in main_db
    existing_vectors = set()
    existing_groups = set()
    claims = {}  # (head,rel) -> list of (tail, "group/vector")
    for vf in iter_vector_files(args.ep_dir):
        v = load_vector(vf)
        tag = f"{v.group}/{v.vector}"
        existing_vectors.add(tag)
        existing_groups.add(v.group)
        for ep in v.eps:
            claims.setdefault(ep.key(), []).append((ep.tail, tag))

    errors, warns, infos = [], [], []
    add_existing = new_vec = new_grp = 0
    new_vector_targets = set()

    for i, raw in enumerate(Path(args.delta).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        try:
            ep = parse_ep_line(raw)
        except ValueError as e:
            errors.append(f"line {i}: {e}")
            continue
        if ep is None:
            continue

        if not ep.backing:
            errors.append(f"line {i}: ungrounded EP (no backing:) — {ep.head} -({ep.rel})-> {ep.tail}")
        if ep.conf and ep.conf not in CONF_LEVELS:
            errors.append(f"line {i}: bad conf:{ep.conf} (must be H|M|L)")

        target = ep.target()
        if not target:
            errors.append(f"line {i}: no route:/new-vector: target — merge can't place it")
        else:
            grp = target.split("/")[0]
            if ep.route:
                if target in existing_vectors:
                    add_existing += 1
                else:
                    errors.append(f"line {i}: route -> {target} does not exist (use new-vector)")
            elif ep.new_vector:
                if target in existing_vectors:
                    errors.append(f"line {i}: new-vector -> {target} already exists (use route)")
                else:
                    if target not in new_vector_targets:
                        new_vector_targets.add(target)
                        new_vec += 1
                        if grp not in existing_groups:
                            new_grp += 1
                            existing_groups.add(grp)  # avoid double-counting within delta

        for ent in (ep.head, ep.tail):
            if reg.canon_for(ent) is None and not is_kebab(ent):
                warns.append(f"line {i}: entity {ent!r} not in registry & not kebab — normalize/replace first")

        prior = claims.get(ep.key())
        if prior:
            diff = [t for (t, _) in prior if t != ep.tail]
            if diff:
                infos.append(f"line {i}: conflict — {ep.head} -({ep.rel})-> already has {diff} in main_db; both kept")

    for e in errors:
        print(f"ERROR  {e}")
    for w in warns:
        print(f"WARN   {w}")
    for inf in infos:
        print(f"INFO   {inf}")

    print(
        f"\nmerge preview: {add_existing} add-to-existing · {new_vec} new-vector · {new_grp} new-group"
    )
    print(f"result: {'CLEAN — safe to merge' if not errors else f'{len(errors)} ERROR(S) — fix before merge'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
