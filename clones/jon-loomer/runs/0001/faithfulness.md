# Faithfulness smoke test — Jon Loomer clone (indicative only, small-N, not proof)

Held-out checkable positions, predicted cold via the contour (fts/map/select), compared to the
grounded `text`. Verdicts: match / partial / miss / contradiction.

| # | Probe | Predicted (as Jon) | Grounded EP | Verdict |
|---|-------|--------------------|-------------|---------|
| 1 | Detailed vs broad targeting in 2026? | Go broad for cold; split-test detailed, drop if it doesn't beat broad | e_s336_03, e_s336_04, e_s157_03 | **match** |
| 2 | Is retargeting/remarketing still necessary? | No — was ~90% of his budget, now unnecessary; lacks incrementality | e_s130_01, e_s011_04 | **match** |
| 3 | Do best practices guarantee results? | No — you can do everything right and still not get results | e_s005_06 | **match** |
| 4 | Should you "warm up"/season a new account or pixel? | No — it's a myth, can even hurt | e_s031_01, e_s420_01 | **match** |
| 5 | How to think about attribution by default? | Foundation-of-fact: Meta counts a click→convert in window; don't overreact to layers | e_s098_05, e_s142_01 | **match** |
| 6 | Advantage+ Shopping and targeting control? | You have virtually no targeting impact in ASC | e_s460_01 | **match** |

End-to-end contour cycle (run 0001): intent → map → select → compile → answer (reasoned as Jon)
→ `verify` = **ACCEPTED** (5 citations, all resolve to delivered EPs).

**Result: 6/6 match, 0 contradiction.** Indicative only — the probes are signature positions with
dense coverage; thin domains (low-level auction mechanics, hands-on creative production) are less
certain. Not tuned to pass.
