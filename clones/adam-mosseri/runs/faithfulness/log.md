# Faithfulness smoke test — Adam Mosseri clone (built 2026-06-27)

Method: predict a clear, checkable Mosseri position *cold* (from the model's reasoning),
then compare to the stored EP `text`. Score: match / partial / miss / **contradiction**.
Small-N, indicative only — never tuned against.

| # | Probe | Cold prediction | Real EP | Verdict |
|---|-------|-----------------|---------|---------|
| 1 | Top ranking signal for reach | sends/shares per reach (sends to friends) | e_s005_29, e_s001_05: "sends per reach … likes per reach" | **match** |
| 2 | Stalled creator: start a new account? | No — revive the old one | (not in corpus — advice lived in an excluded out-of-window clip) | **not-in-corpus** (correctly absent; would be flagged as inference) |
| 3 | Per-view revshare like YouTube AdSense? | No; feed revshare is uneconomic ("burning cash"); prefers bonuses/tools; must be ROI-positive | e_s011_39, e_s001_21 | **match** |
| 4 | Do hashtags drive reach? | Barely; a myth | e_s002_19: "hashtags are no longer a primary way … don't significantly" | **match** |
| 5 | Is shadowbanning real? | Not a secret switch; it's account status / recommendability | e_s009_33: "Shadow banning means different things to different people" | **match** |
| 6 | Photos vs video | Over-pushed video, walked it back; photos efficient to produce | e_s008_15: "not everyone's going to be able to make videos" | **match (partial)** |
| 7 | AI "slop" | Commoditized AI isn't defensible; judge by source & intent; not "truth police" | e_s011_26 (source/intent), e_s008_34 (commoditized = not defensible) | **match** |
| 8 | Where growth comes from | Unconnected/recommended reach to non-followers | e_s001_10: "unconnected versus connected … two [audiences]" | **match** |

**Result: 7 match, 1 not-in-corpus, 0 partial-miss, 0 contradictions.**
No contradictions surfaced. The single non-match is a genuine coverage gap (the position
exists in Mosseri's public output but only in sources outside the user's date/length window),
not model drift. Treat as indicative, not proof.
