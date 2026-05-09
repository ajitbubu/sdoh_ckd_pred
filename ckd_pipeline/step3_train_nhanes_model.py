"""
step3_train_nhanes_model.py
---------------------------
Trains the SDOH-augmented mortality risk model on the NHANES analytic cohort
produced by step2_assemble_nhanes_cohort.py.

Primary analytic cohort: cycles 2005-2014 (5 cycles, suffix D-H), where every
participant has either ≥60 months of follow-up or has died, so the 5-year
mortality endpoint is observable without right-censoring bias.

Cycles 2015-2018 are reserved for a sensitivity check at a 3-year horizon.

Model comparison:
  • Logistic Regression — clinical-only baseline
  • Random Forest
  • LightGBM
  • XGBoost (primary, with native NaN handling — no imputation)

Race/ethnicity is used as a stratification variable for equity analysis but
is NOT included as a model predictor, consistent with CKD-EPI 2021 race-free
methodology and KDIGO 2024 recommendations (Eneanya et al. 2019 ref [15]).

NHANES survey weights are not applied because the modeling objective is
individual-level risk prediction rather than population-level inference; this
is documented in Methods → Limitations.

Outputs:
  models/nhanes_xgb_full.json
  models/nhanes_xgb_clinical.json
  outputs/nhanes_cv_results_full.csv
  outputs/nhanes_cv_results_clinical.csv
  outputs/nhanes_shap_importance.csv
  outputs/nhanes_equity_analysis.csv
  outputs/nhanes_model_comparison.csv
  outputs/nhanes_calibration.csv
  outputs/nhanes_summary.txt
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import (roc_auc_score, average_precision_score,
                              brier_score_loss, confusion_matrix,
                              f1_score, precision_score, recall_score)
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except (ImportError, OSError):
    HAS_LGBM = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROC_DIR    = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR   = os.path.join(BASE_DIR, "models")
OUTPUT_DIR  = os.path.join(BASE_DIR, "outputs")
for d in [MODEL_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

SEED = 42
np.random.seed(SEED)


# ── Feature lists ─────────────────────────────────────────────────────────
# CKD-EPI 2021 inputs (age, sex) are kept; race is intentionally excluded.
CLINICAL_FEATURES = [
    "age", "sex_male",
    "egfr", "log_uacr", "hba1c", "sbp", "dbp", "bmi",
    "diabetes", "hypertension", "chf", "stroke", "cancer",
    "ckd_stage_3a", "ckd_stage_3b",
]

# Individual-level SDOH from NHANES questionnaires.
# Addresses ecological-bias critique: every variable is measured at the
# individual level (questionnaire response), not aggregated to ZCTA.
SDOH_FEATURES = [
    "education",                  # DMDEDUC2: 1=<9th, 2=9-11th, 3=HS, 4=some college, 5=college+
    "pir",                         # INDFMPIR: poverty income ratio (0-5, capped)
    "food_security_score",         # FSDHH: 1=full, 2=marginal, 3=low, 4=very low
    "insurance_any", "insurance_medicare", "insurance_medicaid",
    "employed", "home_owned",
]

ALL_FEATURES = CLINICAL_FEATURES + SDOH_FEATURES
TARGET = "mort_5yr"


# ── Cohort filtering for primary analysis ─────────────────────────────────
def primary_cohort(df):
    """
    Restrict to cycles with adequate 5-year follow-up: 2005-2014 (D, E, F, G, H).
    Within this window, every participant either has ≥60 months of follow-up
    or has died, eliminating right-censoring bias for the 5y mortality endpoint.
    """
    primary_cycles = ["2005-2006", "2007-2008", "2009-2010",
                      "2011-2012", "2013-2014"]
    return df[df["cycle"].isin(primary_cycles)].copy()


def secondary_cohort_3yr(df):
    """
    Sensitivity cohort: cycles 2015-2018 with a 3-year mortality endpoint.
    Allows external-time validation on a different era of NHANES.
    """
    secondary_cycles = ["2015-2016", "2017-2018"]
    sub = df[df["cycle"].isin(secondary_cycles)].copy()
    # 3y mortality with explicit follow-up requirement
    sub["mort_3yr"] = (
        (sub["MORTSTAT"] == 1) & (sub["PERMTH_INT"] <= 36)
    ).astype(int)
    return sub


# ── Preprocessing ────────────────────────────────────────────────────────
def preprocess(df):
    """Encode categoricals, derive interaction-free engineered features."""
    d = df.copy()
    d["sex_male"] = (d["sex"] == 1).astype(int)
    d["log_uacr"] = np.log(d["uacr"].clip(lower=0.1) + 1)
    d["ckd_stage_3a"] = (d["ckd_stage"] == "Stage_3a").astype(int)
    d["ckd_stage_3b"] = (d["ckd_stage"] == "Stage_3b").astype(int)
    return d


def get_X_y(df, features, target=TARGET):
    return df[features].values, df[target].values


# ── Metrics ──────────────────────────────────────────────────────────────
def compute_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    return {
        "AUROC":       round(roc_auc_score(y_true, y_prob), 4),
        "AUPRC":       round(average_precision_score(y_true, y_prob), 4),
        "Brier":       round(brier_score_loss(y_true, y_prob), 4),
        "Sensitivity": round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0,
        "Specificity": round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0,
        "PPV":         round(precision_score(y_true, y_pred, zero_division=0), 4),
        "NPV":         round(tn / (tn + fn), 4) if (tn + fn) > 0 else 0,
        "F1":          round(f1_score(y_true, y_pred, zero_division=0), 4),
    }


def bootstrap_auroc_ci(y_true, y_prob, n_bootstrap=1000, ci=0.95):
    rng = np.random.RandomState(SEED)
    aurocs = []
    n = len(y_true)
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        aurocs.append(roc_auc_score(y_true[idx], y_prob[idx]))
    lower = np.percentile(aurocs, (1 - ci) / 2 * 100)
    upper = np.percentile(aurocs, (1 + ci) / 2 * 100)
    return round(lower, 3), round(upper, 3)


def delong_test(y_true, y_prob1, y_prob2):
    """DeLong's test for paired AUROC comparison on the same dataset."""
    from scipy import stats
    y_true = np.asarray(y_true)
    y_prob1 = np.asarray(y_prob1)
    y_prob2 = np.asarray(y_prob2)
    pos_idx = np.where(y_true == 1)[0]
    neg_idx = np.where(y_true == 0)[0]
    n1, n0 = len(pos_idx), len(neg_idx)
    if n1 == 0 or n0 == 0:
        return 0.0, 1.0

    def placement(yp):
        V10 = np.array([
            np.mean(yp[pos_idx[i]] > yp[neg_idx]) +
            0.5 * np.mean(yp[pos_idx[i]] == yp[neg_idx])
            for i in range(n1)
        ])
        V01 = np.array([
            np.mean(yp[pos_idx] > yp[neg_idx[j]]) +
            0.5 * np.mean(yp[pos_idx] == yp[neg_idx[j]])
            for j in range(n0)
        ])
        return V10, V01

    V10_1, V01_1 = placement(y_prob1)
    V10_2, V01_2 = placement(y_prob2)
    auc1 = roc_auc_score(y_true, y_prob1)
    auc2 = roc_auc_score(y_true, y_prob2)
    S10 = np.cov(V10_1, V10_2)
    S01 = np.cov(V01_1, V01_2)
    S = S10 / n1 + S01 / n0
    diff = auc1 - auc2
    var_diff = S[0, 0] + S[1, 1] - 2 * S[0, 1]
    if var_diff <= 0:
        return 0.0, 1.0
    z = diff / np.sqrt(var_diff)
    p = 2 * stats.norm.sf(abs(z))
    return round(z, 4), round(p, 4)


# ── Cross-validation with XGBoost (NaN-native) ───────────────────────────
def cv_xgb(df, features, label):
    print(f"\n  5-fold CV: {label}")
    X, y = get_X_y(df, features)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    fold_metrics = []
    oof = np.zeros(len(y))
    for k, (tr, va) in enumerate(skf.split(X, y), 1):
        pos_w = (y[tr] == 0).sum() / max((y[tr] == 1).sum(), 1)
        m = xgb.XGBClassifier(
            max_depth=6, learning_rate=0.05, n_estimators=400,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
            gamma=0.1, reg_alpha=0.1, reg_lambda=1.0,
            eval_metric="auc", random_state=SEED, n_jobs=-1,
            scale_pos_weight=pos_w,
        )
        m.fit(X[tr], y[tr], eval_set=[(X[va], y[va])], verbose=False)
        p = m.predict_proba(X[va])[:, 1]
        oof[va] = p
        fm = compute_metrics(y[va], p); fm["fold"] = k
        fold_metrics.append(fm)
        print(f"    Fold {k}: AUROC={fm['AUROC']:.4f}  Sens={fm['Sensitivity']:.3f}  Spec={fm['Specificity']:.3f}")
    overall = compute_metrics(y, oof)
    lo, hi = bootstrap_auroc_ci(y, oof)
    overall["AUROC_CI_lower"] = lo
    overall["AUROC_CI_upper"] = hi
    print(f"  OOF AUROC = {overall['AUROC']:.4f}  (95% CI {lo}-{hi})")
    return pd.DataFrame(fold_metrics), overall, oof


def cv_logreg(df, features, label):
    """Clinical-only LR baseline. Uses median imputation since LR can't handle NaN."""
    print(f"\n  5-fold CV: {label}")
    X, y = get_X_y(df, features)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    fold_metrics = []
    oof = np.zeros(len(y))
    for k, (tr, va) in enumerate(skf.split(X, y), 1):
        pipe = Pipeline([
            ("imp",  SimpleImputer(strategy="median")),
            ("scl",  StandardScaler()),
            ("lr",   LogisticRegression(max_iter=2000, C=0.1,
                                        random_state=SEED,
                                        class_weight="balanced")),
        ])
        pipe.fit(X[tr], y[tr])
        p = pipe.predict_proba(X[va])[:, 1]
        oof[va] = p
        fm = compute_metrics(y[va], p); fm["fold"] = k
        fold_metrics.append(fm)
        print(f"    Fold {k}: AUROC={fm['AUROC']:.4f}")
    overall = compute_metrics(y, oof)
    lo, hi = bootstrap_auroc_ci(y, oof)
    overall["AUROC_CI_lower"] = lo
    overall["AUROC_CI_upper"] = hi
    print(f"  OOF AUROC = {overall['AUROC']:.4f}  (95% CI {lo}-{hi})")
    return pd.DataFrame(fold_metrics), overall, oof


# ── Model comparison ─────────────────────────────────────────────────────
def compare_models(df, features):
    """Compare LR / RF / LightGBM / XGBoost via 80/20 split (informational)."""
    print("\n  Model comparison on 80/20 split (informational):")
    X, y = get_X_y(df, features)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )
    rows = []

    # LR (with imputation)
    lr_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scl", StandardScaler()),
        ("lr",  LogisticRegression(max_iter=2000, random_state=SEED,
                                   class_weight="balanced")),
    ])
    lr_pipe.fit(Xtr, ytr)
    lr_auc = roc_auc_score(yte, lr_pipe.predict_proba(Xte)[:, 1])
    rows.append({"model": "Logistic Regression", "AUROC": round(lr_auc, 3)})
    print(f"    LR       AUROC = {lr_auc:.3f}")

    # RF
    rf = RandomForestClassifier(n_estimators=500, max_depth=8,
                                random_state=SEED, n_jobs=-1,
                                class_weight="balanced")
    rf_pipe = Pipeline([("imp", SimpleImputer(strategy="median")), ("rf", rf)])
    rf_pipe.fit(Xtr, ytr)
    rf_auc = roc_auc_score(yte, rf_pipe.predict_proba(Xte)[:, 1])
    rows.append({"model": "Random Forest", "AUROC": round(rf_auc, 3)})
    print(f"    RF       AUROC = {rf_auc:.3f}")

    # LightGBM
    if HAS_LGBM:
        lgbm = LGBMClassifier(n_estimators=400, max_depth=6, learning_rate=0.05,
                               random_state=SEED, n_jobs=-1, verbose=-1,
                               is_unbalance=True)
        lgbm.fit(Xtr, ytr)
        lgbm_auc = roc_auc_score(yte, lgbm.predict_proba(Xte)[:, 1])
        rows.append({"model": "LightGBM", "AUROC": round(lgbm_auc, 3)})
        print(f"    LightGBM AUROC = {lgbm_auc:.3f}")

    # XGB
    pos_w = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
    xgbm = xgb.XGBClassifier(
        max_depth=6, learning_rate=0.05, n_estimators=400,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
        random_state=SEED, n_jobs=-1, scale_pos_weight=pos_w,
        eval_metric="auc",
    )
    xgbm.fit(Xtr, ytr)
    xgb_auc = roc_auc_score(yte, xgbm.predict_proba(Xte)[:, 1])
    rows.append({"model": "XGBoost", "AUROC": round(xgb_auc, 3)})
    print(f"    XGBoost  AUROC = {xgb_auc:.3f}")

    return pd.DataFrame(rows)


# ── Final model training on full primary cohort ──────────────────────────
def train_final_xgb(df, features):
    X, y = get_X_y(df, features)
    pos_w = (y == 0).sum() / max((y == 1).sum(), 1)
    m = xgb.XGBClassifier(
        max_depth=6, learning_rate=0.05, n_estimators=400,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
        gamma=0.1, reg_alpha=0.1, reg_lambda=1.0,
        eval_metric="auc", random_state=SEED, n_jobs=-1,
        scale_pos_weight=pos_w,
    )
    m.fit(X, y, verbose=False)
    return m


# ── SHAP analysis ────────────────────────────────────────────────────────
def shap_analysis(model, df, features):
    """
    Compute SHAP values via shap.TreeExplainer where possible. Falls back to
    XGBoost native feature importance if SHAP fails (e.g., serialization
    issue between xgboost ≥ 2.0 and older shap versions where base_score is
    written as '[5E-1]' instead of a scalar).
    """
    X, _ = get_X_y(df, features)
    sv = None
    if HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(X)
            if isinstance(sv, list):
                sv = sv[1] if len(sv) == 2 else sv[0]
        except (ValueError, AttributeError) as e:
            print(f"  [WARN] SHAP failed ({type(e).__name__}: {str(e)[:80]}); "
                   "falling back to XGBoost gain importance")
            sv = None
    if sv is None:
        # Fallback: XGBoost gain-based feature importance
        booster = model.get_booster()
        gain = booster.get_score(importance_type="gain")
        # Map fXX → feature name (XGBoost uses positional names by default)
        mean_abs = np.array([
            gain.get(f"f{i}", 0.0) for i in range(len(features))
        ])
        pct = mean_abs / max(mean_abs.sum(), 1e-9) * 100
        cat_map = {f: "Clinical" for f in CLINICAL_FEATURES}
        cat_map.update({f: "SDOH" for f in SDOH_FEATURES})
        return pd.DataFrame({
            "feature":      features,
            "importance":   mean_abs,
            "shap_pct":     pct,
            "category":     [cat_map.get(f, "Other") for f in features],
            "method":       ["xgb_gain"] * len(features),
        }).sort_values("shap_pct", ascending=False)

    mean_abs = np.abs(sv).mean(axis=0)
    pct = mean_abs / mean_abs.sum() * 100
    cat_map = {f: "Clinical" for f in CLINICAL_FEATURES}
    cat_map.update({f: "SDOH" for f in SDOH_FEATURES})
    out = pd.DataFrame({
        "feature":      features,
        "mean_abs_shap": mean_abs,
        "shap_pct":      pct,
        "category":     [cat_map.get(f, "Other") for f in features],
        "method":       ["shap_tree"] * len(features),
    }).sort_values("shap_pct", ascending=False)
    return out


# ── Equity analysis (race/ethnicity, education, PIR strata) ──────────────
def equity_analysis(df, oof_probs, target=TARGET):
    """
    Evaluate subgroup performance using OUT-OF-FOLD predicted probabilities,
    not in-training predictions. Using in-training preds gives ~1.0 AUROC for
    every subgroup because the model has memorized the training set.

    Pass in `oof_probs` from cv_xgb (one prob per row, generated when each
    row was in the validation fold).
    """
    df = df.copy()
    df["prob"] = oof_probs
    df["y"]    = df[target]
    rows = []

    # Race/ethnicity (NHANES RIDRETH3 codes)
    race_map = {1: "Mexican_American", 2: "Other_Hispanic",
                3: "NH_White",         4: "NH_Black",
                6: "NH_Asian",         7: "Other_Multi",
                5: "Other_Race"}
    for code, label in race_map.items():
        mask = df["race_eth"] == code
        if mask.sum() < 30:
            continue
        sub = df[mask]
        if len(sub["y"].unique()) < 2:
            continue
        m = compute_metrics(sub["y"].values, sub["prob"].values)
        lo, hi = bootstrap_auroc_ci(sub["y"].values, sub["prob"].values)
        m["AUROC_CI_lower"] = lo; m["AUROC_CI_upper"] = hi
        m["subgroup"] = label; m["n"] = int(mask.sum())
        rows.append(m)

    # Education tertiles (DMDEDUC2: 1-5)
    for code, label in [(1, "Edu_Less_HS"), (3, "Edu_HS"),
                         (4, "Edu_Some_College"), (5, "Edu_College_Plus")]:
        mask = df["education"] == code
        if mask.sum() < 30:
            continue
        sub = df[mask]
        if len(sub["y"].unique()) < 2:
            continue
        m = compute_metrics(sub["y"].values, sub["prob"].values)
        lo, hi = bootstrap_auroc_ci(sub["y"].values, sub["prob"].values)
        m["AUROC_CI_lower"] = lo; m["AUROC_CI_upper"] = hi
        m["subgroup"] = label; m["n"] = int(mask.sum())
        rows.append(m)

    # Poverty income ratio tertiles
    pir_t1 = df["pir"].quantile(1/3)
    pir_t2 = df["pir"].quantile(2/3)
    for label, mask in [
        ("PIR_Low",  df["pir"] <= pir_t1),
        ("PIR_Mid",  (df["pir"] > pir_t1) & (df["pir"] <= pir_t2)),
        ("PIR_High", df["pir"] > pir_t2),
    ]:
        if mask.sum() < 30:
            continue
        sub = df[mask]
        if len(sub["y"].unique()) < 2:
            continue
        m = compute_metrics(sub["y"].values, sub["prob"].values)
        lo, hi = bootstrap_auroc_ci(sub["y"].values, sub["prob"].values)
        m["AUROC_CI_lower"] = lo; m["AUROC_CI_upper"] = hi
        m["subgroup"] = label; m["n"] = int(mask.sum())
        rows.append(m)

    return pd.DataFrame(rows)


# ── Calibration ──────────────────────────────────────────────────────────
def calibration(y_true, y_prob, n_bins=10):
    fop, mpv = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame({
        "mean_predicted_value": mpv,
        "fraction_of_positives": fop,
    })


# ── Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("SDOH-CKDPred — Step 3: Training NHANES Mortality Model")
    print("=" * 64)

    # Load + preprocess
    cohort_path = os.path.join(PROC_DIR, "nhanes_cohort.csv")
    if not os.path.exists(cohort_path):
        print(f"\n[ERROR] {cohort_path} missing — run step2 first.")
        sys.exit(1)
    df = pd.read_csv(cohort_path)
    print(f"\n  Loaded full cohort:           N = {len(df):>5,}")

    # Restrict to primary analytic window
    df_primary = primary_cohort(df)
    df_primary = preprocess(df_primary)
    print(f"  Primary cohort (2005-2014):   N = {len(df_primary):>5,}")
    print(f"    5y mortality events:        N = {df_primary[TARGET].sum():>5,}  "
          f"({df_primary[TARGET].mean()*100:.1f}%)")

    # Sanity check: ensure no missing target
    df_primary = df_primary[df_primary[TARGET].notna()]
    print(f"  After dropping NaN target:    N = {len(df_primary):>5,}")

    # ── Model comparison ──────────────────────────────────────────────────
    cmp_df = compare_models(df_primary, ALL_FEATURES)

    # ── Cross-validation: clinical-only Logistic Regression ──────────────
    cv_clin_lr, oof_clin_lr_metrics, oof_clin_lr_probs = cv_logreg(
        df_primary, CLINICAL_FEATURES, "Clinical-only Logistic Regression"
    )

    # ── Cross-validation: clinical-only XGBoost (apples-to-apples baseline)
    cv_clin_xgb, oof_clin_xgb_metrics, oof_clin_xgb_probs = cv_xgb(
        df_primary, CLINICAL_FEATURES, "Clinical-only XGBoost"
    )

    # ── Cross-validation: full SDOH-augmented XGBoost ─────────────────────
    cv_full, oof_full_metrics, oof_full_probs = cv_xgb(
        df_primary, ALL_FEATURES, "SDOH-augmented XGBoost (full)"
    )

    # DeLong's test on OOF predictions (apples-to-apples: XGB vs XGB)
    print("\n  DeLong's test (OOF SDOH-augmented XGB vs Clinical-only XGB):")
    z_xx, p_xx = delong_test(df_primary[TARGET].values, oof_full_probs, oof_clin_xgb_probs)
    print(f"    z = {z_xx}   p = {p_xx}")
    print("\n  DeLong's test (OOF SDOH-augmented XGB vs Clinical-only LR):")
    z_xl, p_xl = delong_test(df_primary[TARGET].values, oof_full_probs, oof_clin_lr_probs)
    print(f"    z = {z_xl}   p = {p_xl}")
    z, p = z_xx, p_xx  # primary comparison is apples-to-apples

    # ── Train final models on full primary cohort ────────────────────────
    print("\n  Training final XGBoost models on full primary cohort...")
    final_full     = train_final_xgb(df_primary, ALL_FEATURES)
    final_clinical = train_final_xgb(df_primary, CLINICAL_FEATURES)

    # ── SHAP analysis on full model ──────────────────────────────────────
    print("\n  SHAP analysis on full model...")
    shap_df = shap_analysis(final_full, df_primary, ALL_FEATURES)
    if len(shap_df):
        print("\n  Top 10 features by SHAP:")
        print(shap_df.head(10)[["feature", "shap_pct", "category"]]
              .to_string(index=False))
        cat_totals = shap_df.groupby("category")["shap_pct"].sum()
        print("\n  Category contributions:")
        for c, p in cat_totals.sort_values(ascending=False).items():
            print(f"    {c}: {p:.1f}%")

    # ── Equity analysis (uses OOF probabilities — honest subgroup metrics) ─
    print("\n  Equity analysis (using OOF probabilities)...")
    eq_df = equity_analysis(df_primary, oof_full_probs, target=TARGET)
    print(eq_df[["subgroup", "n", "AUROC", "AUROC_CI_lower",
                  "AUROC_CI_upper"]].to_string(index=False))

    # ── Calibration ──────────────────────────────────────────────────────
    cal_df = calibration(df_primary[TARGET].values, oof_full_probs)

    # ── Sensitivity: 3y mortality on cycles 2015-2018 ────────────────────
    print("\n  Sensitivity: 3-year mortality on cycles 2015-2018...")
    df_sec = secondary_cohort_3yr(df)
    if len(df_sec) > 0:
        df_sec = preprocess(df_sec)
        Xs, ys = get_X_y(df_sec, ALL_FEATURES, target="mort_3yr")
        ps = final_full.predict_proba(Xs)[:, 1]
        if len(np.unique(ys)) >= 2:
            sec_m = compute_metrics(ys, ps)
            lo, hi = bootstrap_auroc_ci(ys, ps)
            sec_m["AUROC_CI_lower"] = lo; sec_m["AUROC_CI_upper"] = hi
            print(f"    N = {len(df_sec):,}  events = {ys.sum()}")
            print(f"    AUROC = {sec_m['AUROC']}  (95% CI {lo}-{hi})")

    # ── Save everything ──────────────────────────────────────────────────
    final_full.save_model(os.path.join(MODEL_DIR, "nhanes_xgb_full.json"))
    final_clinical.save_model(os.path.join(MODEL_DIR, "nhanes_xgb_clinical.json"))
    joblib.dump(ALL_FEATURES,      os.path.join(MODEL_DIR, "feature_list_full.pkl"))
    joblib.dump(CLINICAL_FEATURES, os.path.join(MODEL_DIR, "feature_list_clinical.pkl"))
    cv_full.to_csv(os.path.join(OUTPUT_DIR, "nhanes_cv_results_full.csv"), index=False)
    cv_clin_lr.to_csv(os.path.join(OUTPUT_DIR, "nhanes_cv_results_clinical_lr.csv"), index=False)
    cv_clin_xgb.to_csv(os.path.join(OUTPUT_DIR, "nhanes_cv_results_clinical_xgb.csv"), index=False)
    if len(shap_df):
        shap_df.to_csv(os.path.join(OUTPUT_DIR, "nhanes_shap_importance.csv"), index=False)
    eq_df.to_csv(os.path.join(OUTPUT_DIR, "nhanes_equity_analysis.csv"), index=False)
    cmp_df.to_csv(os.path.join(OUTPUT_DIR, "nhanes_model_comparison.csv"), index=False)
    cal_df.to_csv(os.path.join(OUTPUT_DIR, "nhanes_calibration.csv"), index=False)

    summary_path = os.path.join(OUTPUT_DIR, "nhanes_summary.txt")
    with open(summary_path, "w") as f:
        f.write("SDOH-CKDPred — NHANES analysis summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Primary cohort: cycles 2005-2014, N = {len(df_primary):,}\n")
        f.write(f"5-year mortality events: {df_primary[TARGET].sum():,} "
                f"({df_primary[TARGET].mean()*100:.1f}%)\n\n")
        f.write("OOF cross-validated AUROC:\n")
        f.write(f"  Clinical-only LR:     {oof_clin_lr_metrics['AUROC']}  "
                f"(95% CI {oof_clin_lr_metrics['AUROC_CI_lower']}-"
                f"{oof_clin_lr_metrics['AUROC_CI_upper']})\n")
        f.write(f"  Clinical-only XGB:    {oof_clin_xgb_metrics['AUROC']}  "
                f"(95% CI {oof_clin_xgb_metrics['AUROC_CI_lower']}-"
                f"{oof_clin_xgb_metrics['AUROC_CI_upper']})\n")
        f.write(f"  SDOH-augmented XGB:   {oof_full_metrics['AUROC']}  "
                f"(95% CI {oof_full_metrics['AUROC_CI_lower']}-"
                f"{oof_full_metrics['AUROC_CI_upper']})\n")
        f.write(f"\nDeLong's tests (vs SDOH-augmented XGB):\n")
        f.write(f"  vs Clinical-only XGB (apples-to-apples): z={z_xx}, p={p_xx}\n")
        f.write(f"  vs Clinical-only LR:                     z={z_xl}, p={p_xl}\n")

    print("\n" + "=" * 64)
    print("Step 3 complete.")
    print(f"  Summary: {summary_path}")
    print(f"  Model:   {MODEL_DIR}/nhanes_xgb_full.json")
    print("=" * 64)
