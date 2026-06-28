# Faithfulness Check — Lucas O'Keefe Clone
*Phase 4c smoke test: 7 held-out probes*

---

## Probe 1
**Question:** "Should a business with 500 followers focus on growing to 10K before they start selling?"

**Cold prediction (from EP model):**
No. Lucas believes small audiences are sufficient for service businesses. "Start at 100, start at 200 — just actively talk about what you are passionate about, what you can help with, and what you are confident in delivering." Most service businesses need 5 clients, not 500 followers. The 10K milestone is overrated — it was linked to the swipe-up Stories feature, which no longer requires 10K anyway.

**Real text (EP e_s005_025):**
"You don't need 10,000 followers to make your first sale. Many people prioritize that. I say start at 100, start at 200, just actively talk about what you are passionate about, what you can help with, and what you are confident in delivering."

**Verdict:** ✅ MATCH

---

## Probe 2
**Question:** "What's the single best Instagram metric to track for growth?"

**Cold prediction (from EP model):**
Saves. Lucas explicitly argues saves are harder to fake than likes/comments, and signal to Instagram that a viewer plans to return — which the algorithm interprets as high-quality content. Shares matter for new reach, but saves matter for depth of value signal.

**Real text (EP e_s005_016):**
"Saves are the best metric in my opinion. Instagram ranks: likes, comments, saves, and shares. Shares are good to get you out to new people — but likes, comments, those can really be fabricated."

**Verdict:** ✅ MATCH

---

## Probe 3
**Question:** "What's the best Instagram content format for a new creator?"

**Cold prediction (from EP model):**
Carousels are his #1 recommendation for beginners — they maximize dwell time, earn saves (mini-ebook effect), can be templated to 30 min production once set up, and are shown twice by the algorithm. The dominant format should match the creator's strengths, but carousels are the safest starting point.

**Real text (EPs on carousel-tactics):**
"Carousels are great in my opinion because of dwell time... If it is like a mini guide that is a carousel, like a mini ebook almost, people are very likely to save those." Plus ACCEL framework recommends choosing your "dominant content type."

**Verdict:** ✅ MATCH (with nuance: he allows for format flexibility based on strengths)

---

## Probe 4
**Question:** "How should you use Stories vs. feed posts for sales?"

**Cold prediction (from EP model):**
Strict separation: feed = discovery and value; Stories = sales and conversion. Selling in the feed too often damages community trust. Stories are ephemeral and casual — pitch there repeatedly without burning the feed relationship.

**Real text (EPs on stories-strategy):**
"Your main feed content is what gets you discovered. Your stories are how people decide if they like you and if they want to buy from you." + "Stories can be your secret weapon to get sales, to pitch your offer, to talk about what you're selling."

**Verdict:** ✅ MATCH

---

## Probe 5
**Question:** "Lucas went full-time as a creator in 2020 during COVID. True or false?"

**Cold prediction (from EP model):**
False. Lucas *started* creating during COVID lockdowns (March 2020) while still teaching. He taught full-time AND created content from 5pm to 2am for 4 years. He only went full-time as a creator in January 2024, when the school board refused to grant him a leave of absence.

**Real text (EP e_s004_009):**
"I retired from teaching — I had to resign from the board because they wouldn't give me a leave to work on my business. I had to choose and I chose my business as a full-time content creator. That was January of 2024. I was doing both for four years."

**Verdict:** ✅ MATCH — model correctly holds the distinction

---

## Probe 6
**Question:** "What does Lucas think about posting daily on Instagram?"

**Cold prediction (from EP model):**
He distinguishes consistency from frequency. Quality over quantity. 4-5 posts per week (not daily) is his recommendation. "Consistency is not to be confused with frequency — it's about showing up for a long period of time." Unsustainable frequency leads to burnout and content quality decline.

**Real text (EP on 4-1-1 / ACCEL):**
"Quality is now more important than quantity when it comes to your content. Consistency is not to be confused with frequency. It's about showing up for a long period of time." ACCEL recommends 4-5 posts/week.

**Verdict:** ✅ MATCH

---

## Probe 7
**Question:** "What's Lucas's primary revenue source as a creator?"

**Cold prediction (from EP model):**
Brand partnerships, ~90-95% of his revenue. He discovered this by accident in summer 2021 when a brand reached out, realized he loved it, and built his business around it. He also has digital products (content calendar) on a low-price/high-volume model, but those are secondary.

**Real text (EP e_s004_020):**
"Being an influencer fell into my hands — a brand just reached out and was like hey we'd like to sponsor a post and I'd never thought of it. It was summer of 2021. My business is pretty much entirely 90%, 95% brand partnerships."

**Verdict:** ✅ MATCH

---

## Summary

| Probe | Topic | Verdict |
|-------|-------|---------|
| 1 | Follower count before selling | ✅ MATCH |
| 2 | Best metric to track | ✅ MATCH |
| 3 | Best content format | ✅ MATCH (with nuance) |
| 4 | Feed vs. Stories for sales | ✅ MATCH |
| 5 | When he went full-time | ✅ MATCH |
| 6 | Daily posting philosophy | ✅ MATCH |
| 7 | Primary revenue source | ✅ MATCH |

**Score: 7/7 match** — model is faithful to sources. Confidence is appropriately high for well-documented positions. Time-bound caveat: Platform mechanic views (Reels vs. carousels, SEO signals) reflect 2021-2025 data and should be treated as `as_of` bounded.

*Caveat: This is a small-N smoke test (7 probes), not a proof of faithfulness. The clone may drift on topics not covered by current sources.*
