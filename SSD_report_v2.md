# SSD Analysis — Updated Report (Part A extended + Part B)

## What's new in this update
- Part A extended from 11 to **16 constructs**: added `gender`, `sexuality`, `special_interests`, `growing_up_difficulties`, `adjustment`. Cross-construct Holm correction recomputed across all 16.
- **Part B run for the first time**: within the autistic subsample only, comparing `diagnosis` and `medical_history` construal between childhood-diagnosed and adult-diagnosed authors.
- Known open item (not acted on, per team decision): 3 low-confidence ASD file matches (*Born on a Blue Day*, *Glass Half Empty, Glass Half Full*, *Asperger Syndrome Universe*) remain unverified — flagged for future manual check.

---

## Part A (extended) — still confounded by era, same limitation as before

All 16 constructs, sorted by effect size:

| Construct | n kept | Cohen's d | p (Holm, across 16) |
|---|---|---|---|
| emotion | 215 | 5.32 | .0032 |
| mind_thinking | 215 | 5.21 | .0032 |
| friendship_relationships | 215 | 4.99 | .0032 |
| communication | 215 | 4.95 | .0032 |
| routine_control | 215 | 4.90 | .0032 |
| self_identity | 211 | 4.85 | .0032 |
| family | 215 | 4.73 | .0032 |
| growing_up_difficulties | 215 | 4.67 | .0032 |
| senses_body | 215 | 4.55 | .0032 |
| difference_normalcy | 215 | 4.50 | .0032 |
| special_interests | 212 | 4.43 | .0032 |
| childhood_memory | 215 | 4.35 | .0032 |
| work_achievement | 215 | 4.17 | .0032 |
| gender | 215 | 4.11 | .0032 |
| adjustment | 213 | 3.87 | .0032 |
| sexuality | 166 | 2.84 | .0032 |

Same reading as before applies to all 16: this is the contemporary-vs-archaic register artifact from the era-confounded corpus (see the original Part A report for the qualitative word-level evidence), not a construct-specific autism signal. `sexuality` stands out as the one construct with both the lowest coverage (166/215 documents even mention it) and the smallest — though still very large — effect size, consistent with it being a less consistently-discussed topic across autobiographies generally.

## Part B (new) — within the autistic subsample, no era confound

This analysis stays entirely inside the 97 autistic-authored texts (all published 1986–2023), so the register confound above does not apply here. `time_of_diagnosis` was free text (e.g. "childhood", "adulthood (30)", "36"), so it was recoded into a binary **childhood-diagnosed vs. adult-diagnosed** split (standalone ages <18 and any mention of "child"/"adolescen"/"teen" → childhood; "adult"/"elderly"/"middle age" or age ≥18 → adulthood). 5 of 97 documents had no usable value and were excluded. Recoding rule is fully transparent above — worth a quick sanity check from your side since it's a judgment call, not a fact from the data.

**Resulting groups: 55 adult-diagnosed, 37 childhood-diagnosed.**

| Construct | n kept | Cohen's d | p (raw) | p (Holm, across 2) |
|---|---|---|---|---|
| diagnosis | 87 | 1.38 | .029 | .059 |
| medical_history | 91 | 1.01 | .036 | .059 |

Both are nominally significant before correction, borderline after correcting for the two tests (p≈.059) — this is a much more plausible effect size range than Part A (d≈1–1.4 vs. d≈4–5), and, importantly, **the nearest-neighbour words show no register artifact this time** — both poles are contemporary vocabulary, thematically coherent:

- **diagnosis**: adult-diagnosed pole → *want, know, try, you, sure* (agentic, reflective framing) — childhood-diagnosed pole → *infant, divided, separated, surrounded, constructed* (early-developmental framing)
- **medical_history**: adult-diagnosed pole → *hurry, wait, go, back, waiting* (plausibly: the "years of waiting for a diagnosis" narrative common in late-diagnosis memoirs) — childhood-diagnosed pole → *concepts, fundamental, theoretical, diversity, emphasis* (plausibly: therapy/educational-framework language typical of childhood intervention contexts)

This reads as a genuine, interpretable pattern rather than an artifact — but it's exploratory (borderline correction, moderate N, only 2 constructs tested, and the childhood/adulthood recoding is my rule, not yours), so treat it as a promising lead worth writing up carefully rather than a confirmed finding.

## Files
- `part_a_summary_FULL.csv` — all 16 Part A results
- `part_b_summary.csv` — Part B results
- `combined_metadata.csv` (sent earlier) — the master text+metadata table these all run on
