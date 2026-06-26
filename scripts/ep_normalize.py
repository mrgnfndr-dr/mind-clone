#!/usr/bin/env python3
"""ep_normalize — fold entity surface-forms in a DELTA to canonical ids.

CONTRACT (what the LLM needs to know — input/output only, not the logic):
    in : a delta .Ep.md file  +  ep/entities.jsonl
    out : the same delta with every [head]/[tail] rewritten to its canonical id
    flag: --write applies in place; without it, prints a dry-run diff
    scope: operates on the DELTA buffer ONLY. main_db is never touched.

    $ python ep_normalize.py ep/_delta/s042.Ep.md --registry ep/entities.jsonl --write

Unknown entities (no alias match) are left as-is and reported, with a proposed
kebab-case canon — the LLM/user decides whether to register them or `replace` them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ep_entities import load_registry, slugify, norm_surface
from ep_lib import parse_vector_text, is_kebab


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("delta", help="path to the delta .Ep.md buffer file")
    ap.add_argument("--registry", default="ep/entities.jsonl", help="entities.jsonl path")
    ap.add_argument("--write", action="store_true", help="apply changes in place")
    args = ap.parse_args(argv)

    reg = load_registry(args.registry)
    v = parse_vector_text(Path(args.delta).read_text(encoding="utf-8"))

    changes, unknown = [], {}
    for ep in v.eps:
        for attr in ("head", "tail"):
            surface = getattr(ep, attr)
            canon = reg.canon_for(surface)
            if canon and canon != surface:
                changes.append((surface, canon))
                setattr(ep, attr, canon)
            elif not canon and not is_kebab(surface):
                unknown[norm_surface(surface)] = (surface, slugify(surface))

    for old, new in changes:
        print(f"  normalize  {old!r} -> {new!r}")
    for surface, proposed in unknown.values():
        print(f"  UNKNOWN    {surface!r}  (propose canon: {proposed!r} — register or replace)")
    print(f"\n{len(changes)} folded, {len(unknown)} unknown entit{'y' if len(unknown)==1 else 'ies'}.")

    if args.write:
        v.refresh_entities()
        Path(args.delta).write_text(v.to_text(), encoding="utf-8")
        print(f"written: {args.delta}")
    else:
        print("(dry-run — pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
