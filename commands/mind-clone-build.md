---
description: Build a mind-clone of an author from their public content
argument-hint: <author name>  [--archive-raw]  [quick|standard|exhaustive]
---

Invoke the **mind-clone** skill in **BUILD mode** for this request.

Arguments: $ARGUMENTS

- Treat `$ARGUMENTS` as the author to clone (plus optional flags: `--archive-raw` to additionally keep more *book* text — transcripts/article text are already saved by default; depth `quick|standard|exhaustive`).
- Run the full pipeline in `SKILL.md`: discovery → source table (review gate) → harvest (extract-on-the-fly, with timestamps + deep-links) → cognitive model → playbook (if the author teaches a methodology) → finalize. Write everything under `./clones/<author-slug>/`.
- If a clone for this author already exists, ask whether to update/rebuild it or just talk to it (`/mind-clone-ask`) before overwriting.
- Follow the language protocol (ask chat language on first use; artifacts in English) and the quality gates (no fabrication, report every coverage gap).
- To talk to an existing clone instead, use `/mind-clone-ask`.
