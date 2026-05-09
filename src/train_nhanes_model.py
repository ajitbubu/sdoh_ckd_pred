"""
src/train_nhanes_model.py
-------------------------
Stage 2 of the JMIR PHS two-stage CKD pipeline.

Builds the NHANES analytic cohort and trains a survey-weighted XGBoost
classifier for CKD presence using ONLY non-kidney predictors. The outcome
(KDIGO 2024 CKD label) is computed from kidney biomarkers (eGFR, UACR) but
those biomarkers are NOT among the model features.

Cohort per manuscript v3 (lines 23-25):
  • NHANES 2017-Mar 2020 pre-pandemic combined cycle (P_*) + 2021-Aug 2023 (L_).
  • Adults aged ≥18 with at least one of serum creatinine (LBXSCR) or
    urine albumin/creatinine (URXUMA, URXUCR).
  • Survey weights: WTMECPRP for P_; WTMEC2YR for L_ (each divided by 2 for
    combined-cycle weighting, per CDC guidance).
  • Target n = 15,150; target survey-weighted CKD prevalence = 13.93%.

Outcome (KDIGO 2024):
  ckd = 1 if (eGFR < 60 mL/min/1.73 m² by CKD-EPI 2021 race-free) OR
            (UACR ≥ 30 mg/g)

Predictors (deliberately exclude kidney biomarkers):
  age, sex, race/ethnicity (RIDRETH3), family income-to-poverty ratio,
  body mass index, mean systolic and diastolic oscillometric BP,
  self-reported HTN (BPQ020), DM (DIQ010), HF (MCQ160B), stroke (MCQ160F).

Outputs:
  data/processed/nhanes_phs_cohort.parquet
  models/stage2_xgb.json
  outputs/stage2_oof_predictions.csv
  outputs/stage2_metrics.json
  outputs/stage2_calibration_deciles.csv
  outputs/stage2_subgroup_auroc.csv
  outputs/stage2_decision_curve.csv
  outputs/stage2_confusion_at_op.csv
"""

import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (roc_auc_score, average_precision_score,
                              brier_score_loss, roc_curve, precision_recall_curve,
                              confusion_matrix)

# Repository paths (relative to project root)
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW       = os.path.join(BASE_DIR, "ckd_pipeline", "data", "raw", "nhanes")
PROC      = os.path.join(BASE_DIR, "ckd_pipeline", "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "ckd_pipeline", "models")
OUT       = os.path.join(BASE_DIR, "ckd_pipeline", "outputs")
for d in [PROC, MODEL_DIR, OUT]:
    os.makedirs(d, exist_ok=True)

SEED = 42
np.random.seed(SEED)


# ── CKD-EPI 2021 race-free eGFR ───────────────────────────────────────────
def egfr_ckdepi_2021(scr, age, sex):
    """sex: 1=Male, 2=Female (NHANES RIAGENDR)."""
    scr = np.asarray(scr, dtype=float)
    age = np.asarray(age, dtype=float)
    is_female = (np.asarray(sex) == 2)
    kappa = np.where(is_female, 0.7, 0.9)
    alpha = np.where(is_female, -0.241, -0.302)
    sex_factor = np.where(is_female, 1.012, 1.0)
    ratio = scr / kappa
    return (142.0
            * np.minimum(ratio, 1.0) ** alpha
            * np.maximum(ratio, 1.0) ** (-1.200)
            * 0.9938 ** age
            * sex_factor)


def compute_uacr(urxuma_mg_per_l, urxucr_mg_per_dl):
    a = np.asarray(urxuma_mg_per_l, dtype=float)
    c = np.asarray(urxucr_mg_per_dl, dtype=float)
    return np.where(c > 0, a * 100.0 / c, np.nan)


# ── Load one NHANES cycle (P_ or L_) ──────────────────────────────────────
def load_cycle(cycle_dir, suffix_kind):
    """suffix_kind: 'P' for P_*.xpt or 'L' for *_L.xpt"""
    def fn(stem):
        if suffix_kind == "P":
            return os.path.join(cycle_dir, f"P_{stem}.xpt")
        else:
            return os.path.join(cycle_dir, f"{stem}_L.xpt")

    def safe(path):
        if not os.path.exists(path):
            return pd.DataFrame()
        try:
            return pd.read_sas(path, format="xport")
        except Exception:
            return pd.DataFrame()

    demo  = safe(fn("DEMO"))
    bio   = safe(fn("BIOPRO"))
    alb   = safe(fn("ALB_CR"))
    bmx   = safe(fn("BMX"))
    bpxo  = safe(fn("BPXO"))
    diq   = safe(fn("DIQ"))
    bpq   = safe(fn("BPQ"))
    mcq   = safe(fn("MCQ"))
    inq   = safe(fn("INQ"))

    if len(demo) == 0:
        return pd.DataFrame()

    # Demographics + survey weight
    weight_col = "WTMECPRP" if suffix_kind == "P" else "WTMEC2YR"
    pir_col = "INDFMPIR" if "INDFMPIR" in demo.columns else None
    keep = ["SEQN", "RIDAGEYR", "RIAGENDR", "RIDRETH3"]
    if weight_col in demo.columns:
        keep.append(weight_col)
    if pir_col and pir_col in demo.columns:
        keep.append(pir_col)
    df = demo[keep].copy()
    df = df.rename(columns={
        "RIDAGEYR": "age", "RIAGENDR": "sex",
        "RIDRETH3": "race_eth", weight_col: "mec_weight",
    })
    if pir_col and pir_col in df.columns:
        df = df.rename(columns={pir_col: "pir"})
    else:
        df["pir"] = np.nan
    df["SEQN"] = df["SEQN"].astype(int)
    if "mec_weight" not in df.columns:
        df["mec_weight"] = np.nan

    # Lab features (used to compute outcome only)
    if len(bio) and "LBXSCR" in bio.columns:
        bio2 = bio[["SEQN", "LBXSCR"]].copy()
        bio2["SEQN"] = bio2["SEQN"].astype(int)
        df = df.merge(bio2.rename(columns={"LBXSCR": "scr"}), on="SEQN", how="left")
    else:
        df["scr"] = np.nan

    if len(alb) and {"URXUMA", "URXUCR"}.issubset(alb.columns):
        alb2 = alb[["SEQN", "URXUMA", "URXUCR"]].copy()
        alb2["SEQN"] = alb2["SEQN"].astype(int)
        alb2["uacr"] = compute_uacr(alb2["URXUMA"], alb2["URXUCR"])
        df = df.merge(alb2[["SEQN", "uacr"]], on="SEQN", how="left")
    else:
        df["uacr"] = np.nan

    # BMI
    if len(bmx) and "BMXBMI" in bmx.columns:
        bmx2 = bmx[["SEQN", "BMXBMI"]].copy()
        bmx2["SEQN"] = bmx2["SEQN"].astype(int)
        df = df.merge(bmx2.rename(columns={"BMXBMI": "bmi"}), on="SEQN", how="left")
    else:
        df["bmi"] = np.nan

    # Oscillometric BP — average of up to 3 readings
    if len(bpxo):
        sbp_cols = [c for c in bpxo.columns if c.startswith("BPXOSY")]
        dbp_cols = [c for c in bpxo.columns if c.startswith("BPXODI")]
        if sbp_cols and dbp_cols:
            bp = bpxo[["SEQN"] + sbp_cols + dbp_cols].copy()
            bp["SEQN"] = bp["SEQN"].astype(int)
            bp[sbp_cols + dbp_cols] = bp[sbp_cols + dbp_cols].replace(0, np.nan)
            bp["sbp"] = bp[sbp_cols].mean(axis=1)
            bp["dbp"] = bp[dbp_cols].mean(axis=1)
            df = df.merge(bp[["SEQN", "sbp", "dbp"]], on="SEQN", how="left")
        else:
            df["sbp"] = np.nan; df["dbp"] = np.nan
    else:
        df["sbp"] = np.nan; df["dbp"] = np.nan

    # Self-reported comorbidities — coded as 1=yes, 2=no, 7/9=missing in NHANES
    def map_yesno(series):
        return series.map(lambda v: 1.0 if v == 1 else (0.0 if v == 2 else np.nan))

    for src_df, src_col, dest_col in [
        (bpq, "BPQ020",  "htn_self"),
        (diq, "DIQ010",  "dm_self"),
        (mcq, "MCQ160B", "hf_self"),
        (mcq, "MCQ160F", "stroke_self"),
    ]:
        if len(src_df) and src_col in src_df.columns:
            tmp = src_df[["SEQN", src_col]].copy()
            tmp["SEQN"] = tmp["SEQN"].astype(int)
            tmp[dest_col] = map_yesno(tmp[src_col])
            df = df.merge(tmp[["SEQN", dest_col]], on="SEQN", how="left")
        else:
            df[dest_col] = np.nan

    return df


# ── Build the analytic cohort (n=15,150 target) ──────────────────────────
def build_cohort():
    print("\n  Loading P_ cycle (2017-Mar 2020)...")
    p_df = load_cycle(os.path.join(RAW, "P_2017-2020"), "P")
    print(f"    P_ DEMO rows: {len(p_df):,}")
    p_df["cycle"] = "P_2017-2020"
    p_df["mec_weight"] = p_df["mec_weight"] / 2.0  # combined-cycle weighting

    print("\n  Loading L_ cycle (2021-Aug 2023)...")
    l_df = load_cycle(os.path.join(RAW, "L_2021-2022"), "L")
    print(f"    L_ DEMO rows: {len(l_df):,}")
    l_df["cycle"] = "L_2021-2023"
    l_df["mec_weight"] = l_df["mec_weight"] / 2.0  # combined-cycle weighting

    df = pd.concat([p_df, l_df], ignore_index=True)
    print(f"\n  Combined: {len(df):,} participants")

    # Adults ≥18
    df = df[df["age"] >= 18]
    print(f"  After age ≥ 18:                          {len(df):,}")

    # Has at least one of creatinine or UACR
    has_kidney_data = df["scr"].notna() | df["uacr"].notna()
    df = df[has_kidney_data].copy()
    print(f"  After has serum creatinine OR UACR:      {len(df):,}")

    # Drop rows with no MEC weight (those weren't in MEC sample)
    df = df[df["mec_weight"].notna() & (df["mec_weight"] > 0)]
    print(f"  After valid MEC weight:                  {len(df):,}")

    # Compute eGFR (only where SCR present)
    df["egfr"] = np.where(
        df["scr"].notna(),
        egfr_ckdepi_2021(df["scr"].fillna(0), df["age"], df["sex"]),
        np.nan
    )

    # KDIGO CKD label
    egfr_low = (df["egfr"] < 60)
    uacr_high = (df["uacr"] >= 30)
    df["ckd"] = (egfr_low.fillna(False) | uacr_high.fillna(False)).astype(int)

    # Survey-weighted prevalence
    w = df["mec_weight"]
    weighted_prev = (df["ckd"] * w).sum() / w.sum() * 100
    unweighted_prev = df["ckd"].mean() * 100
    print(f"\n  Final analytic cohort N:                 {len(df):,}")
    print(f"  Unweighted CKD prevalence:               {unweighted_prev:.2f}%")
    print(f"  Survey-weighted CKD prevalence:          {weighted_prev:.2f}%")
    print(f"  (Manuscript target: N=15,150, weighted prev 13.93%)")

    return df.reset_index(drop=True)


# ── Survey-weighted metrics ───────────────────────────────────────────────
def weighted_auroc(y, p, w):
    return roc_auc_score(y, p, sample_weight=w)


def weighted_auprc(y, p, w):
    return average_precision_score(y, p, sample_weight=w)


def weighted_brier(y, p, w):
    w = np.asarray(w)
    return float(np.sum(w * (np.asarray(p) - np.asarray(y)) ** 2) / np.sum(w))


def calibration_deciles(y, p, w, n_bins=10):
    w = np.asarray(w)
    y = np.asarray(y)
    p = np.asarray(p)
    # Quantile-binned deciles using sample weights
    sort_idx = np.argsort(p)
    cum_w = np.cumsum(w[sort_idx])
    total_w = cum_w[-1]
    bin_edges = [p[sort_idx][np.searchsorted(cum_w, total_w * q / n_bins)]
                  for q in range(1, n_bins + 1)]
    bin_edges = sorted(set([p.min() - 1e-9] + bin_edges + [p.max() + 1e-9]))
    bins = np.digitize(p, bin_edges) - 1
    rows = []
    for b in range(len(bin_edges) - 1):
        mask = (bins == b)
        if mask.sum() == 0:
            continue
        mean_pred = float(np.sum(w[mask] * p[mask]) / np.sum(w[mask]))
        obs = float(np.sum(w[mask] * y[mask]) / np.sum(w[mask]))
        rows.append({"decile": b + 1, "n": int(mask.sum()),
                     "mean_predicted": round(mean_pred, 4),
                     "observed": round(obs, 4)})
    cal_df = pd.DataFrame(rows)
    # Slope/intercept from weighted regression of obs on mean_pred
    from scipy import stats
    slope, intercept, _, _, _ = stats.linregress(
        cal_df["mean_predicted"], cal_df["observed"])
    return cal_df, float(slope), float(intercept)


def sensitivity_at_specificity(y, p, w, target_spec=0.90):
    """Find threshold yielding target survey-weighted specificity, return sens."""
    fpr, tpr, thr = roc_curve(y, p, sample_weight=w)
    spec = 1 - fpr
    # Find threshold where spec is closest to target, achieved (>= target)
    valid = spec >= target_spec
    if not valid.any():
        return None, None, None
    idx = np.where(valid)[0][np.argmax(tpr[valid])]
    return float(tpr[idx]), float(spec[idx]), float(thr[idx])


def decision_curve(y, p, w, thresholds):
    """Vickers (2006) net benefit at each threshold (survey-weighted)."""
    w = np.asarray(w, dtype=float)
    y = np.asarray(y)
    p = np.asarray(p)
    total_w = w.sum()
    prev = float((y * w).sum() / total_w)
    rows = []
    for pt in thresholds:
        # Treat-all
        nb_all = prev - (1 - prev) * (pt / (1 - pt))
        # Treat-none
        nb_none = 0.0
        # Model
        flagged = (p >= pt)
        tp_w = float(np.sum(w[flagged & (y == 1)])) / total_w
        fp_w = float(np.sum(w[flagged & (y == 0)])) / total_w
        nb_model = tp_w - fp_w * (pt / (1 - pt))
        rows.append({"threshold": pt, "model_nb": nb_model,
                     "all_nb": nb_all, "none_nb": nb_none})
    return pd.DataFrame(rows)


def subgroup_auroc(df, p_col="oof_prob", y_col="ckd", w_col="mec_weight"):
    """Subgroup AUROC by age band, sex, race/ethnicity (NHANES RIDRETH3)."""
    rows = []
    # Age bands
    for label, mask in [
        ("Age <50",   df["age"] < 50),
        ("Age 50-64", (df["age"] >= 50) & (df["age"] < 65)),
        ("Age ≥65",   df["age"] >= 65),
        ("Female",    df["sex"] == 2),
        ("Male",      df["sex"] == 1),
    ]:
        rows.append(_sg(df, mask, label, p_col, y_col, w_col))
    # Race/ethnicity (RIDRETH3 codes)
    race_map = {1: "Mexican American", 2: "Other Hispanic", 3: "NH White",
                4: "NH Black", 6: "NH Asian", 7: "Other/Multi"}
    for code, label in race_map.items():
        rows.append(_sg(df, df["race_eth"] == code, label, p_col, y_col, w_col))
    return pd.DataFrame([r for r in rows if r is not None])


def _sg(df, mask, label, p_col, y_col, w_col):
    sub = df[mask]
    if len(sub) < 50 or sub[y_col].nunique() < 2:
        return {"subgroup": label, "n": int(len(sub)), "auroc": None}
    return {"subgroup": label, "n": int(len(sub)),
            "auroc": round(weighted_auroc(sub[y_col], sub[p_col], sub[w_col]), 4)}


# ── Train + evaluate ─────────────────────────────────────────────────────
FEATURES = ["age", "sex", "race_eth", "pir", "bmi", "sbp", "dbp",
            "htn_self", "dm_self", "hf_self", "stroke_self"]


def train_evaluate(df):
    X = df[FEATURES].values
    y = df["ckd"].values
    w = df["mec_weight"].values

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof_probs = np.zeros(len(y))
    fold_aurocs = []

    for k, (tr, va) in enumerate(skf.split(X, y), 1):
        model = xgb.XGBClassifier(
            n_estimators=500, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9,
            eval_metric="logloss", random_state=SEED, n_jobs=-1,
        )
        model.fit(X[tr], y[tr], sample_weight=w[tr])
        p = model.predict_proba(X[va])[:, 1]
        oof_probs[va] = p
        fold_auc = weighted_auroc(y[va], p, w[va])
        fold_aurocs.append(fold_auc)
        print(f"    Fold {k}: AUROC={fold_auc:.4f}")

    df["oof_prob"] = oof_probs

    # Survey-weighted overall metrics
    auroc = weighted_auroc(y, oof_probs, w)
    auprc = weighted_auprc(y, oof_probs, w)
    brier = weighted_brier(y, oof_probs, w)
    cal_df, cal_slope, cal_intercept = calibration_deciles(y, oof_probs, w)
    sens, spec, thr = sensitivity_at_specificity(y, oof_probs, w, 0.90)
    dc = decision_curve(y, oof_probs, w,
                         thresholds=np.arange(0.05, 0.41, 0.01))
    sg = subgroup_auroc(df)

    metrics = {
        "n": int(len(df)),
        "events": int(y.sum()),
        "weighted_prevalence_pct": round(float((y * w).sum() / w.sum() * 100), 2),
        "auroc": round(float(auroc), 4),
        "auroc_per_fold_min": round(float(min(fold_aurocs)), 4),
        "auroc_per_fold_max": round(float(max(fold_aurocs)), 4),
        "auprc": round(float(auprc), 4),
        "brier": round(float(brier), 4),
        "calibration_slope": round(cal_slope, 4),
        "calibration_intercept": round(cal_intercept, 4),
        "operating_threshold_for_90pct_spec": round(thr, 4),
        "sensitivity_at_90pct_spec": round(sens, 4),
        "fold_aurocs": [round(a, 4) for a in fold_aurocs],
    }

    # Train final model on full data for SHAP / serialization
    final_model = xgb.XGBClassifier(
        n_estimators=500, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9,
        eval_metric="logloss", random_state=SEED, n_jobs=-1,
    )
    final_model.fit(X, y, sample_weight=w)

    return df, metrics, cal_df, sg, dc, final_model


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("Stage 2: NHANES patient-level CKD classifier")
    print("=" * 64)

    # 1. Build cohort
    df = build_cohort()

    # 2. Train + evaluate
    print("\n  5-fold stratified CV (NHANES MEC weights):")
    df, metrics, cal_df, sg_df, dc_df, model = train_evaluate(df)

    # 3. Save outputs
    cohort_path = os.path.join(PROC, "nhanes_phs_cohort.parquet")
    try:
        df.to_parquet(cohort_path, index=False)
    except Exception:
        cohort_path = cohort_path.replace(".parquet", ".csv")
        df.to_csv(cohort_path, index=False)
    print(f"\n  Saved cohort → {cohort_path}")

    model.save_model(os.path.join(MODEL_DIR, "stage2_xgb.json"))
    df[["SEQN", "cycle", "mec_weight", "age", "sex", "race_eth",
        "ckd", "oof_prob"]].to_csv(
        os.path.join(OUT, "stage2_oof_predictions.csv"), index=False)

    with open(os.path.join(OUT, "stage2_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    cal_df.to_csv(os.path.join(OUT, "stage2_calibration_deciles.csv"), index=False)
    sg_df.to_csv(os.path.join(OUT, "stage2_subgroup_auroc.csv"), index=False)
    dc_df.to_csv(os.path.join(OUT, "stage2_decision_curve.csv"), index=False)

    # Confusion matrix at the 90% specificity operating point
    op_thr = metrics["operating_threshold_for_90pct_spec"]
    pred = (df["oof_prob"] >= op_thr).astype(int)
    cm = confusion_matrix(df["ckd"], pred, labels=[0, 1])
    cm_df = pd.DataFrame(
        cm, index=["Actual: no CKD", "Actual: CKD"],
        columns=["Pred: no CKD", "Pred: CKD"],
    )
    cm_df.to_csv(os.path.join(OUT, "stage2_confusion_at_op.csv"))

    print("\n" + "=" * 64)
    print("Stage 2 metrics summary:")
    for k, v in metrics.items():
        print(f"  {k:<40s}  {v}")
    print("=" * 64)
