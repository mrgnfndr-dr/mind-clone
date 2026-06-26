#!/usr/bin/env python3
"""ep_lib — shared parser/serializer for the .Ep.md vector format (mind-clone v2 EP-store).

The EP-store is an append-only knowledge layer that sits *alongside* evidence.jsonl.
A "vector" is one `.Ep.md` file whose name approximates the cluster of EP points inside.
A "group" is a folder of vectors (groups never hold EP points directly).
An "EP" (extract point) is one N-dimensional relation on a single line.

This module is the single source of truth for the on-disk grammar. Every command
script (normalize/smoke/replace/merge/context) imports it so they can never disagree
about how an EP is parsed or written.

Grammar of one EP line (pipe-delimited, human-readable, machine-parseable):

    [head] -(relation)-> [tail] | dim:val | dim:val | backing:e0007,e0012 | conf:H | as_of:2025 | density:3 | route:group/vector | thesis

  - first field           : the triple  [head] -(relation)-> [tail]
  - dim:val fields        : free semantic dimensions (because, when, because, value, ...)
  - meta fields (reserved): backing, conf, as_of, density, route, new-vector, src
  - flags (reserved)      : thesis   (marks an author opinion, not a bare fact)

Vector-file header lines start with '# key: value':

    # group: worldview
    # vector: distribution-vs-product
    # centroid: how distribution dominates product outcomes
    # entities: distribution, product, go-to-market
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Meta keys are reserved: a `key:value` field whose key is here is metadata, not a
# free semantic dimension. Everything else with a colon is a dimension.
META_KEYS = {"backing", "conf", "as_of", "density", "route", "new-vector", "src"}
FLAGS = {"thesis"}
CONF_LEVELS = {"H", "M", "L"}

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TRIPLE_RE = re.compile(
    r"^\s*\[(?P<head>[^\]]+)\]\s*-\((?P<rel>[^)]+)\)->\s*\[(?P<tail>[^\]]+)\]\s*(?P<rest>.*)$"
)


def is_kebab(name: str) -> bool:
    """A canonical entity / vector / group id must be kebab-case ASCII."""
    return bool(KEBAB_RE.match(name))


@dataclass
class EP:
    head: str
    rel: str
    tail: str
    dims: dict = field(default_factory=dict)       # ordered free dimensions
    backing: list = field(default_factory=list)    # evidence ids, e.g. ["e0007"]
    conf: str | None = None                        # H | M | L
    as_of: str | None = None                       # year, e.g. "2025"
    density: int | None = None                     # # of independent signals
    route: str | None = None                       # "group/vector" target for merge
    new_vector: str | None = None                  # "group/vector" to create on merge
    src: str | None = None                         # originating source id of the delta
    thesis: bool = False

    def key(self) -> tuple:
        """Identity used for conflict detection: same head+rel => same claim slot."""
        return (self.head, self.rel)

    def target(self) -> str | None:
        """Where merge should place this EP (route into existing, or new-vector)."""
        return self.route or self.new_vector

    def to_line(self) -> str:
        parts = [f"[{self.head}] -({self.rel})-> [{self.tail}]"]
        for k, v in self.dims.items():
            parts.append(f"{k}:{v}")
        if self.backing:
            parts.append("backing:" + ",".join(self.backing))
        if self.conf:
            parts.append(f"conf:{self.conf}")
        if self.as_of:
            parts.append(f"as_of:{self.as_of}")
        if self.density is not None:
            parts.append(f"density:{self.density}")
        if self.route:
            parts.append(f"route:{self.route}")
        if self.new_vector:
            parts.append(f"new-vector:{self.new_vector}")
        if self.src:
            parts.append(f"src:{self.src}")
        if self.thesis:
            parts.append("thesis")
        return " | ".join(parts)


def parse_ep_line(line: str) -> EP | None:
    """Parse one EP line. Returns None for blank/comment lines."""
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    m = _TRIPLE_RE.match(s)
    if not m:
        raise ValueError(f"not a valid EP line (bad triple): {line!r}")
    ep = EP(head=m["head"].strip(), rel=m["rel"].strip(), tail=m["tail"].strip())
    rest = m["rest"].strip()
    if rest.startswith("|"):
        rest = rest[1:]
    for raw in rest.split("|"):
        f = raw.strip()
        if not f:
            continue
        if f in FLAGS:
            if f == "thesis":
                ep.thesis = True
            continue
        if ":" not in f:
            # bare token that isn't a known flag -> treat as a value-less dim flag
            ep.dims[f] = ""
            continue
        key, val = f.split(":", 1)
        key, val = key.strip(), val.strip()
        if key == "backing":
            ep.backing = [x.strip() for x in val.split(",") if x.strip()]
        elif key == "conf":
            ep.conf = val
        elif key == "as_of":
            ep.as_of = val
        elif key == "density":
            ep.density = int(val) if val.isdigit() else None
        elif key == "route":
            ep.route = val
        elif key == "new-vector":
            ep.new_vector = val
        elif key == "src":
            ep.src = val
        else:
            ep.dims[key] = val
    return ep


@dataclass
class Vector:
    group: str = ""
    vector: str = ""
    centroid: str = ""
    entities: list = field(default_factory=list)
    eps: list = field(default_factory=list)  # list[EP]

    def header_lines(self) -> list:
        ents = ", ".join(self.entities) if self.entities else ""
        return [
            f"# group: {self.group}",
            f"# vector: {self.vector}",
            f"# centroid: {self.centroid}",
            f"# entities: {ents}",
            "",
        ]

    def to_text(self) -> str:
        out = self.header_lines()
        out += [ep.to_line() for ep in self.eps]
        return "\n".join(out) + "\n"

    def refresh_entities(self) -> None:
        """Recompute the entity index from the EP points (head + tail)."""
        seen = []
        for ep in self.eps:
            for e in (ep.head, ep.tail):
                if e not in seen:
                    seen.append(e)
        self.entities = seen


def parse_vector_text(text: str) -> Vector:
    v = Vector()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            body = s[1:].strip()
            if ":" in body:
                k, val = body.split(":", 1)
                k, val = k.strip().lower(), val.strip()
                if k == "group":
                    v.group = val
                elif k == "vector":
                    v.vector = val
                elif k == "centroid":
                    v.centroid = val
                elif k == "entities":
                    v.entities = [x.strip() for x in val.split(",") if x.strip()]
            continue
        ep = parse_ep_line(line)
        if ep is not None:
            v.eps.append(ep)
    return v


def load_vector(path) -> Vector:
    from pathlib import Path

    p = Path(path)
    v = parse_vector_text(p.read_text(encoding="utf-8"))
    if not v.vector:
        v.vector = p.stem.replace(".Ep", "")
    if not v.group:
        v.group = p.parent.name
    return v


def save_vector(path, v: Vector) -> None:
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(v.to_text(), encoding="utf-8")


def iter_vector_files(ep_dir):
    """Yield every real vector file under ep/, skipping the _delta buffer and
    any folder/file whose name starts with '_' (reserved, not a group)."""
    from pathlib import Path

    root = Path(ep_dir)
    if not root.exists():
        return
    for p in sorted(root.rglob("*.Ep.md")):
        if any(part.startswith("_") for part in p.relative_to(root).parts):
            continue
        yield p
