#!/usr/bin/env python3
"""migrate_jsonl.py <slug> — one-time bridge: legacy sources.jsonl + evidence.jsonl
-> contour-v3 two-table store (meta + ep) in clone.db. Rebuilds clone.db fresh.
group = kind, vector = slug(topic) (deterministic; refine later via EP pipeline).
Hermetic: stdlib only, run with `python -s`."""
import sqlite3, sys, os, json, re, hashlib

slug = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(slug, "clone.db")
KIND_OK = {'belief','heuristic','framework','stance','antipattern','procedure',
           'reasoning','anecdote','prediction','axiom','relation','observation'}

def slug_topic(t):
    s = re.sub(r"[^a-z0-9]+", "-", (t or "misc").lower()).strip("-")
    return s[:40] or "misc"

def file_hash(path):
    if path and os.path.exists(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(8192), b""): h.update(b)
        return h.hexdigest()[:16]
    return "nohash"

if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB)
con.executescript(open(os.path.join(HERE, "schema.sql"), encoding="utf-8").read())

srcs = {}
for l in open(os.path.join(slug, "sources.jsonl"), encoding="utf-8"):
    r = json.loads(l); srcs[r["id"]] = r
    raw = None
    for ext in (".srt", ".md"):
        if os.path.exists(os.path.join(slug, "raw", r["id"] + ext)):
            raw = os.path.join("raw", r["id"] + ext); break
    con.execute(
        "INSERT INTO meta(id,hash,type,title,url,outlet,date,duration_min,lang,raw_path)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)",
        (r["id"], file_hash(os.path.join(slug, raw) if raw else None),
         r.get("type", "article"), r.get("title"), r.get("url", ""), r.get("outlet"),
         r.get("date"), r.get("duration_min"), r.get("lang", "en"), raw))

n = skip = 0
for l in open(os.path.join(slug, "evidence.jsonl"), encoding="utf-8"):
    e = json.loads(l)
    if e["source"] not in srcs: skip += 1; continue
    kind = e.get("kind", "observation")
    if kind not in KIND_OK: kind = "observation"
    con.execute(
        "INSERT INTO ep(id,meta_id,grp,vector,kind,text,t_start,deeplink,as_of,backing)"
        " VALUES(?,?,?,?,?,?,?,?,?,?)",
        (e["id"], e["source"], kind, slug_topic(e.get("topic")), kind, e.get("quote", ""),
         e.get("t_start"), e.get("deeplink"), (e.get("date") or "")[:4] or None, e.get("locator")))
    con.execute("INSERT INTO ep_fts(id,text,subject,object) VALUES(?,?,?,?)",
                (e["id"], e.get("quote", ""), None, None))
    n += 1
con.commit()
print(f"migrated {slug}: {len(srcs)} meta, {n} ep ({skip} skipped)")
con.close()
