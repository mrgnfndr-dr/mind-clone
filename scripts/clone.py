#!/usr/bin/env python3
"""clone.py — access + write layer over the SQLite table store (the canonical truth).
stdlib only. The LLM NEVER reads clone.db directly; it goes through these commands
(described in MANIFEST.md). Subcommands:
  import   rebuild clone.db from sources.jsonl + evidence.jsonl (validate-on-write) + regen manifest
  query    filtered slice (--kind --topic --since --limit [--headers])
  get      full bodies for explicit --ids
  search   regex over quote+note
  fts      SQLite FTS5 token search
  stats    distribution --by <field>
  validate integrity report (enum / FK / required)
Run from inside a clone dir, e.g.:  python <skill>/scripts/clone.py query . --kind heuristic
"""
import sqlite3, json, re, sys, os, argparse, collections

KINDS = ("belief","argument","prediction","heuristic","anecdote","reasoning",
         "framework","antipattern","mental-model","stance","axiom","causal",
         "analogy","observation")
# legacy/dirty kind values seen in older harvests -> canonical (so migration loses nothing)
NORMALIZE = {"causal-belief": "causal"}
REQUIRED = ("id","source","date","kind","quote")

SCHEMA = f"""
DROP TABLE IF EXISTS evidence; DROP TABLE IF EXISTS sources; DROP TABLE IF EXISTS evidence_fts;
CREATE TABLE sources (
  id TEXT PRIMARY KEY, date TEXT NOT NULL, type TEXT NOT NULL,
  voice TEXT CHECK (voice IN ('primary','secondary')),
  title TEXT, url TEXT NOT NULL, video_id TEXT, outlet TEXT,
  views INTEGER, duration_min REAL, lang TEXT, status TEXT, summary TEXT
);
CREATE TABLE evidence (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL REFERENCES sources(id),
  date TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ({",".join(repr(k) for k in KINDS)})),
  topic TEXT, context TEXT, quote TEXT NOT NULL, note TEXT,
  t_start REAL, deeplink TEXT, locator TEXT
);
CREATE VIRTUAL TABLE evidence_fts USING fts5(id UNINDEXED, quote, note);
"""

def jsonl(path):
    if not os.path.exists(path): return
    for l in open(path, encoding="utf-8"):
        if l.strip(): yield json.loads(l)

def connect(slug):
    db = sqlite3.connect(os.path.join(slug, "clone.db"))
    db.execute("PRAGMA foreign_keys=ON")
    return db

# ---- write ----
def cmd_import(a):
    db = connect(a.slug); db.executescript(SCHEMA)
    with db:
        for r in jsonl(os.path.join(a.slug, "sources.jsonl")):
            db.execute("INSERT INTO sources(id,date,type,voice,title,url,video_id,outlet,views,duration_min,lang,status,summary)"
                       " VALUES(:id,:date,:type,:voice,:title,:url,:video_id,:outlet,:views,:duration_min,:lang,:status,:summary)",
                       {k: r.get(k) for k in
                        ("id","date","type","voice","title","url","video_id","outlet","views","duration_min","lang","status","summary")})
    loaded = rejected = normalized = 0
    for r in jsonl(os.path.join(a.slug, "evidence.jsonl")):
        if r.get("kind") in NORMALIZE:
            r["kind"] = NORMALIZE[r["kind"]]; normalized += 1
        try:
            with db:
                db.execute("INSERT INTO evidence(id,source,date,kind,topic,context,quote,note,t_start,deeplink,locator)"
                           " VALUES(:id,:source,:date,:kind,:topic,:context,:quote,:note,:t_start,:deeplink,:locator)",
                           {k: r.get(k) for k in
                            ("id","source","date","kind","topic","context","quote","note","t_start","deeplink","locator")})
                db.execute("INSERT INTO evidence_fts(id,quote,note) VALUES(?,?,?)",
                           (r["id"], r.get("quote",""), r.get("note","")))
            loaded += 1
        except sqlite3.IntegrityError as e:
            rejected += 1; print(f"  REJECTED {r.get('id')}: {e}", file=sys.stderr)
    db.close()
    print(f"imported {loaded} evidence rows (normalized={normalized}, rejected={rejected})")
    print("Now regenerate the contract:  python <skill>/scripts/manifest.py", a.slug)

# ---- read ----
def _body(r): return (f"[{r['id']}] {r['date']} {r['kind']} | {r['topic'] or ''}\n"
                      f"  QUOTE: {r['quote']}\n  NOTE: {r['note'] or ''}"
                      + (f"\n  LINK: {r['deeplink']}" if r['deeplink'] else "") + "\n")

def cmd_query(a):
    db = connect(a.slug); q = "SELECT id,date,kind,topic,quote,note,deeplink FROM evidence WHERE 1=1"; p=[]
    if a.kind:  q += " AND kind IN (%s)" % ",".join("?"*len(a.kind.split(","))); p += a.kind.split(",")
    if a.topic: q += " AND lower(topic) LIKE ?"; p.append(f"%{a.topic.lower()}%")
    if a.since: q += " AND date >= ?"; p.append(a.since)
    q += " ORDER BY date DESC LIMIT ?"; p.append(a.limit)
    rows = [dict(zip(("id","date","kind","topic","quote","note","deeplink"), r)) for r in db.execute(q,p)]
    for r in rows:
        print(f"[{r['id']}] {r['date']} {r['kind']:11} | {r['topic'] or ''}" if a.headers else _body(r))
    print(f"-- {len(rows)} rows", file=sys.stderr)

def cmd_get(a):
    db = connect(a.slug); ids = a.ids.split(",")
    for r in db.execute("SELECT id,date,kind,topic,quote,note,deeplink FROM evidence WHERE id IN (%s)"
                        % ",".join("?"*len(ids)), ids):
        print(_body(dict(zip(("id","date","kind","topic","quote","note","deeplink"), r))))

def cmd_search(a):
    db = connect(a.slug); rx = re.compile(a.term, re.I); n=0
    for r in db.execute("SELECT id,date,kind,topic,quote,note,deeplink FROM evidence"):
        d = dict(zip(("id","date","kind","topic","quote","note","deeplink"), r))
        if rx.search((d['quote'] or '')+(d['note'] or '')):
            print(_body(d)); n+=1
            if n>=a.limit: break

def cmd_fts(a):
    db = connect(a.slug)
    ids = [r[0] for r in db.execute("SELECT id FROM evidence_fts WHERE evidence_fts MATCH ? LIMIT ?",
                                     (a.term, a.limit))]
    if ids: a.ids = ",".join(ids); cmd_get(a)
    print(f"-- {len(ids)} fts hits", file=sys.stderr)

def cmd_stats(a):
    db = connect(a.slug)
    c = collections.Counter(dict(db.execute(f"SELECT {a.by},count(*) FROM evidence GROUP BY {a.by}")))
    for k,n in c.most_common(): print(f"{n:5}  {k}")

def cmd_validate(a):
    db = connect(a.slug); errs=0
    for kind, in db.execute("SELECT DISTINCT kind FROM evidence"):
        if kind not in KINDS: print(f"bad kind: {kind}"); errs+=1
    orph = db.execute("SELECT count(*) FROM evidence e LEFT JOIN sources s ON e.source=s.id WHERE s.id IS NULL").fetchone()[0]
    if orph: print(f"FK orphans: {orph}"); errs+=1
    print(f"-- {errs} violations", file=sys.stderr); sys.exit(1 if errs else 0)

p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
def add(name, fn, *args):
    s = sub.add_parser(name); s.add_argument("slug")
    for a_,kw in args: s.add_argument(a_, **kw)
    s.set_defaults(fn=fn); return s
add("import", cmd_import)
add("query", cmd_query, ("--kind",{}),("--topic",{}),("--since",{}),
    ("--limit",{"type":int,"default":20}),("--headers",{"action":"store_true"}))
add("get", cmd_get, ("--ids",{"required":True}))
add("search", cmd_search, ("term",{}),("--limit",{"type":int,"default":10}))
add("fts", cmd_fts, ("term",{}),("--limit",{"type":int,"default":10}))
add("stats", cmd_stats, ("--by",{"default":"kind"}))
add("validate", cmd_validate)
a = p.parse_args(); a.fn(a)
