-- mind-clone canonical store (contour v3). Two tables. clone.db is the ONE center.
-- meta  = source provenance + integrity (one row per source).
-- ep    = the source table: semantic compression of each source as EP points,
--         organised group -> vector -> point. One EP = one row. The `text` is the
--         grounded author extract (the core); subject/relation/object is the EP
--         relation overlay (for navigation + extrapolation). Everything else
--         (cognitive-model, playbook, evidence) is a JIT view over this.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  id           TEXT PRIMARY KEY,                 -- source id, e.g. s001
  hash         TEXT NOT NULL,                    -- content hash of raw (integrity)
  type         TEXT NOT NULL CHECK (type IN
                 ('youtube','article','interview','podcast','radio','talk',
                  'thread','paper','profile','book')),
  title        TEXT,
  url          TEXT NOT NULL,
  outlet       TEXT,
  date         TEXT,                             -- ISO yyyy-mm-dd
  duration_min REAL,
  lang         TEXT,
  raw_path     TEXT                              -- path to raw/<id>.srt|.md (file is source material, referenced not duplicated)
);

CREATE TABLE IF NOT EXISTS ep (
  id         TEXT PRIMARY KEY,                   -- ep id, e.g. e_s001_01
  meta_id    TEXT NOT NULL REFERENCES meta(id),
  grp        TEXT NOT NULL,                      -- group  (theme / folder)
  vector     TEXT NOT NULL,                      -- vector (cluster within group)
  kind       TEXT NOT NULL CHECK (kind IN
               ('belief','heuristic','framework','stance','antipattern','procedure',
                'reasoning','anecdote','prediction','axiom','relation','observation')),
  subject    TEXT,                               -- entity A  )
  relation   TEXT,                               -- predicate ) the EP relation (extrapolation overlay)
  object     TEXT,                               -- entity B  )
  text       TEXT NOT NULL,                      -- grounded author extract — THE core
  t_start    INTEGER,                            -- locator into raw (audio/video sec); NULL for text
  deeplink   TEXT,                               -- ready grounded link
  confidence TEXT CHECK (confidence IN ('H','M','L')),
  as_of      TEXT,                               -- time tag (year) for time-bound views
  backing    TEXT                                -- locator/ids backing this EP inside the source
);

CREATE INDEX IF NOT EXISTS ix_ep_source  ON ep(meta_id);
CREATE INDEX IF NOT EXISTS ix_ep_map     ON ep(meta_id, grp, vector);

-- full-text recall over the grounded text + entities (recall mechanism, NOT selection — A9)
CREATE VIRTUAL TABLE IF NOT EXISTS ep_fts USING fts5(id UNINDEXED, text, subject, object);
