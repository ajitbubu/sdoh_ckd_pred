"""
step4_external_validation.py
----------------------------
Two external-data checks on the NHANES analytic cohort and the trained model.

1. Cohort distributional validation against USRDS 2024 Annual Data Report
   Table B.8 (NHANES-derived CKD prevalence). Same NHANES source as our
   training data, so the demographic distributions should match closely.
   This is a sanity check on cohort assembly correctness.

2. Sensitivity application of the trained NHANES mortality model to the UCI
   CKD dataset (Rubini et al. 2015, N=400, Indian hospital). UCI's outcome
   is prevalent-CKD classification (ckd vs. notckd), not mortality, so the
   transfer is loose — we report whether our predicted-high-risk UCI patients
   are enriched for the UCI 'ckd' label.

Inputs:
  data/processed/nhanes_cohort.csv               (from step2)
  models/nhanes_xgb_full.json                    (from step3)
  ../real_world_ckd_data/uci_ckd_dataset.csv
  ../real_world_ckd_data/usrds_2024_reference_tables/usrds_2024_CKD_Prevalence_B.8.csv

Outputs:
  outputs/cohort_vs_usrds_b8.csv                 — distributional comparison table
  outputs/uci_sensitivity.csv                    — UCI risk-score by class
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

EXTERNAL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "real_world_ckd_data"))


# ── (1) USRDS Table B.8 cohort comparison ─────────────────────────────────
def cohort_vs_usrds():
    """
    Compare the NHANES analytic cohort age/sex/race distribution to USRDS 2024
    Table B.8, which itself is NHANES-derived CKD prevalence weighted to the
    US adult population. The 2005-2014 columns of Table B.8 are most relevant.
    """
    cohort_path = os.path.join(PROC_DIR, "nhanes_cohort.csv")
    if not os.path.exists(cohort_path):
        print(f"  [SKIP] {cohort_path} missing — run step2 first.")
        return None
    df = pd.read_csv(cohort_path)
    primary = df[df["cycle"].isin([
        "2005-2006", "2007-2008", "2009-2010", "2011-2012", "2013-2014"
    ])]

    # Our cohort distributions
    age_buckets = pd.cut(
        primary["age"],
        bins=[19, 44, 54, 64, 74, 999],
        labels=["20-44", "45-54", "55-64", "65-74", "75+"],
    )
    age_pct = age_buckets.value_counts(normalize=True).sort_index() * 100

    sex_pct = primary["sex"].value_counts(normalize=True) * 100
    sex_female = sex_pct.get(2.0, 0.0)
    sex_male = sex_pct.get(1.0, 0.0)

    # NHANES race recoding
    # Our cohort uses RIDRETH3 in 2011+ (codes 1,2,3,4,6,7) and RIDRETH1 in
    # 2005-2010 (codes 1,2,3,4,5). For the comparison, map to USRDS B.8 groups:
    #   White, Black, Hispanic, Other.
    def usrds_race(r):
        if r in (3,):       return "White"     # NH White
        if r in (4,):       return "Black"     # NH Black
        if r in (1, 2):     return "Hispanic"  # Mexican Am + Other Hispanic
        return "Other"
    race_groups = primary["race_eth"].map(usrds_race)
    race_pct = race_groups.value_counts(normalize=True) * 100

    # USRDS 2024 Table B.8 — CKD prevalence among NHANES adults
    # Columns are 2017-Mar 2020, 2013-2016, 2009-2012, 2005-2008. We average
    # 2005-2008 and 2013-2016 since our primary cohort spans 2005-2014.
    usrds = {
        "Age 20-44":   (23.95 + 21.55) / 2,
        "Age 45-54":   (13.55 + 12.81) / 2,
        "Age 55-64":   (14.54 + 18.08) / 2,
        "Age 65-74":   (18.09 + 22.00) / 2,
        "Age 75+":     (29.86 + 25.56) / 2,
        "Sex Female":  (59.64 + 58.32) / 2,
        "Sex Male":    (40.36 + 41.68) / 2,
        "Race White":      (68.39 + 66.53) / 2,
        "Race Black":      (15.29 + 14.04) / 2,
        "Race Hispanic":   (11.64 + 12.28) / 2,
        "Race Other":      (4.68 +  7.15) / 2,
    }

    rows = []
    for k, label in [
        ("Age 20-44",  "20-44"), ("Age 45-54", "45-54"),
        ("Age 55-64",  "55-64"), ("Age 65-74", "65-74"),
        ("Age 75+",    "75+"),
    ]:
        ours = float(age_pct.get(label, 0.0))
        rows.append({"Stratum": k, "Our cohort %": round(ours, 1),
                     "USRDS B.8 %": round(usrds[k], 1),
                     "Diff (pp)": round(ours - usrds[k], 1)})
    rows.append({"Stratum": "Sex Female",
                 "Our cohort %": round(sex_female, 1),
                 "USRDS B.8 %": round(usrds["Sex Female"], 1),
                 "Diff (pp)": round(sex_female - usrds["Sex Female"], 1)})
    rows.append({"Stratum": "Sex Male",
                 "Our cohort %": round(sex_male, 1),
                 "USRDS B.8 %": round(usrds["Sex Male"], 1),
                 "Diff (pp)": round(sex_male - usrds["Sex Male"], 1)})
    for k, label in [
        ("Race White",    "White"),    ("Race Black",    "Black"),
        ("Race Hispanic", "Hispanic"), ("Race Other",    "Other"),
    ]:
        ours = float(race_pct.get(label, 0.0))
        rows.append({"Stratum": k, "Our cohort %": round(ours, 1),
                     "USRDS B.8 %": round(usrds[k], 1),
                     "Diff (pp)": round(ours - usrds[k], 1)})

    out = pd.DataFrame(rows)
    return out


# ── (2) UCI CKD sensitivity application ───────────────────────────────────
def uci_sensitivity():
    """
    Apply the trained NHANES mortality model to the UCI CKD dataset.
    Caveat: UCI's outcome is 'ckd' vs 'notckd' (a prevalent-CKD classification),
    not mortality. We report whether NHANES-predicted-high-risk UCI patients
    are enriched for the 'ckd' label as a loose cross-cohort consistency check.
    """
    uci_path = os.path.join(EXTERNAL_DIR, "uci_ckd_dataset.csv")
    if not os.path.exists(uci_path):
        print(f"  [SKIP] UCI dataset missing at {uci_path}")
        return None

    uci = pd.read_csv(uci_path, engine="python", on_bad_lines="skip",
                       na_values=["?", "\t?", "?\t"])

    # Drop rows with missing class label
    uci = uci.dropna(subset=["class"])

    # Map UCI → NHANES feature names (best effort; many features have no
    # equivalent. Missing inputs are left as NaN; XGBoost handles them.)
    # CKD-EPI 2021 race-free eGFR from serum creatinine, age, sex.
    # UCI doesn't record sex; we test both Male and Female assumptions and
    # take the average to get a sex-agnostic estimate.
    uci["age"] = uci["age"].astype(float)
    uci["scr"] = uci["sc"].astype(float)

    def egfr(scr, age, female):
        kappa = 0.7 if female else 0.9
        alpha = -0.241 if female else -0.302
        sex_factor = 1.012 if female else 1.0
        ratio = scr / kappa
        return (142.0
                * min(ratio, 1.0)**alpha
                * max(ratio, 1.0)**(-1.200)
                * 0.9938**age * sex_factor)

    def egfr_avg(row):
        if pd.isna(row["scr"]) or pd.isna(row["age"]):
            return np.nan
        return (egfr(row["scr"], row["age"], True) +
                egfr(row["scr"], row["age"], False)) / 2

    uci["egfr"] = uci.apply(egfr_avg, axis=1)
    uci["sex_male"] = 0.5  # unknown — model will average
    uci["log_uacr"] = np.nan  # UCI has no UACR
    uci["hba1c"] = np.nan      # UCI has no HbA1c
    uci["sbp"] = uci["bp"].astype(float)  # UCI has only one BP reading
    uci["dbp"] = np.nan
    uci["bmi"] = np.nan

    uci["diabetes"] = (uci["dm"].astype(str).str.strip() == "yes").astype(int)
    uci["hypertension"] = (uci["htn"].astype(str).str.strip() == "yes").astype(int)
    uci["chf"] = 0
    uci["stroke"] = 0
    uci["cancer"] = 0
    uci["ckd_stage_3a"] = ((uci["egfr"] >= 45) & (uci["egfr"] < 60)).fillna(False).astype(int)
    uci["ckd_stage_3b"] = ((uci["egfr"] >= 30) & (uci["egfr"] < 45)).fillna(False).astype(int)

    # UCI has no SDOH features
    for sdoh_col in ["education", "pir", "food_security_score",
                      "insurance_any", "insurance_medicare", "insurance_medicaid",
                      "employed", "home_owned"]:
        uci[sdoh_col] = np.nan

    # Load model
    model_path = os.path.join(MODEL_DIR, "nhanes_xgb_full.json")
    if not os.path.exists(model_path):
        print(f"  [SKIP] trained model missing at {model_path}")
        return None
    booster = xgb.Booster()
    booster.load_model(model_path)

    # Reconstruct feature order from saved feature list
    import joblib
    features_path = os.path.join(MODEL_DIR, "feature_list_full.pkl")
    features = joblib.load(features_path)

    X = uci[features].values
    dmat = xgb.DMatrix(X, feature_names=features)
    probs = booster.predict(dmat)

    uci["risk_score"] = probs
    uci["uci_class"] = (uci["class"].str.strip() == "ckd").astype(int)

    # Risk score by UCI class
    by_class = uci.groupby("class")["risk_score"].agg(
        ["mean", "median", "std", "count"]
    ).round(3)

    # Top decile risk vs class
    threshold = uci["risk_score"].quantile(0.5)
    uci["high_risk"] = (uci["risk_score"] >= threshold).astype(int)
    cross = pd.crosstab(uci["high_risk"], uci["class"])

    return by_class, cross, uci


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("SDOH-CKDPred — Step 4: External Validation Checks")
    print("=" * 64)

    # (1) USRDS Table B.8
    print("\n[1] Cohort vs USRDS 2024 Table B.8 (NHANES-derived CKD prevalence)")
    cmp_df = cohort_vs_usrds()
    if cmp_df is not None:
        print(cmp_df.to_string(index=False))
        out_path = os.path.join(OUTPUT_DIR, "cohort_vs_usrds_b8.csv")
        cmp_df.to_csv(out_path, index=False)
        print(f"  Saved → {out_path}")
        max_diff = cmp_df["Diff (pp)"].abs().max()
        print(f"\n  Maximum stratum deviation: {max_diff:.1f} percentage points")
        if max_diff < 10:
            print("  → Cohort distributions are consistent with USRDS 2024 published estimates.")

    # (2) UCI sensitivity
    print("\n[2] UCI CKD dataset — model risk score by 'ckd'/'notckd' class")
    result = uci_sensitivity()
    if result is not None:
        by_class, cross, uci_full = result
        print("\n  Risk score by UCI class:")
        print(by_class)
        print(f"\n  Top-50% NHANES risk vs UCI class:")
        print(cross)
        out_path = os.path.join(OUTPUT_DIR, "uci_sensitivity.csv")
        uci_full[["age", "scr", "egfr", "diabetes", "hypertension",
                   "risk_score", "class"]].to_csv(out_path, index=False)
        print(f"  Saved → {out_path}")

        # Quick effect-size check
        ckd_mean = by_class.loc["ckd", "mean"]
        notckd_mean = by_class.loc["notckd", "mean"]
        print(f"\n  Mean risk score: ckd={ckd_mean:.3f}, notckd={notckd_mean:.3f}, "
              f"delta={ckd_mean - notckd_mean:+.3f}")

    print("\n" + "=" * 64)
    print("Step 4 complete.")
    print("=" * 64)
