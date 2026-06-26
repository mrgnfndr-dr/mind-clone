# Language protocol

## Conversation language
- **First interaction of a session:** ask the user which language they'd like to talk in. Offer at least: the language their message arrived in, and English. Keep the question short.
- Persist the answer in `manifest.json` as `"chat_language": "<code or name>"`. On subsequent sessions, read it and **do not ask again** (unless the user switches).
- From then on, **converse entirely in the chosen language** — questions, summaries, the clone's answers, everything the user reads.
- If the user starts writing in a different language mid-session, follow them and update `chat_language`.

## Artifact language (always English)
Everything written to disk stays in **English**, regardless of chat language:
- `clone.db`, `MANIFEST.md`, `sources.jsonl`, `sources.md`, `evidence.jsonl`, `raw/*`, `cognitive-model.md`, `reasoning-traces.md`, `persona.md`, `manifest.json`.

Why: keeps each clone portable and shareable on GitHub, and keeps the cognitive model in one canonical language for consistent reasoning. Translate to the user's language only at the moment of display.

## Source-content language
Sources may be in any language. When extracting evidence quotes:
- Keep the **verbatim quote in its original language**, and add an English `note` with a faithful translation if the quote isn't English.
- Write `topic`, `kind`, and all surrounding analysis in English.

## Quoting the author in CHAT mode (display language)
The whole answer — including the author's quotes — must read in the **user's chat language**. But a quote is evidence: the deep-link points at the author's *actual words* in the source's original language, so we must never silently swap those words for a translation.

Rule when the **source language differs from the chat language** (e.g. English source, Russian chat):
1. **Lead with a faithful translation** of the quote into the user's language, inside the quote marks, so the answer flows in their language.
2. **Always keep the verbatim original** right beside it, on an `оригинал:` / `original:` sub-line (or inline after), in the source language.
3. The **deep-link attaches to the original** — it's what's verifiable.
4. **Never present a translation alone as a verbatim quote.** A translated string in quote marks with a source link, but no original, reads as something the author literally said in that language — that's a fabricated quote and violates the no-fabrication guardrail. The translation is for comprehension; the original is the citation.

When the **source language already equals the chat language**, just show the single verbatim quote — no translation line needed.

Concrete format lives in `04-clone-runtime.md` → "Cite the author with deep-links".
