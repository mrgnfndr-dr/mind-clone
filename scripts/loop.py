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
import sqlite3, sys, os, json, re, shutil

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
    # OR the terms (recall: any term matches) and rank by bm25 — a multi-word query
    # must not be implicit-AND (that misses paraphrases). Sanitize to plain tokens so
    # FTS5 operators in user text can't break the query.
    terms = [t for t in re.split(r"\W+", " ".join(ARGS).lower()) if t]
    if not terms: die("fts needs at least one word")
    match = " OR ".join(f'"{t}"' for t in terms)
    rows = db().execute(
        "SELECT e.id,e.meta_id,e.vector,e.text FROM ep_fts f JOIN ep e ON e.id=f.id "
        "WHERE ep_fts MATCH ? ORDER BY bm25(ep_fts) LIMIT 20", (match,)).fetchall()
    for r in rows:
        print(f"  [{r['id']}] {r['meta_id']}/{r['vector']}: {r['text'][:90]}")
    print(f"-- {len(rows)} hits, best-ranked first (recall only — read before selecting; A9)")
    hint("map <source>", "get <id,...>")

def cmd_runs():
    """List the runs (read-only). The GC keeps the contour's run dir from growing forever."""
    if not os.path.isdir(RUNS): print("(no runs yet)"); return
    cur = cur_run()
    for d in sorted((x for x in os.listdir(RUNS) if x.isdigit()), key=int):
        intent = ""
        ip = os.path.join(RUNS, d, "intent.md")
        if os.path.exists(ip): intent = open(ip, encoding="utf-8").read().strip().splitlines()[0][:70]
        pin = " 📌" if os.path.exists(os.path.join(RUNS, d, "pin")) else ""
        cur_mark = " (current)" if d == cur else ""
        print(f"  {d}{pin}{cur_mark}  {intent}")

def cmd_pin():
    """pin <id> — mark a run so gc never deletes it (e.g. a reusable retrieval)."""
    if not ARGS: die("pin needs a run id:  pin 0007")
    d = os.path.join(RUNS, ARGS[0])
    if not os.path.isdir(d): die(f"no run {ARGS[0]}")
    open(os.path.join(d, "pin"), "w").close()
    print(f"pinned run {ARGS[0]} (gc will keep it)")

def cmd_gc():
    """gc [N] — keep the N most recent runs (default 20) + any pinned, delete the rest."""
    keep = int(ARGS[0]) if (ARGS and ARGS[0].isdigit()) else 20
    if not os.path.isdir(RUNS): print("(no runs)"); return
    runs = sorted((x for x in os.listdir(RUNS) if x.isdigit()), key=int)
    pinned = {d for d in runs if os.path.exists(os.path.join(RUNS, d, "pin"))}
    unpinned = [d for d in runs if d not in pinned]
    drop = unpinned[:-keep] if len(unpinned) > keep else []
    for d in drop:
        shutil.rmtree(os.path.join(RUNS, d))
    print(f"gc: {len(runs)-len(drop)} kept ({len(pinned)} pinned), {len(drop)} deleted")

def cmd_get():
    if not ARGS: die("get needs ids:  get e_s001_01,e_s001_02")
    ids = [i.strip() for i in " ".join(ARGS).split(",") if i.strip()]
    qs = ",".join("?" * len(ids))
    rows = db().execute(
        f"SELECT id,meta_id,vector,kind,text,deeplink FROM ep WHERE id IN ({qs})", ids).fetchall()
    for r in rows:
        print(f"[{r['id']}] {r['meta_id']}/{r['vector']} ({r['kind']}): {r['text']}\n  → {r['deeplink'] or ''}")

_KINDS = {'belief','heuristic','framework','stance','antipattern','procedure',
          'reasoning','anecdote','prediction','axiom','relation','observation'}

def _entities(con):
    e = set()
    for col in ("subject", "object"):
        for r in con.execute(f"SELECT DISTINCT {col} FROM ep WHERE {col} IS NOT NULL AND {col}<>''"):
            e.add(r[0])
    return e

def cmd_context():
    """PRESSURE for extracting a new source's delta: the entities + vector map that
    already exist, so new EPs reuse canonical entities/vectors instead of inventing
    near-duplicates. (Table-native replacement for the old ep_context.py.)"""
    con = db()
    ents = sorted(_entities(con))
    print("== KNOWN ENTITIES (reuse these canonical ids; don't invent near-duplicates) ==")
    print(", ".join(ents) if ents else "(none yet — first ingest)")
    print("\n== VECTOR MAP (route EPs here when they fit; new vector only if truly new) ==")
    cur = None
    rows = con.execute("SELECT grp,vector,COUNT(*) n FROM ep GROUP BY grp,vector ORDER BY grp,vector").fetchall()
    for r in rows:
        if r["grp"] != cur: print(f"[{r['grp']}]"); cur = r["grp"]
        print(f"  {r['grp']}/{r['vector']}  ({r['n']} ep)")
    if not rows: print("(no vectors yet — first ingest)")
    hint("extract the delta routed to these, then: smoke <delta.jsonl>")

def cmd_smoke():
    """Dry-run a delta against the table. Reports problems, writes NOTHING (read-only).
    Table-native ep_smoke: grounding / kind / conf / id-collision / dangling source /
    route-vs-new-vector + a merge preview. Exit 1 if any ERROR."""
    if not ARGS: die("smoke needs a delta file:  smoke delta.jsonl")
    path = ARGS[0]
    if not os.path.exists(path): die(f"no such file: {path}")
    con = db()
    vectors = {f"{r['grp']}/{r['vector']}" for r in con.execute("SELECT DISTINCT grp,vector FROM ep")}
    groups  = {r[0] for r in con.execute("SELECT DISTINCT grp FROM ep")}
    ids     = {r[0] for r in con.execute("SELECT id FROM ep")}
    metas   = {r[0] for r in con.execute("SELECT id FROM meta")}
    ents    = _entities(con)
    errors, warns = [], []
    add_existing = new_vec = new_grp = 0
    seen_vec = set(); delta_meta = set()
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r.get("_t") == "meta": delta_meta.add(r.get("id")); continue
        eid = r.get("id")
        if not r.get("text"): errors.append(f"L{ln} {eid}: no text — ungrounded EP")
        if not (r.get("backing") or r.get("deeplink") or r.get("t_start") is not None):
            errors.append(f"L{ln} {eid}: no backing/deeplink/t_start — ungrounded")
        if r.get("kind") not in _KINDS: errors.append(f"L{ln} {eid}: bad kind {r.get('kind')!r}")
        if r.get("confidence") and r["confidence"] not in ("H","M","L"):
            errors.append(f"L{ln} {eid}: bad confidence {r.get('confidence')!r} (H|M|L)")
        if eid in ids: errors.append(f"L{ln} {eid}: id already in table (collision)")
        if r.get("meta_id") not in metas and r.get("meta_id") not in delta_meta:
            errors.append(f"L{ln} {eid}: meta_id {r.get('meta_id')!r} not in table — import its source first")
        grp, vec = _canon(r.get("grp")), _canon(r.get("vector"))   # canon as import will
        if not grp or not vec:
            errors.append(f"L{ln} {eid}: no grp/vector — merge can't place it")
        else:
            tag = f"{grp}/{vec}"
            if tag in vectors: add_existing += 1
            elif tag not in seen_vec:
                seen_vec.add(tag); new_vec += 1
                if grp not in groups: new_grp += 1; groups.add(grp)
        for ent in (_canon(r.get("subject")), _canon(r.get("object"))):
            if ent and ent not in ents:
                warns.append(f"L{ln}: entity {ent!r} not seen before — fold to an existing one or keep if truly new")
    for e in errors: print("ERROR ", e)
    for w in warns[:30]: print("WARN  ", w)
    if len(warns) > 30: print(f"WARN   … +{len(warns)-30} more")
    print(f"\nmerge preview: {add_existing} add-to-existing · {new_vec} new-vector · {new_grp} new-group")
    print("CLEAN — safe to import" if not errors else f"{len(errors)} ERROR(S) — fix before import")
    sys.exit(1 if errors else 0)

_META_COLS = ("id","hash","type","title","url","outlet","date","duration_min","lang","raw_path")
_EP_COLS   = ("id","meta_id","grp","vector","kind","subject","relation","object",
              "text","t_start","deeplink","confidence","as_of","backing")

def _canon(s):
    """Canonical kebab id for grp/vector/subject/object: lowercase, ws/underscore -> hyphen,
    collapse, strip. Unicode-safe (keeps Cyrillic etc.) — normalizes form only, so
    'Go To Market' and 'go_to_market' land as the same 'go-to-market' (no casing/spacing dupes)."""
    if not s: return s
    s = re.sub(r"[\s_]+", "-", str(s).strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-") or s

def cmd_import():
    """Write path = a transaction that emits a LOG (not a stored duplicate).
    Reads a delta .jsonl (one row per line; `_t:"meta"` for a source row, else an EP).
    Validation is on write (CHECK kind / FK meta_id / NOT NULL) — bad rows are rejected
    by the engine with a reason, never silently. Prints loaded/rejected + why."""
    if not ARGS: die("import needs a delta file:  import delta.jsonl")
    path = ARGS[0]
    if not os.path.exists(path): die(f"no such file: {path}")
    con = db()
    urls = {u: i for i, u in con.execute("SELECT id,url FROM meta")}   # hygiene: dedup sources by url
    loaded = {"meta": 0, "ep": 0}; rejected = []; hygiene = []
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line: continue
        r = json.loads(line); t = r.get("_t", "ep")
        try:
            if t == "meta":
                u = r.get("url")
                if u in urls and urls[u] != r.get("id"):
                    hygiene.append(f"L{ln} {r.get('id')}: duplicate source url (already {urls[u]}) — skipped")
                    continue
                con.execute(f"INSERT OR REPLACE INTO meta({','.join(_META_COLS)}) "
                            f"VALUES({','.join('?'*len(_META_COLS))})", [r.get(k) for k in _META_COLS])
                if u: urls[u] = r.get("id")
                loaded["meta"] += 1
            else:
                for k in ("grp", "vector", "subject", "object"):   # canonicalize entity/vector ids
                    if r.get(k): r[k] = _canon(r[k])
                con.execute(f"INSERT INTO ep({','.join(_EP_COLS)}) "
                            f"VALUES({','.join('?'*len(_EP_COLS))})", [r.get(k) for k in _EP_COLS])
                con.execute("INSERT INTO ep_fts(id,text,subject,object) VALUES(?,?,?,?)",
                            (r.get("id"), r.get("text"), r.get("subject"), r.get("object")))
                loaded["ep"] += 1
            con.commit()
        except (sqlite3.IntegrityError, sqlite3.Error) as e:
            con.rollback(); rejected.append((ln, r.get("id"), str(e)))
    print(f"import: loaded meta={loaded['meta']} ep={loaded['ep']}, rejected={len(rejected)}, hygiene={len(hygiene)}")
    for ln, rid_, why in rejected:
        print(f"  REJECT L{ln} {rid_}: {why}")
    for h in hygiene:
        print(f"  HYGIENE {h}")
    rid = cur_run()
    if rid: log(rid, {"cmd": "import", "loaded": loaded,
                      "rejected": [list(x) for x in rejected], "hygiene": hygiene})

def cmd_migrate():
    """migrate — apply migrations/NNN_*.sql with seq > the db's PRAGMA user_version, in order,
    each in a transaction, bumping user_version. The schema-versioning framework (V9)."""
    con = db()
    cur = con.execute("PRAGMA user_version").fetchone()[0]
    migdir = os.path.join(HERE, "migrations")
    applied = []
    if os.path.isdir(migdir):
        for fn in sorted(os.listdir(migdir)):
            m = re.match(r"^(\d+)_.*\.sql$", fn)
            if not m: continue
            seq = int(m.group(1))
            if seq > cur:
                con.executescript(open(os.path.join(migdir, fn), encoding="utf-8").read())
                con.execute(f"PRAGMA user_version = {seq}")
                con.commit()
                applied.append(fn)
    new = con.execute("PRAGMA user_version").fetchone()[0]
    print(f"migrate: user_version {cur} → {new}; applied {len(applied)}: {', '.join(applied) or '(none)'}")

def cmd_render():
    """JIT representations — built from the tables on demand, printed to stdout,
    NEVER stored. Replaces the old persisted sources.md / cognitive-model.md /
    playbook.md / MANIFEST.md (all were duplicates of the canon)."""
    what = ARGS[0] if ARGS else None
    con = db()
    if what == "sources":
        for r in con.execute("SELECT id,date,type,outlet,title,url FROM meta ORDER BY date"):
            print(f"- {r['id']}: {r['title'] or ''}\n    {r['type']} · {r['outlet'] or '—'} · {r['date'] or '—'} · {r['url']}")
    elif what == "manifest":
        print(f"# MANIFEST — generated JIT from {DB} (schema + live counts). The LLM reads this, not the table.")
        for t in ("meta", "ep"):
            n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            cols = [c["name"] for c in con.execute(f"PRAGMA table_info({t})")]
            print(f"\n## {t} ({n} rows): {', '.join(cols)}")
        kinds = con.execute("SELECT kind,COUNT(*) n FROM ep GROUP BY kind ORDER BY n DESC").fetchall()
        print("\n## ep.kind:", ", ".join(f"{r['kind']}={r['n']}" for r in kinds))
        print("## commands:", " | ".join(CMDS))
    elif what == "brain":
        sid = ARGS[1] if len(ARGS) > 1 else None
        q = ("SELECT grp,vector,subject,relation,object,text FROM ep"
             + (" WHERE meta_id=?" if sid else "") + " ORDER BY grp,vector")
        rows = con.execute(q, (sid,) if sid else ()).fetchall()
        cur = None
        for r in rows:
            if r["grp"] != cur: print(f"\n[{r['grp']}]"); cur = r["grp"]
            rel = f"{r['subject']} —{r['relation']}→ {r['object']}" if r["relation"] else (r["text"][:80] + "…")
            print(f"  {r['vector']}: {rel}")
    elif what == "playbook":
        rows = con.execute("SELECT meta_id,vector,text,deeplink FROM ep WHERE kind='procedure' ORDER BY meta_id").fetchall()
        if not rows: print("(no procedure EPs — this author teaches no extractable methodology, or none harvested)")
        for r in rows: print(f"- {r['text']}  → {r['deeplink'] or ''}  [{r['meta_id']}/{r['vector']}]")
    else:
        die("render needs a view: render sources | manifest | brain [source] | playbook")

_CITE = re.compile(r"\[(e_[a-z0-9_]+)\]")

def cmd_verify():
    """A4 gate: the answer (runs/<id>/answer.md) may cite ONLY ep ids physically
    present in delivery.md. Anything else -> loud REJECT. Catches off-rail grounding."""
    rid = cur_run() or die("no open run")
    d = run_dir(rid)
    ans, deliv = os.path.join(d, "answer.md"), os.path.join(d, "delivery.md")
    if not os.path.exists(deliv): die("no delivery.md — compile first")
    if not os.path.exists(ans): die("no answer.md — write the interpreted answer first, then verify")
    delivered = set(_CITE.findall(open(deliv, encoding="utf-8").read()))
    cited = _CITE.findall(open(ans, encoding="utf-8").read())
    bad = sorted({c for c in cited if c not in delivered})
    log(rid, {"cmd": "verify", "cited": len(cited), "bad": bad, "accepted": not bad and bool(cited)})
    if not cited:
        die("answer cites no ids — A4: no id, no claim. Ground every claim in a delivered [id].")
    if bad:
        die(f"REJECTED — cited ids not in delivery: {', '.join(bad)}. "
            "You may cite ONLY EPs physically delivered this run (see delivery.md).")
    print(f"ACCEPTED — {len(cited)} citation(s), all resolve to delivered EPs.")
    hint("done — deliver answer.md to the user")

CMDS = {"init": cmd_init, "intent": cmd_intent, "sources": cmd_sources, "map": cmd_map,
        "select": cmd_select, "compile": cmd_compile, "fts": cmd_fts, "get": cmd_get,
        "verify": cmd_verify, "render": cmd_render, "import": cmd_import,
        "context": cmd_context, "smoke": cmd_smoke,
        "runs": cmd_runs, "pin": cmd_pin, "gc": cmd_gc, "migrate": cmd_migrate}

if CMD not in CMDS:
    die(f"unknown command '{CMD}'.", *CMDS)
CMDS[CMD]()
