#!/usr/bin/env python3
"""ep_merge — append a clean DELTA into main_db. Append-only.

CONTRACT (input/output only):
    in : a clean delta .Ep.md file (routed + grounded; pass ep_smoke first)
    out : EPs appended into ep/<group>/<vector>.Ep.md ; entities.jsonl updated
    scope: main_db grows. The only operations are ADD-EP and CREATE-VECTOR.
           Nothing is ever deleted, overwritten, or de-duplicated.

    $ python ep_merge.py ep/_delta/s042.Ep.md --ep-dir ep --registry ep/entities.jsonl

Behaviour:
  - route:group/vector       -> append the EP line to that existing vector file
  - new-vector:group/vector  -> create the vector (and group folder) then append
  - similar signals are NOT collapsed — they accumulate; `density` is recomputed as
    the count of EPs sharing the same head+rel in the vector (density = confidence)
  - the routing annotations (route/new-vector) are stripped on write; `src`+`backing`
    stay as provenance
  - entities.jsonl gains every head/tail (as canon) with the vector it now lives in
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from ep_entities import load_registry, save_registry
from ep_lib import parse_vector_text, load_vector, save_vector, Vector


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("delta", help="path to the clean delta .Ep.md buffer file")
    ap.add_argument("--ep-dir", default="ep", help="main_db ep/ directory")
    ap.add_argument("--registry", default="ep/entities.jsonl", help="entities.jsonl path")
    args = ap.parse_args(argv)

    ep_dir = Path(args.ep_dir)
    reg = load_registry(args.registry)
    delta = parse_vector_text(Path(args.delta).read_text(encoding="utf-8"))

    by_target = defaultdict(list)
    for ep in delta.eps:
        target = ep.target()
        if not target:
            print(f"SKIP (no target): {ep.head} -({ep.rel})-> {ep.tail}", file=sys.stderr)
            continue
        by_target[target].append(ep)

    added, created = 0, 0
    for target, eps in by_target.items():
        group, vector = target.split("/", 1)
        path = ep_dir / group / f"{vector}.Ep.md"
        if path.exists():
            v = load_vector(path)
        else:
            v = Vector(group=group, vector=vector, centroid="")
            created += 1
            print(f"CREATE vector {target}  (set its # centroid:)")

        for ep in eps:
            ep.route = None
            ep.new_vector = None
            v.eps.append(ep)
            added += 1
            reg.add(ep.head, vector=target)
            reg.add(ep.tail, vector=target)

        # density = number of signals sharing the same head+rel in this vector
        counts = defaultdict(int)
        for ep in v.eps:
            counts[ep.key()] += 1
        for ep in v.eps:
            ep.density = counts[ep.key()]

        v.refresh_entities()
        save_vector(path, v)

    save_registry(args.registry, reg)
    print(f"\nmerged: {added} EP appended · {created} vector(s) created")
    return 0


if __name__ == "__main__":
    sys.exit(main())
