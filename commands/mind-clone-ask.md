---
description: Ask a mind-clone of an author — advice, or their likely view on a topic
argument-hint: <author> <question>  |  what would <author> think about <topic>
---

Invoke the **mind-clone** skill in **CHAT mode** for this request.

Arguments: $ARGUMENTS

- Resolve which clone is meant: match `$ARGUMENTS` against the folders in `./clones/`. If the author is named, use that clone; if only a question is given and exactly one clone exists, use it; if ambiguous or none exists, list `./clones/` and ask (do NOT start a build from this command).
- Then follow `reference/04-clone-runtime.md`: route by question type — how-to/method questions from `playbook.md` (concrete steps), advice grounded in documented beliefs, or a confidence-rated prediction (clearly labeled as extrapolation). Grounded answers quote the author with deep-links to the exact minute.
- Follow the language protocol: reply in the user's chat language (from `manifest.json`); keep saved artifacts in English.
- This command never builds or modifies a clone — it only reads. To build, use `/mind-clone-build`.
