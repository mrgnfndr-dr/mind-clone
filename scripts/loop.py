#!/usr/bin/env python3
"""loop.py <slug> <command> [args] — THE CONTOUR: the only interface to a clone.

Drill-down retrieval over the two-table store (meta + ep). The LLM advances ONLY
through these commands; every command prints its result + the NEXT legal command(s);
an unknown command returns a loud error (never a silent no-op). Each run records a
machine log under runs/<id>/. Hermetic: stdlib only — invoke with `python -s`.

Cycle:  intent "<q>"  ->  sources  ->  map <src>  ->  select <src> <vecs>  ->  compile
        (repeat map/select across sources)            delivery.md assembled from EPs
The interpretation step reads runs/<id>/delivery.md and writes the answer; it may
cite ONLY ep ids physically present in delivery.md (A4 — enforced in Phase 3).
"""
import sqlite3, sys, os, json

# the contour speaks UTF-8 regardless of console codepage (Cyrillic/any-language EPs)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SLUG = sys.argv[1] if len(sys.argv) > 1 else None
CMD  = sys.argv[2] if len(sys.argv) > 2 else None
ARGS = sys.argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__))

def die(msg, *avail):
    print("ERROR:", msg)
    if avail: print("available:", " | ".join(avail))
    sys.exit(2)

if not SLUG:
    die("usage: loop.py <slug> <command> [args]")
DB   = os.path.join(SLUG, "clone.db")
RUNS = os.path.join(SLUG, "runs")

def db():
    if not os.path.exists(DB):
        die(f"no clone.db at {DB} — run: python -s loop.py {SLUG} init")
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

def cur_run():
    p = os.path.join(RUNS, "CURRENT")
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else None

def run_dir(rid):
    d = os.path.join(RUNS, rid); os.makedirs(d, exist_ok=True); return d

def log(rid, entry):
    with open(os.path.join(run_dir(rid), "log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def hint(*cmds):
    print("\nNEXT →", "  |  ".join(cmds))

# ---------------------------------------------------------------- commands
def cmd_init():
    os.makedirs(SLUG, exist_ok=True)
    sql = open(os.path.join(HERE, "schema.sql"), encoding="utf-8").read()
    c = sqlite3.connect(DB); c.executescript(sql); c.close()
    print(f"initialized {DB} (tables: meta, ep, ep_fts)")
    hint('intent "<your question>"')

def cmd_intent():
    if not ARGS: die('intent needs text:  intent "what would X think about Y"')
    text = " ".join(ARGS)
    os.makedirs(RUNS, exist_ok=True)
    existing = [int(d) for d in os.listdir(RUNS) if d.isdigit()]
    rid = f"{(max(existing)+1) if existing else 1:04d}"
    open(os.path.join(run_dir(rid), "intent.md"), "w", encoding="utf-8").write(text + "\n")
    open(os.path.join(RUNS, "CURRENT"), "w", encoding="utf-8").write(rid)
    log(rid, {"cmd": "intent", "text": text})
    print(f"run {rid} opened.  intent: {text}")
    hint("sources")

def cmd_sources():
    rid = cur_run() or die("no open run — start with:  intent \"...\"")
    rows = db().execute("SELECT id,date,type,title FROM meta ORDER BY date").fetchall()
    for r in rows:
        print(f"  {r['id']}  {(r['date'] or '—'):10}  {r['type']:9}  {r['title'] or ''}")
    print(f"-- {len(rows)} sources")
    log(rid, {"cmd": "sources", "n": len(rows)})
    hint("map <source_id>")

def cmd_map():
    rid = cur_run() or die("no open run")
    if not ARGS: die("map needs a source id:  map s001")
    sid = ARGS[0]
    rows = db().execute(
        "SELECT grp,vector,COUNT(*) n FROM ep WHERE meta_id=? GROUP BY grp,vector ORDER BY grp,vector",
        (sid,)).fetchall()
    if not rows: die(f"no EPs for source '{sid}' (unknown source or empty)")
    cur = None
    for r in rows:
        if r["grp"] != cur:
            print(f"  [{r['grp']}]"); cur = r["grp"]
        print(f"      {r['vector']}  ({r['n']} ep)")
    log(rid, {"cmd": "map", "source": sid, "vectors": len(rows)})
    hint(f"select {sid} <vector,vector,...>", "map <other_source>")

def cmd_select():
    rid = cur_run() or die("no open run")
    if len(ARGS) < 2: die("select needs source + vectors:  select s001 vecA,vecB")
    sid = ARGS[0]
    vecs = [v.strip() for v in " ".join(ARGS[1:]).split(",") if v.strip()]
    known = {r["vector"] for r in db().execute(
        "SELECT DISTINCT vector FROM ep WHERE meta_id=?", (sid,)).fetchall()}
    bad = [v for v in vecs if v not in known]
    if bad: die(f"unknown vector(s) for {sid}: {', '.join(bad)} — run: map {sid}")
    with open(os.path.join(run_dir(rid), "selection.tsv"), "a", encoding="utf-8") as f:
        for v in vecs: f.write(f"{sid}\t{v}\n")
    log(rid, {"cmd": "select", "source": sid, "vectors": vecs})
    print(f"selected from {sid}: {', '.join(vecs)}")
    hint("select <more>", "compile")

def cmd_compile():
    rid = cur_run() or die("no open run")
    sel = os.path.join(run_dir(rid), "selection.tsv")
    if not os.path.exists(sel): die("nothing selected — use:  select <source> <vectors>")
    pairs = [l.split("\t") for l in open(sel, encoding="utf-8").read().splitlines() if l.strip()]
    con = db(); out = []
    for sid, vec in pairs:
        for r in con.execute(
            "SELECT id,kind,text,deeplink,confidence,backing FROM ep "
            "WHERE meta_id=? AND vector=? ORDER BY id", (sid, vec)).fetchall():
            out.append((sid, vec, r))
    deliv = os.path.join(run_dir(rid), "delivery.md")
    with open(deliv, "w", encoding="utf-8") as f:
        f.write(f"# Delivery — run {rid}\n> Interpret using ONLY these rows. Cite [id]; an id not here = no claim.\n\n")
        for sid, vec, r in out:
            line = f"- [{r['id']}] ({sid}/{vec} · {r['kind']} · conf {r['confidence'] or '—'}) {r['text']}"
            if r["deeplink"]: line += f"  → {r['deeplink']}"
            f.write(line + "\n")
    log(rid, {"cmd": "compile", "eps": len(out)})
    print(f"compiled {len(out)} EP → {deliv}")
    hint("read delivery.md, then interpret (mode a) or pick rows (mode b)")

def cmd_fts():
    if not ARGS: die('fts needs a query:  fts "pricing value"')
    q = " ".join(ARGS)
    rows = db().execute(
        "SELECT e.id,e.meta_id,e.vector,e.text FROM ep_fts f JOIN ep e ON e.id=f.id "
        "WHERE ep_fts MATCH ? LIMIT 20", (q,)).fetchall()
    for r in rows:
        print(f"  [{r['id']}] {r['meta_id']}/{r['vector']}: {r['text'][:90]}")
    print(f"-- {len(rows)} hits (recall only — read before selecting; A9)")
    hint("map <source>", "get <id,...>")

def cmd_get():
    if not ARGS: die("get needs ids:  get e_s001_01,e_s001_02")
    ids = [i.strip() for i in " ".join(ARGS).split(",") if i.strip()]
    qs = ",".join("?" * len(ids))
    rows = db().execute(
        f"SELECT id,meta_id,vector,kind,text,deeplink FROM ep WHERE id IN ({qs})", ids).fetchall()
    for r in rows:
        print(f"[{r['id']}] {r['meta_id']}/{r['vector']} ({r['kind']}): {r['text']}\n  → {r['deeplink'] or ''}")

CMDS = {"init": cmd_init, "intent": cmd_intent, "sources": cmd_sources, "map": cmd_map,
        "select": cmd_select, "compile": cmd_compile, "fts": cmd_fts, "get": cmd_get}

if CMD not in CMDS:
    die(f"unknown command '{CMD}'.", *CMDS)
CMDS[CMD]()
