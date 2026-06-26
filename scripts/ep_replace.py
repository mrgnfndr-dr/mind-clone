#!/usr/bin/env python3
"""ep_replace — rename an entity inside a DELTA buffer.

CONTRACT (input/output only — the LLM doesn't need the internals):
    in : a delta .Ep.md file  +  one or more   "from":"to"   pairs
    out : the delta with every entity "from" replaced by "to" (head & tail)
    flag: --write applies in place; without it, prints a dry-run
    scope: DELTA buffer ONLY. main_db is append-only and is never edited.

    $ python ep_replace.py ep/_delta/s042.Ep.md "higgsfield ai":"higgsfield" --write

This is the manual fix-up used after `ep_normalize` flags an unknown duplicate:
collapse the stray surface form onto the canon before the delta is merged.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ep_lib import parse_vector_text


def parse_pair(s: str):
    # accept   "a":"b"   or   a:b
    if ":" not in s:
        raise argparse.ArgumentTypeError(f'expected "from":"to", got {s!r}')
    left, right = s.split(":", 1)
    return left.strip().strip('"'), right.strip().strip('"')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("delta", help="path to the delta .Ep.md buffer file")
    ap.add_argument("pairs", nargs="+", type=parse_pair, metavar='"from":"to"')
    ap.add_argument("--write", action="store_true", help="apply changes in place")
    args = ap.parse_args(argv)

    mapping = dict(args.pairs)
    v = parse_vector_text(Path(args.delta).read_text(encoding="utf-8"))

    n = 0
    for ep in v.eps:
        for attr in ("head", "tail"):
            cur = getattr(ep, attr)
            if cur in mapping:
                setattr(ep, attr, mapping[cur])
                n += 1
    for old, new in mapping.items():
        print(f"  replace  {old!r} -> {new!r}")
    print(f"\n{n} occurrence(s) replaced.")

    if args.write:
        v.refresh_entities()
        Path(args.delta).write_text(v.to_text(), encoding="utf-8")
        print(f"written: {args.delta}")
    else:
        print("(dry-run — pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
