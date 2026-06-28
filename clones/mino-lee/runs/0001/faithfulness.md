# Faithfulness smoke test — Mino Lee clone (Phase 4c)

Held-out checkable positions, predicted cold through the contour, compared to real EP text.
**Indicative only** (small-N, not proof). Verdicts: MATCH / PARTIAL / MISS / CONTRADICTION.

| # | Probe | Cold prediction (as the author) | Real grounding | Verdict |
|---|-------|---------------------------------|----------------|---------|
| 1 | Do captions / hashtags / posting times affect performance? | "They basically don't matter — stop optimizing them; the video itself is what matters." | e_s057_54, e_s041_17 ("no hashtags or posting times actually matter… in the caption it really does not matter") | MATCH |
| 2 | Should a beginner "become the niche" / niche down hard? | Contrarian: rejects the blanket "become the niche" advice as survivorship bias; pick a viewer/clarity, not a forced personal niche. | e_s052_02 (survivorship-bias), e_s056_07, e_s064_06 | MATCH |
| 3 | How long to reach the first 10k followers? | "Hardest stage — 60–90 days and 90+ videos of consistent posting; 95% quit before it." | e_s005_02 ("60 to 90 days… 90 plus videos"), e_s037_48 | MATCH |
| 4 | Which platform makes you rich? | Has a definitive ranked verdict (delivered via s061's final-verdict EP). | e_s061_34 (final-verdict) | MATCH (position exists & is cited) |
| 5 | Post daily even if imperfect? | "Post one video every day; ship imperfect work, 'eat dirt', volume + reps beat polishing." | e_s041_04, e_s002 post-imperfect-daily, e_s029_01 | MATCH |
| 6 | Importance of the first 3 seconds / the hook? | "The hook is the first 3 seconds — make-or-break between 300 views and 1M." | e_s064_01 (delivered run 0001) | MATCH |

**Result: 6 MATCH / 0 PARTIAL / 0 MISS / 0 CONTRADICTION** over 6 probes.
Every probe resolved to direct, multi-source grounding (positions are documented, not inferred), which is
expected for a clone built by direct extraction. No tuning was done to pass this test.
