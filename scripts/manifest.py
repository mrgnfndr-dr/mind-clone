#!/usr/bin/env python3
"""manifest.py <slug> [--verify] — generate MANIFEST.md FROM the live clone.db.
The manifest is a DERIVATIVE of the schema, so it always reflects current state.
The LLM reads MANIFEST.md (the contract), never the raw tables.
--verify: exit 1 if MANIFEST.md's stored schema_hash != live DB hash (drift guard)."""
import sqlite3, sys, os, re, hashlib

slug = sys.argv[1]; verify = "--verify" in sys.argv
dbp = os.path.join(slug, "clone.db"); mfp = os.path.join(slug, "MANIFEST.md")
db = sqlite3.connect(dbp)
ddl = [r[0] for r in db.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY name")]
schema_hash = hashlib.sha256("\n".join(ddl).encode()).hexdigest()[:12]
uv = db.execute("PRAGMA user_version").fetchone()[0]

if verify:
    stored = None
    if os.path.exists(mfp):
        m = re.search(r"schema_hash:\s*([0-9a-f]+)", open(mfp, encoding="utf-8").read())
        stored = m.group(1) if m else None
    if stored != schema_hash:
        print(f"DRIFT: manifest={stored} live={schema_hash} — regenerate", file=sys.stderr); sys.exit(1)
    print("manifest in sync"); sys.exit(0)

def tables():
    return [r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%'")]
def enum_of(t, c):
    sql = db.execute("SELECT sql FROM sqlite_master WHERE name=?", (t,)).fetchone()[0]
    m = re.search(rf"{c}[^,]*?CHECK\s*\(\s*{c}\s+IN\s*\(([^)]+)\)", sql, re.I|re.S)
    return [v.strip().strip("'\"") for v in m.group(1).split(",")] if m else None

L=[]; w=L.append
w(f"# CLONE TABLE MANIFEST — {slug}\n")
w("> Generated FROM the live clone.db. Do NOT edit by hand. Do NOT read the raw tables —")
w("> interact ONLY through the commands below. Regenerated on every schema change.\n")
w("```")
w(f"schema_hash: {schema_hash}\nuser_version: {uv}\ndb: {slug}/clone.db")
w("```\n")
w("## Tables & fields")
for t in tables():
    fks = {f[3]: f"{f[2]}.{f[4]}" for f in db.execute(f"PRAGMA foreign_key_list({t})")}
    n = db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    w(f"\n### `{t}` — {n} rows")
    for _,name,typ,notnull,_,pk in db.execute(f"PRAGMA table_info({t})"):
        fl=[]; pk and fl.append("PK"); notnull and fl.append("NOT NULL")
        name in fks and fl.append(f"FK→{fks[name]}"); enum_of(t,name) and fl.append(f"enum[{len(enum_of(t,name))}]")
        w(f"- `{name}` {typ or 'TEXT'} {' '.join(fl)}".rstrip())
w("\n## Enums (allowed + live distribution)")
for t in tables():
    for _,col,*_ in db.execute(f"PRAGMA table_info({t})"):
        en = enum_of(t,col)
        if not en: continue
        live = dict(db.execute(f"SELECT {col},count(*) FROM {t} GROUP BY {col}"))
        w(f"\n`{t}.{col}` allowed: {', '.join(en)}")
        w("present: " + ", ".join(f"{k}={v}" for k,v in sorted(live.items(), key=lambda x:-x[1])))
w("\n## Coverage")
for t in tables():
    mn,mx = db.execute(f"SELECT min(date),max(date) FROM {t}").fetchone()
    w(f"- `{t}`: dates {mn} … {mx}")
if [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE sql LIKE '%fts5%'")]:
    w("- full-text: evidence_fts (over quote+note)")
w("""
## Commands — the ONLY way to touch the data (each returns a small slice, never the table)
| Intent | Command (run from the clone dir) |
|---|---|
| filter | `python <skill>/scripts/clone.py query . --kind A,B --topic T --since YYYY-MM-DD --limit N [--headers]` |
| bodies by id | `python <skill>/scripts/clone.py get . --ids e0_001,e1_004` |
| regex | `python <skill>/scripts/clone.py search . "<regex>" --limit N` |
| full-text | `python <skill>/scripts/clone.py fts . "<query>" --limit N` |
| distribution | `python <skill>/scripts/clone.py stats . --by kind` |
| integrity | `python <skill>/scripts/clone.py validate .` |

## Intent → recipe
- "what does X think about <topic>" → `query --topic <t>` then `fts "<kw1> OR <kw2>"`
- "strongest convictions" → `query --kind axiom,stance,belief`
- "decision rules / method" → `query --kind heuristic,framework`
- "what they reject" → `query --kind antipattern`
- "corpus shape" → `stats --by kind` / `stats --by source`
- "recent shift" → `query --topic <t> --since <date>` (recency wins)

## Two-role protocol (retrieve → analyze; isolation by responsibility)
- RETRIEVER: read this manifest, choose commands, deliver a slice to `runs/<id>/retrieval.md`. Does NOT judge.
- ANALYST: sees ONLY the delivered slice (not the table, not memory) → writes `runs/<id>/choice.md`
  citing row ids. No id → no claim. If short, emit `INSUFFICIENT: need X` → new retrieval round.
- Re-deciding rewrites only choice.md; the (expensive) retrieval is reused.

## Guardrails
- NEVER read clone.db / *.jsonl directly. Go through commands.
- NEVER fabricate quotes — only surface rows the commands return.
- If `manifest.py <slug> --verify` fails, the manifest is stale: regenerate before trusting it.
""")
open(mfp,"w",encoding="utf-8").write("\n".join(L))
print(f"wrote {mfp} (schema_hash={schema_hash})")
