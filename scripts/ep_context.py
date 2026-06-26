#!/usr/bin/env python3
"""ep_context — dump main_db's entity list + vector map as PRESSURE for extraction.

CONTRACT (input/output only):
    in : ep/ dir (main_db)  +  ep/entities.jsonl
    out : a compact text context (stdout) to paste into the LLM prompt BEFORE it
          extracts/routes a new delta — so the new source is spoken in the language
          of the existing base (reuse entities, reuse vectors) instead of in a vacuum.

    $ python ep_context.py --ep-dir ep --registry ep/entities.jsonl

This is the mechanism that gives discipline: the LLM sees what already exists and is
pushed to land the delta in existing entities/vectors when it genuinely fits, and to
spin up a new vector/group only when the meaning is actually new.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ep_entities import load_registry
from ep_lib import load_vector, iter_vector_files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ep-dir", default="ep", help="main_db ep/ directory")
    ap.add_argument("--registry", default="ep/entities.jsonl", help="entities.jsonl path")
    args = ap.parse_args(argv)

    reg = load_registry(args.registry)

    print("== KNOWN ENTITIES (reuse these canonical ids; don't invent near-duplicates) ==")
    canons = reg.all_canons()
    if canons:
        print(", ".join(sorted(canons)))
    else:
        print("(none yet — first ingest)")

    print("\n== VECTOR MAP (land EPs here when they fit; new-vector only if truly new) ==")
    any_v = False
    for vf in iter_vector_files(args.ep_dir):
        any_v = True
        v = load_vector(vf)
        ents = ", ".join(v.entities[:8]) + (" …" if len(v.entities) > 8 else "")
        print(f"  {v.group}/{v.vector}  — {v.centroid or '(no centroid)'}")
        print(f"      entities: {ents}")
    if not any_v:
        print("(no vectors yet — first ingest)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
