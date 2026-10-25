"""
src/stage2_model_comparison.py
------------------------------
XGBoost vs logistic regression for the Stage 2 classifier, compared on equal
terms and with uncertainty that respects both the CV and the survey design.

Models (identical predictors, identical 5-fold stratified CV):
  xgb_native   XGBoost with native missing-value handling (comparator)
  xgb_median   XGBoost with median imputation fitted inside each training fold
  lr_median    L2 logistic regression with the same median imputation (primary model)
               (+ standardization, one-hot race/ethnicity; survey weights,
               no class reweighting)

Uncertainty: Rao-Wu rescaled bootstrap over NHANES PSUs within strata; in
each replicate the full 5-fold CV is re-run on the replicate sample with
replicate weights, so the interval reflects both model refitting and the
survey design. Differences are reported with 95% CIs only (no p-values;
DeLong's test assumes independent observations and fixed predictions).

Run after src/train_nhanes_model.py. Output: outputs/stage2_comparator_lr.json
"""

import json
import os
import sys
import time

import numpy as np
import xgboost as xgb
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from train_nhanes_model import OUT, SEED, FEATURES, XGB_PARAMS, weighted_auroc
from stage2_supplementary import load_cohort_with_design, rao_wu_replicates, ci

N_REFIT_BOOT = int(sys.argv[1]) if len(sys.argv) > 1 else 200
NUMERIC = [f for f in FEATURES if f != "race_eth"]


def make_models():
    lr_pre = make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
        (OneHotEncoder(handle_unknown="ignore"), ["race_eth"]))
    med = make_column_transformer(
        (SimpleImputer(strategy="median"), FEATURES))
    return {
        "xgb_native": make_pipeline(make_column_transformer(("passthrough", FEATURES)),
                                    xgb.XGBClassifier(**XGB_PARAMS)),
        "xgb_median": make_pipeline(med, xgb.XGBClassifier(**XGB_PARAMS)),
        "lr_median": make_pipeline(lr_pre, LogisticRegression(C=1.0, max_iter=2000)),
    }


def cv_aurocs(df, w, seed):
    """Run 5-fold CV for every model on df with weights w; return AUROCs."""
    y = df["ckd"].values
    oof = {k: np.zeros(len(y)) for k in make_models()}
    for tr, va in StratifiedKFold(5, shuffle=True, random_state=seed).split(df, y):
        for name, model in make_models().items():
            step = model.steps[-1][0]
            model.fit(df.iloc[tr][FEATURES], y[tr], **{f"{step}__sample_weight": w[tr]})
            oof[name][va] = model.predict_proba(df.iloc[va][FEATURES])[:, 1]
    return {k: weighted_auroc(y, v, w) for k, v in oof.items()}


if __name__ == "__main__":
    df = load_cohort_with_design()
    w = df["mec_weight"].values
    est = cv_aurocs(df, w, SEED)
    print("Point estimates:", {k: round(v, 4) for k, v in est.items()})

    reps = rao_wu_replicates(df, n_boot=N_REFIT_BOOT, seed=SEED + 1)
    boot = {k: [] for k in est}
    t0 = time.time()
    for b, rw in enumerate(reps):
        keep = rw > 0
        res = cv_aurocs(df[keep].reset_index(drop=True), rw[keep], SEED + b)
        for k, v in res.items():
            boot[k].append(v)
        if (b + 1) % 20 == 0:
            print(f"  replicate {b + 1}/{N_REFIT_BOOT} ({time.time() - t0:.0f}s)")

    boot = {k: np.asarray(v) for k, v in boot.items()}
    out = {
        "method": "5-fold stratified CV re-run inside each of "
                  f"{N_REFIT_BOOT} Rao-Wu PSU-within-strata bootstrap replicates; "
                  "replicate survey weights; percentile 95% CIs; no p-values",
        "models": {k: {"auroc": round(est[k], 4), "auroc_ci": ci(boot[k])} for k in est},
        "delta_xgb_median_minus_lr_median": {
            "estimate": round(est["xgb_median"] - est["lr_median"], 4),
            "ci": ci(boot["xgb_median"] - boot["lr_median"])},
        "delta_xgb_native_minus_lr_median": {
            "estimate": round(est["xgb_native"] - est["lr_median"], 4),
            "ci": ci(boot["xgb_native"] - boot["lr_median"])},
        "delta_xgb_native_minus_xgb_median": {
            "estimate": round(est["xgb_native"] - est["xgb_median"], 4),
            "ci": ci(boot["xgb_native"] - boot["xgb_median"])},
    }
    with open(os.path.join(OUT, "stage2_comparator_lr.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
