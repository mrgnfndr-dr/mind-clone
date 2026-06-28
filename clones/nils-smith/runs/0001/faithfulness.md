# Faithfulness smoke test — Nils Smith clone (build)

Method: 6 held-out probes across domains. For each, the target source was excluded and the
position predicted *cold* from the rest of the corpus, then compared to the held-out EP text.
Smoke test only — small-N, indicative, not proof.

| # | Probe (domain) | Held-out src | Cold prediction | Real position | Verdict |
|---|---|---|---|---|---|
| 1 | Should a church build its own mobile app? (church) | s024 | Cautious/usually no — apps are expensive; only if your audience has clearly adopted them and you can justify the cost/maintenance | "say no" — too expensive & ineffective for the cost/time over the last 10 years; 4 reasons against | **match** |
| 2 | Host your podcast on Kajabi? (creator-business) | s011 | No — use a dedicated host (Libsyn); Kajabi is all-in-one but podcast hosting isn't its strength | Antipattern: don't host the podcast on Kajabi, use Libsyn | **match** |
| 3 | Org account vs founder personal brand? (social) | s004 | Founder/personal brand carries more reach than the org account | Founder-led personal brands beat org accounts ("LinkedIn front door") | **partial** — theme present, but the specific claim is concentrated in s004; cross-source signal is thin |
| 4 | Is an expensive webcam worth it vs a cheap one? (gear) | s010 | No — "good enough" + cost-to-value; a cheap option that's nearly as good wins | $50 Logitech beats the $200 Lumina; not worth the premium | **match** |
| 5 | Nils's biggest concern about AI? (ai) | s028 | Not job loss per se — loss of purpose; response is to lean in, not fear | "my biggest fear of AI is... not even the loss of jobs... it's the loss of purpose"; lean in | **match** (corroborated in s023) |
| 6 | Auto vs custom YouTube thumbnails? (content) | s026 | Always create a custom, eye-catching thumbnail; never rely on auto | Antipattern: never use auto-generated thumbnails; the thumbnail is the #1 view driver | **match** |

## Headline
**5 match · 1 partial · 0 miss · 0 contradiction.** No confident-wrong drift surfaced.

## Calibration notes (feed into CHAT confidence)
- **Personal-brand vs org-account** (probe 3) rests largely on a single recent source (s004); the
  pre-cutoff "Should Pastors Have a Personal Brand" video was excluded by the >2024-06-01 rule.
  Treat this claim as M-confidence, not H.
- Thin/​absent domains (lower confidence in CHAT): deep crypto/web3 thesis (only 2 EP, the HeatBit
  miner), and anything pre-June-2024 (deliberately out of scope).
- Indicative only — covers the 6 probes chosen, not the whole model.
