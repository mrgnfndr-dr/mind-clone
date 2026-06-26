# Phase 1 — Discovery (exhaustive search)

Goal: find **everything public** the author produced or appeared in — not the first page of results. Treat this like a multi-modal sweep where each angle is blind to the others.

Tools: built-in `WebSearch` and `WebFetch` (always available). No paid APIs required.

## Step 1 — Identity map (do this before searching)

Build the set of query handles. Public figures appear under many forms:

- **Name variants**: full name, short/Western form, native-script form, transliterations, nicknames, maiden/former names, handles. (e.g. "Alexander Mashrabov" / "Alex Mashrabov" / "@mashrabov").
- **Affiliations as anchors**: every company/role/project, current and past. Searching "<name> <company>" surfaces interviews and talks that bare-name search misses.
- **Co-occurrence anchors**: co-founders, frequent interviewers, podcasts they recur on, conferences.

Confirm the identity map with the user if there's ambiguity (common name, multiple people). Save the variants — they go into `config.json` (state) and are reused in CHAT mode.

## Step 2 — Multi-modal sweep

Run searches across **each** channel separately. For every query, vary the handle (name variant × affiliation × channel keyword). Don't stop at the first result set — paginate and re-query with different phrasings until new queries stop surfacing new sources.

| Channel | Query patterns | Notes |
|---|---|---|
| Long-form text | `<name> essay/blog/article/op-ed`, `<name> writes` | Personal site, Substack, Medium, Paul-Graham-style essays |
| Interviews (text) | `<name> interview`, `<name> Q&A`, `<name> AMA` | Often the richest source of *reasoning* |
| YouTube | `<name>` on youtube, `<name> talk/keynote/fireside/panel/podcast` | Capture video IDs/URLs for Phase 3. **Also check video *descriptions*, not just titles** — guests are often named only in the description (a trends-y clickbait title can hide a real interview). See note below. |
| Podcasts | `<name> podcast`, `<show name> <name>` | Note if show notes/transcripts exist |
| Radio / audio | `<name> radio`, `<name> NPR/BBC/<local outlet>` | |
| Talks / slides | `<name> conference`, `<name> slides/deck` | |
| Social long-form | `<name> twitter/X thread`, LinkedIn posts | Threads encode condensed opinions |
| Academic / technical | Google Scholar, arXiv, patents | For technical authors |
| **Books** | `<name> book`, publisher page, Goodreads/Amazon author page, Google Books | A book is often the author's most complete, structured methodology — high value, esp. for a playbook. See acquisition note below. |
| Press / profiles | Profiles, founder interviews, press releases | Biography + stated positions |

### Books — register the book, then resolve how to read it (Phase 3 decides)
If the author has written a book, **add it as a source** (`type:"book"`) even before you know how you'll read it — but record how it can be ingested, because that's an ethics/acquisition fork resolved in harvest:
- **Ask the user** whether they have a legally-owned copy (EPUB/PDF/Kindle) they can supply — that unlocks full extraction. Note it in the source (`acquire:"user_file"` once provided).
- If not, register what's **publicly available**: publisher sample chapters, Google Books preview, the author's own talks/interviews/posts *about* the book, reputable detailed summaries (mark these `voice:secondary`). `acquire:"public_only"`.
- **Never** plan to pull the book from a pirate/shadow library — see `reference/ethics.md`.

### YouTube descriptions (catch title-less mentions) — cheap
A guest is frequently named only in a video's **description**, not its title, so title/snippet search misses them. This is cheap to fix because `yt-dlp` pulls **metadata only** (no video download), seconds per clip:
- For ambiguous/candidate videos: `yt-dlp --skip-download --print "%(title)s | %(upload_date)s | %(description)s" "<url>"` and check whether the author is named.
- For known recurring channels (interviewers, podcasts, conferences the author appears on): enumerate recent uploads' metadata and grep the descriptions for the name variants.
Do this as a targeted pass over candidates/channels — not over all of YouTube (which needs the API).

### Step 2.5 — Exhaustive appearance enumeration (catch missed podcasts/interviews)
Name+keyword search reliably *misses* podcast and interview appearances. Add these passes — they're the single biggest completeness win:
- **Podcast aggregators that list a person's full appearance history in one place:** ListenNotes, Podchaser, and the guest's Apple Podcasts / Spotify "person" pages. One query there often returns every show they've been on.
- **The author's own announcements.** People post "I was on @podcast / here's my talk." Scan their X and LinkedIn feeds for `podcast`, `episode`, `talk`, `interview`, links to Spotify/Apple/YouTube — each is a source you'd otherwise miss.
- **Topic-anchored search.** Search the *topics the author is known for*, not just their name: `<topic> <name>`, `<hot topic in their field> interview`. An interview is often indexed by its subject, not the guest — e.g. a talk on a niche trend whose title never mentions the person.
- **Co-occurrence enumeration.** For each recurring host/show/conference found, enumerate their recent episodes/lineups and check for the author.

### Step 2.6 — Completeness critic (loop until dry)
Before closing discovery, run an explicit "what's missing?" pass: a channel not swept, a platform not checked (regional/native-language ones), a topic the author is known for but has no source, a time period with a gap. Re-query for those. **Repeat until two consecutive passes surface nothing new.** Then ask the user if they know of sources you might have missed (they often do — a podcast they remember, a talk). Treat user-supplied links as first-class and run them through harvest.

## Step 3 — Triangulate and deduplicate

- The same talk may exist as video + transcript + article. Keep them as **separate sources** if they add coverage, but cross-link in the registry.
- Prefer **primary** (the author's own words) over **secondary** (someone describing them). Mark each `voice: primary | secondary`.
- Discard pure SEO spam, AI-generated rehashes, and namesakes (wrong person).

## Step 4 — Write the source registry

Each source becomes a **`meta` row**, emitted as a `_t:"meta"` line in the harvest delta and loaded via `loop.py import` (never a persisted `sources.jsonl`):

```json
{"_t":"meta","id":"s001","date":"2024-03-15","type":"youtube","title":"Fireside: building <company>","url":"https://...","outlet":"<channel>","duration_min":42,"hash":"<raw content hash>","raw_path":"raw/s001.srt"}
```

- `id`: stable, sequential (`s001`…). Never reused.
- `type`: `article | interview | youtube | podcast | radio | talk | thread | paper | profile | book`.
- `status`: `pending` → set to `harvested` / `failed` in Phase 3.
- `summary`: written now from search snippets; refined after harvest.

## Depth control

Ask the user (or infer) how deep to go:
- **quick** — top ~15 highest-signal primary sources.
- **standard** (default) — 30–50+ sources, all channels swept once.
- **exhaustive** — sweep until queries stop yielding new sources; aim to saturate.

If you find fewer than expected, **report the actual count** ("found 22 primary sources") — never pad with low-quality filler to hit a number.
