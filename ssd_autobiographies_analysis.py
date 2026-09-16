"""
==============================================================================
SSD analysis: semantic construal of psychological constructs in
autism-spectrum vs. non-autistic autobiographies
==============================================================================

Built on the `ssdiff` package (Supervised Semantic Differential;
Plisiecki, Lenartowicz, Pokropek, Malyska & Flakus, 2025 -
https://doi.org/10.31234/osf.io/gvrsb_v1).

WHAT THIS SCRIPT DOES
----------------------
PART A - GROUP COMPARISON (main analysis)
    For each construct in CONSTRUCTS_GROUP_COMPARISON (self/identity,
    senses/body, family, ...):
      1. Anchors the construct with a seed lexicon (lemmatized).
      2. Builds one Personal Concept Vector (PCV) per document from local
         contexts around the lexicon.
      3. Compares construal between the "autistic" and "non_autistic"
         groups via ssd.fit_groups() (permutation inference).
      4. Collects omnibus p-values across ALL tested constructs and
         applies an ACROSS-CONSTRUCT correction on top of the
         within-test correction ssdiff already applies to pairwise
         contrasts (only relevant once you have >2 groups; with exactly
         2 groups the across-construct correction below is the one that
         matters, because you are running one test per construct).

PART B - WITHIN-AUTISTIC GRADIENT (secondary analysis)
    Constructs in CONSTRUCTS_WITHIN_AUTISTIC (diagnosis, medical_history)
    will have near-zero coverage in non-autistic texts, so comparing them
    across groups mostly tests "do they mention this at all" rather than
    "how do they construe it". Instead, within the autistic subsample
    only, this block relates construal of these constructs to
    time_of_diagnosis (continuous, via fit_pls) and/or diagnosis subtype
    (categorical, via fit_groups).

BEFORE RUNNING
--------------
- pip install ssdiff statsmodels   (add ssdiff[results] for .docx/.xlsx export)
- point EMBEDDINGS_PATH at a pretrained embeddings file matching LANG
  (see the ssdiff README for supported formats and a Polish source)
- point METADATA_PATH at your coded spreadsheet - one row per UNIT OF
  ANALYSIS (see note below), with a column holding the path to that
  unit's .txt file
- rename TEXT_COL / GROUP_COL / TIME_OF_DX_COL / DIAGNOSIS_COL to match
  your actual column names
- edit / extend CONSTRUCTS_* freely - these are starting points, not a
  fixed list

A NOTE ON UNIT OF ANALYSIS
---------------------------
fit_groups() drops any group with fewer than 20 documents, and the SSD
validation study used hundreds of short, single-topic essays per group.
Whole autobiographies are usually far fewer in number (tens, not
hundreds) and much longer / multi-topic, which is a mismatch with that
design. If you have few complete books, consider using CHAPTERS as the
unit of analysis instead (you already code "chapters") - each chapter
becomes one "document", inheriting its book's group/covariate labels.
This also opens a bonus analysis: whether construal shifts across the
narrative arc (early vs. late chapters) - not implemented here, but a
straightforward extension once texts are chapter-split.
==============================================================================
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ssdiff import Embeddings, Corpus, SSD

# ----------------------------------------------------------------------------
# 0. CONFIG - edit this section to match your data
# ----------------------------------------------------------------------------

LANG = "en"  # "pl" or "en" - must match BOTH the texts and the embeddings model
EMBEDDINGS_PATH = "embeddings/glove.840B.300d.txt"  # any large pretrained English GloVe/word2vec file - see ssdiff README

METADATA_PATH = "metadata.xlsx"        # your coded spreadsheet, one row per unit of analysis
TEXT_COL = "text_path"                 # column holding the path to each unit's .txt file
GROUP_COL = "group"                    # values: "autistic" / "non_autistic"
TIME_OF_DX_COL = "time_of_diagnosis"   # numeric age/year at diagnosis; empty for non-autistic rows
DIAGNOSIS_COL = "diagnosis"            # subtype label; only present for autistic rows

UNIT_OF_ANALYSIS = "chapter"           # "book" or "chapter" - see note above

OUTDIR = Path("ssd_results")
OUTDIR.mkdir(parents=True, exist_ok=True)

N_PERM = 5000
RANDOM_STATE = 2137
WITHIN_TEST_CORRECTION = "holm"        # ssdiff's own pairwise correction (fit_groups)
CROSS_CONSTRUCT_CORRECTION = "holm"    # applied below, across the constructs we loop over

# ----------------------------------------------------------------------------
# 1. Candidate constructs & seed lexicons
#    Lemmatized base forms only - SSD matches against corpus.docs (lemmas).
# ----------------------------------------------------------------------------

CONSTRUCTS_GROUP_COMPARISON = {
    "self_identity": {
        "pl": ["ja", "osobowość", "tożsamość", "charakter"],
        "en": ["self", "identity", "personality", "character"],
        "rationale": "Self-construal: trait/individual framing vs. relational/role framing.",
    },
    "difference_normalcy": {
        "pl": ["inny", "odmienny", "normalny", "wyjątkowy"],
        "en": ["different", "normal", "unusual", "unique"],
        "rationale": "Otherness/'fitting in' recurs across disability life-writing generally, not only ASD.",
    },
    "senses_body": {
        "pl": ["dźwięk", "hałas", "dotyk", "światło", "zmysł"],
        "en": ["sound", "noise", "touch", "light", "sense"],
        "rationale": "Sensory-processing differences are a hallmark of autistic experience; framing may differ even where both groups mention senses.",
    },
    "communication": {
        "pl": ["mówić", "rozmowa", "słowo", "język"],
        "en": ["talk", "conversation", "word", "language"],
        "rationale": "Social-communication framing (effort, directness, difficulty) is theorised to differ (cf. the 'double empathy problem').",
    },
    "friendship_relationships": {
        "pl": ["przyjaciel", "znajomy", "relacja", "samotność"],
        "en": ["friend", "relationship", "loneliness"],
        "rationale": "Tests whether friendship/loneliness is construed differently, not just mentioned at different rates.",
    },
    "family": {
        "pl": ["rodzina", "matka", "ojciec", "dom"],
        "en": ["family", "mother", "father", "home"],
        "rationale": "Near-universal in autobiography - a good high-coverage baseline construct.",
    },
    "emotion": {
        "pl": ["czuć", "emocja", "uczucie", "strach"],
        "en": ["feel", "emotion", "feeling", "fear"],
        "rationale": "Emotional-experience framing (intensity, alexithymia-adjacent language) recurs in first-person ASD accounts.",
    },
    "routine_control": {
        "pl": ["rutyna", "porządek", "kontrola", "zasada"],
        "en": ["routine", "order", "control", "rule"],
        "rationale": "Preference for predictability/order is a classic ASD theme; worth testing whether/how it appears in non-ASD writers too.",
    },
    "work_achievement": {
        "pl": ["praca", "kariera", "sukces", "zawód"],
        "en": ["work", "career", "success", "job"],
        "rationale": "Ties to your existing 'occupation' coding; tests external-recognition vs. personal-fit/mastery framing.",
    },
    "childhood_memory": {
        "pl": ["dzieciństwo", "wspomnienie", "dziecko"],
        "en": ["childhood", "memory", "child"],
        "rationale": "Almost every autobiography narrates childhood - another strong-coverage baseline construct.",
    },
    "mind_thinking": {
        "pl": ["myśleć", "umysł", "myśl", "rozumieć"],
        "en": ["think", "mind", "thought", "understand"],
        "rationale": "Theory-of-mind / meta-cognitive framing ('I think', 'people think') is a theoretically motivated axis in ASD narrative research.",
    },
}

# Autism-specific: expect near-zero coverage in non-autistic texts, so these
# are analysed WITHIN the autistic subsample (Part B), not across groups.
CONSTRUCTS_WITHIN_AUTISTIC = {
    "diagnosis": {
        "pl": ["diagnoza", "diagnostyka", "rozpoznanie"],
        "en": ["diagnosis", "diagnose", "assessment"],
        "rationale": "Framing of diagnosis (relief/identity vs. burden/label) may shift with age/timing of diagnosis.",
    },
    "medical_history": {
        "pl": ["lekarz", "terapia", "leczenie", "szpital"],
        "en": ["doctor", "therapy", "treatment", "hospital"],
        "rationale": "Framing of medical involvement (support vs. pathologisation) as a function of time_of_diagnosis / diagnosis subtype.",
    },
}

# ----------------------------------------------------------------------------
# 2. Data loading helpers
# ----------------------------------------------------------------------------

def load_metadata(path: str) -> pd.DataFrame:
    path = Path(path)
    if path.suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def load_texts(df: pd.DataFrame, text_col: str) -> list[str]:
    return [Path(p).read_text(encoding="utf-8") for p in df[text_col]]


def build_embeddings(path: str) -> Embeddings:
    emb = Embeddings.load(path, verbose=True)
    emb.normalize()  # L2 + ABTT(m=1), matches the SSD paper's defaults
    return emb


def build_corpus(texts: list[str], lang: str) -> Corpus:
    return Corpus(texts, lang=lang)


# ----------------------------------------------------------------------------
# 3. Lexicon quality check
#    Mirrors Table 2 of the SSD paper: coverage + lexicon-presence
#    correlation with the outcome. Run this BEFORE trusting a result -
#    a construct with very unequal coverage across groups, or a strong
#    lexicon-presence/outcome correlation, is confounding "do they mention
#    it" with "how do they construe it".
# ----------------------------------------------------------------------------

def check_lexicon(corpus: Corpus, y, lexicon: list[str], var_type: str = "categorical"):
    res = corpus.evaluate_lexicon(y, lexicon, var_type=var_type)
    print(res.summary)
    return res


# ----------------------------------------------------------------------------
# 4. PART A - group comparison (autistic vs. non-autistic)
# ----------------------------------------------------------------------------

def run_group_comparison(emb, corpus, group_labels, lexicon, name, outdir):
    ssd = SSD(emb, corpus, y=group_labels, lexicon=lexicon)
    result = ssd.fit_groups(
        n_perm=N_PERM, correction=WITHIN_TEST_CORRECTION, random_state=RANDOM_STATE
    )

    result.report(clusters={"n": 50, "n_words": 8, "n_snippets": 2}).save(
        outdir / f"{name}_group_report.md"
    )
    result.words.save(outdir / f"{name}_words.csv")
    result.pairs.save(outdir / f"{name}_pairs.csv")

    return result


def run_part_a(df: pd.DataFrame, emb: Embeddings) -> pd.DataFrame:
    texts = load_texts(df, TEXT_COL)
    corpus = build_corpus(texts, LANG)
    group_labels = df[GROUP_COL].tolist()

    summary_rows = []
    for name, spec in CONSTRUCTS_GROUP_COMPARISON.items():
        lexicon = spec[LANG]
        print(f"\n=== {name} ===  lexicon: {lexicon}")

        check_lexicon(corpus, group_labels, lexicon)  # inspect coverage/imbalance first
        result = run_group_comparison(emb, corpus, group_labels, lexicon, name, OUTDIR)

        summary_rows.append(
            {
                "construct": name,
                "omnibus_T": result.test.omnibus_T,
                "omnibus_p_raw": result.test.omnibus_p,
                "n_kept": result.n_kept,
            }
        )

    summary = pd.DataFrame(summary_rows)

    from statsmodels.stats.multitest import multipletests

    summary["p_corrected_across_constructs"] = multipletests(
        summary["omnibus_p_raw"], method=CROSS_CONSTRUCT_CORRECTION
    )[1]
    summary = summary.sort_values("p_corrected_across_constructs")
    summary.to_csv(OUTDIR / "part_a_summary.csv", index=False)
    print(summary)
    return summary


# ----------------------------------------------------------------------------
# 5. PART B - within-autistic gradient (time_of_diagnosis / diagnosis subtype)
# ----------------------------------------------------------------------------

def run_gradient(emb, corpus, y, lexicon, name, outdir, backend: str = "pls"):
    ssd = SSD(emb, corpus, y=y, lexicon=lexicon)
    result = ssd.fit_pls() if backend == "pls" else ssd.fit_ols()
    result.report().save(outdir / f"{name}_gradient_report.md")
    return result


def run_part_b(df: pd.DataFrame, emb: Embeddings) -> dict:
    asd = df[df[GROUP_COL] == "autistic"].copy()
    texts = load_texts(asd, TEXT_COL)
    corpus = build_corpus(texts, LANG)

    results: dict = {}

    # (B1) continuous: age / timing of diagnosis
    if TIME_OF_DX_COL in asd.columns and asd[TIME_OF_DX_COL].notna().any():
        y = asd[TIME_OF_DX_COL].to_numpy(dtype=float)
        for name, spec in CONSTRUCTS_WITHIN_AUTISTIC.items():
            lexicon = spec[LANG]
            check_lexicon(corpus, y, lexicon, var_type="continuous")
            results[f"{name}_by_time_of_dx"] = run_gradient(
                emb, corpus, y, lexicon, f"{name}_by_time_of_dx", OUTDIR
            )

    # (B2) categorical: diagnosis subtype (needs >=2 subtypes, >=20 docs each)
    if DIAGNOSIS_COL in asd.columns and asd[DIAGNOSIS_COL].nunique() > 1:
        y_cat = asd[DIAGNOSIS_COL].tolist()
        for name, spec in CONSTRUCTS_WITHIN_AUTISTIC.items():
            lexicon = spec[LANG]
            ssd = SSD(emb, corpus, y=y_cat, lexicon=lexicon)
            result = ssd.fit_groups(
                n_perm=N_PERM, correction=WITHIN_TEST_CORRECTION, random_state=RANDOM_STATE
            )
            result.report().save(OUTDIR / f"{name}_by_diagnosis_subtype_report.md")
            results[f"{name}_by_diagnosis_subtype"] = result

    return results


# ----------------------------------------------------------------------------
# 6. Main
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    df = load_metadata(METADATA_PATH)

    smallest_group = df[GROUP_COL].value_counts().min()
    if smallest_group < 20:
        raise ValueError(
            f"Smallest group has only {smallest_group} documents; fit_groups() "
            "drops groups under 20. If these are whole books, switch "
            "UNIT_OF_ANALYSIS to 'chapter' and re-build METADATA_PATH with "
            "one row per chapter."
        )

    emb = build_embeddings(EMBEDDINGS_PATH)

    part_a_summary = run_part_a(df, emb)
    part_b_results = run_part_b(df, emb)

    print("\nDone. Reports and CSVs written to:", OUTDIR.resolve())
