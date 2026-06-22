# Language protocol

## Conversation language
- **First interaction of a session:** ask the user which language they'd like to talk in. Offer at least: the language their message arrived in, and English. Keep the question short.
- Persist the answer in `manifest.json` as `"chat_language": "<code or name>"`. On subsequent sessions, read it and **do not ask again** (unless the user switches).
- From then on, **converse entirely in the chosen language** — questions, summaries, the clone's answers, everything the user reads.
- If the user starts writing in a different language mid-session, follow them and update `chat_language`.

## Artifact language (always English)
Everything written to disk stays in **English**, regardless of chat language:
- `sources.jsonl`, `sources.md`, `evidence.jsonl`, `raw/*`, `cognitive-model.md`, `reasoning-traces.md`, `persona.md`, `manifest.json`.

Why: keeps each clone portable and shareable on GitHub, and keeps the cognitive model in one canonical language for consistent reasoning. Translate to the user's language only at the moment of display.

## Source-content language
Sources may be in any language. When extracting evidence quotes:
- Keep the **verbatim quote in its original language**, and add an English `note` with a faithful translation if the quote isn't English.
- Write `topic`, `kind`, and all surrounding analysis in English.
