# Source table template (Phase 2 review gate)

Present this table **in chat** for the user to approve/prune, and mirror it to `clones/<slug>/sources.md`.

## Chat format

```
Found N sources for <Author> (P primary / S secondary). Review before harvest:

| # | Date | Type | Source / Outlet | Summary | URL |
|---|------|------|-----------------|---------|-----|
| s001 | 2024-03-15 | youtube | <channel> | Fireside on building <co> | https://… |
| s002 | 2023-11-02 | article | <site> | Essay on hiring under uncertainty | https://… |
| s003 | 2023-09-10 | podcast | <show> | 60-min interview, has transcript | https://… |

Reply to: remove rows, add URLs I missed, or approve to start harvesting.
```

## Rules
- **One row = exactly one source, every row, including in chat.** Never collapse multiple sources into a single row, a range (`s005–s008`), or a comma-separated list. If there are 38 sources, show 38 rows.
- **Every row must include its own `URL`.** Do not omit the URL in the chat version to save space — it's how the user audits and prunes.
- Keyed by its `id` from `sources.jsonl`.
- `Date`: best known publish date (`YYYY-MM-DD`, or `~YYYY` if approximate).
- `Type`: article · interview · youtube · podcast · radio · talk · thread · paper · profile · book.
- For a **book**, note in `Summary` how it'll be ingested — *user file* (legally owned EPUB/PDF) or *public only* (sample/preview/summaries) — so the user can supply the file at the review gate if they have one.
- `Summary`: ≤ 12 words, what it covers.
- Sort by **date descending (newest first)** — this also surfaces the highest-priority (most recent) sources at the top. You may add type sub-headings, but each source still gets its own full row with URL.
- If the list is long, show it all anyway (paginate in one message); a long table is fine — silently truncating the source list is not.
- After approval, set pruned rows to `status:"dropped"` in `sources.jsonl` (don't delete the line — keep the registry auditable).

## Disk mirror (`sources.md`)
Same table, plus a header line: `# Sources — <Author> — built <date> — N sources`.
