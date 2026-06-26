#!/usr/bin/env python3
"""ep_entities — the canonical entity registry for the EP-store.

Entities are the retrieval keys of the graph: the same node must have ONE canonical
id so that "[viktor savin]" and "[savin viktor]" collapse to the same searchable node
and EPs from different sources actually connect.

Registry file: ep/entities.jsonl — one JSON object per line:
    {"canon": "viktor-savin", "aliases": ["savin viktor", "в. савин"], "vectors": ["business-ops/hiring"]}

Canonical ids are kebab-case ASCII (single naming convention for the whole store).
Aliases may be any surface form (including non-Latin); they map onto the canon.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


def slugify(name: str) -> str:
    """Best-effort kebab-case ASCII slug. Used only to *propose* a canon id for a
    brand-new entity; existing canons always win via the alias index."""
    s = name.strip().lower()
    # transliterate accents away where possible; non-Latin scripts will be dropped
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def norm_surface(name: str) -> str:
    """Normalize a surface form for alias matching: lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", name.strip().lower())


class Registry:
    def __init__(self, records: list | None = None):
        self.records = records or []  # list[dict]
        self._alias_index = {}        # norm_surface -> canon
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._alias_index = {}
        for r in self.records:
            canon = r["canon"]
            self._alias_index[norm_surface(canon)] = canon
            for a in r.get("aliases", []):
                self._alias_index[norm_surface(a)] = canon

    def canon_for(self, surface: str) -> str | None:
        """Return the canonical id for a surface form, or None if unknown."""
        return self._alias_index.get(norm_surface(surface))

    def all_canons(self) -> list:
        return [r["canon"] for r in self.records]

    def add(self, canon: str, aliases: list | None = None, vector: str | None = None) -> dict:
        rec = next((r for r in self.records if r["canon"] == canon), None)
        if rec is None:
            rec = {"canon": canon, "aliases": [], "vectors": []}
            self.records.append(rec)
        for a in aliases or []:
            if norm_surface(a) != norm_surface(canon) and a not in rec["aliases"]:
                rec["aliases"].append(a)
        if vector and vector not in rec["vectors"]:
            rec["vectors"].append(vector)
        self._rebuild_index()
        return rec


def load_registry(path) -> Registry:
    p = Path(path)
    records = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return Registry(records)


def save_registry(path, reg: Registry) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in reg.records]
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
