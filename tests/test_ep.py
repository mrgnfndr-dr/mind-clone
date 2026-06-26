#!/usr/bin/env python3
"""Deterministic tests for the EP-store pipeline (no LLM involved).

Run:  python tests/test_ep.py
Covers: format round-trip, normalization, replacement, smoke checks, append-only merge
(incl. signal accumulation / density). Exits non-zero on any failure.
"""

from __future__ import annotations

import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import ep_normalize  # noqa: E402
import ep_replace  # noqa: E402
import ep_smoke  # noqa: E402
import ep_merge  # noqa: E402
from ep_lib import parse_ep_line, load_vector  # noqa: E402
from ep_entities import load_registry  # noqa: E402

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  ok   {name}")
    else:
        _failed += 1
        print(f"  FAIL {name}")


def quiet(fn, *a, **k):
    """Run a script main() swallowing its stdout, return its exit code."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


def test_roundtrip():
    print("[format round-trip]")
    line = ("[distribution] -(beats)-> [product] | because:products die unshipped "
            "| backing:e0007,e0012 | conf:H | as_of:2025 | thesis")
    ep = parse_ep_line(line)
    check("triple parsed", (ep.head, ep.rel, ep.tail) == ("distribution", "beats", "product"))
    check("dim parsed", ep.dims.get("because") == "products die unshipped")
    check("backing parsed", ep.backing == ["e0007", "e0012"])
    check("conf parsed", ep.conf == "H")
    check("thesis flag", ep.thesis is True)
    again = parse_ep_line(ep.to_line())
    check("serialize->parse stable", ep.to_line() == again.to_line())
    check("blank line -> None", parse_ep_line("   ") is None)
    bad = False
    try:
        parse_ep_line("not an ep at all")
    except ValueError:
        bad = True
    check("malformed raises", bad)


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_normalize():
    print("[normalize]")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        reg = d / "ep" / "entities.jsonl"
        write(reg, '{"canon":"viktor-savin","aliases":["savin viktor","в. савин"],"vectors":[]}\n')
        delta = d / "ep" / "_delta" / "s1.Ep.md"
        write(delta, "[savin viktor] -(founded)-> [carpinteria-estilo-ruso] | backing:e1 | conf:M | route:biz/workshop\n")
        rc, _ = quiet(ep_normalize.main, [str(delta), "--registry", str(reg), "--write"])
        v = load_vector(delta)
        check("alias folded to canon", v.eps[0].head == "viktor-savin")
        check("exit 0", rc == 0)


def test_replace():
    print("[replace]")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        delta = d / "ep" / "_delta" / "s2.Ep.md"
        write(delta, "[higgsfield ai] -(builds)-> [video-models] | backing:e2 | route:biz/product\n")
        rc, _ = quiet(ep_replace.main, [str(delta), 'higgsfield ai:higgsfield', "--write"])
        v = load_vector(delta)
        check("entity renamed", v.eps[0].head == "higgsfield")
        check("exit 0", rc == 0)


def base_db(d: Path):
    """A tiny main_db with one existing vector + registry."""
    write(d / "ep" / "worldview" / "distribution-vs-product.Ep.md",
          "# group: worldview\n# vector: distribution-vs-product\n# centroid: distribution dominates product\n# entities: distribution, product\n\n"
          "[distribution] -(beats)-> [product] | backing:e0001 | conf:H\n")
    write(d / "ep" / "entities.jsonl",
          '{"canon":"distribution","aliases":[],"vectors":["worldview/distribution-vs-product"]}\n'
          '{"canon":"product","aliases":[],"vectors":["worldview/distribution-vs-product"]}\n')


def test_smoke():
    print("[smoke]")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        base_db(d)
        ep_dir, reg = str(d / "ep"), str(d / "ep" / "entities.jsonl")

        ungrounded = d / "ep" / "_delta" / "bad.Ep.md"
        write(ungrounded, "[focus] -(beats)-> [optionality] | route:worldview/distribution-vs-product\n")
        rc, out = quiet(ep_smoke.main, [str(ungrounded), "--ep-dir", ep_dir, "--registry", reg])
        check("ungrounded EP -> error exit 1", rc == 1 and "ungrounded" in out)

        badroute = d / "ep" / "_delta" / "badroute.Ep.md"
        write(badroute, "[focus] -(beats)-> [optionality] | backing:e9 | route:worldview/does-not-exist\n")
        rc, out = quiet(ep_smoke.main, [str(badroute), "--ep-dir", ep_dir, "--registry", reg])
        check("route to missing vector -> error", rc == 1 and "does not exist" in out)

        clean = d / "ep" / "_delta" / "ok.Ep.md"
        write(clean, "[go-to-market] -(hire-early)-> [startup] | backing:e9 | conf:M | new-vector:biz/hiring\n")
        rc, out = quiet(ep_smoke.main, [str(clean), "--ep-dir", ep_dir, "--registry", reg])
        check("clean delta -> exit 0", rc == 0)
        check("preview counts new-vector", "1 new-vector" in out)


def test_merge_append_only():
    print("[merge / append-only / density]")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        base_db(d)
        ep_dir, reg = str(d / "ep"), str(d / "ep" / "entities.jsonl")

        d1 = d / "ep" / "_delta" / "d1.Ep.md"
        write(d1, "[generalists] -(hire-before)-> [specialists] | because:uncertainty | backing:e0012 | conf:M | new-vector:biz/hiring\n")
        quiet(ep_merge.main, [str(d1), "--ep-dir", ep_dir, "--registry", reg])
        vpath = d / "ep" / "biz" / "hiring.Ep.md"
        check("new vector created", vpath.exists())
        v = load_vector(vpath)
        check("1 EP after first merge", len(v.eps) == 1)
        check("density=1", v.eps[0].density == 1)
        check("route annotation stripped", v.eps[0].route is None and v.eps[0].new_vector is None)
        r = load_registry(reg)
        check("entity registered", r.canon_for("generalists") == "generalists")

        # second, SIMILAR signal -> must accumulate, NOT collapse; density bumps to 2
        d2 = d / "ep" / "_delta" / "d2.Ep.md"
        write(d2, "[generalists] -(hire-before)-> [specialists] | backing:e0044 | conf:M | route:biz/hiring\n")
        quiet(ep_merge.main, [str(d2), "--ep-dir", ep_dir, "--registry", reg])
        v = load_vector(vpath)
        check("similar signal accumulated (2 EP)", len(v.eps) == 2)
        check("density recomputed to 2", all(ep.density == 2 for ep in v.eps))

        # original main_db vector untouched (append-only)
        wv = load_vector(d / "ep" / "worldview" / "distribution-vs-product.Ep.md")
        check("pre-existing vector untouched", len(wv.eps) == 1)


def main():
    test_roundtrip()
    test_normalize()
    test_replace()
    test_smoke()
    test_merge_append_only()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
