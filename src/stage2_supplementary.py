"""
src/stage2_supplementary.py
---------------------------
Supplementary Stage 2 analyses (JMIR PHS revision, v6). Run after
src/train_nhanes_model.py, which writes the analytic cohort with
out-of-fold XGBoost predictions.

  1. Design-based 95% CIs for every headline metric: Rao-Wu rescaled
     bootstrap (1,000 replicates) resampling NHANES masked variance PSUs
     (SDMVPSU) within masked variance strata (SDMVSTRA), using MEC weights.
     Out-of-fold predictions are held fixed, so the CIs reflect sampling
     uncertainty of the evaluation sample.
  2. (Moved) The logistic regression comparison is in
     src/stage2_model_comparison.py.
  3. Missing data: per-predictor missingness and a multiple-imputation
     (chained equations, m=5) sensitivity analysis, imputing inside each
     training fold only.
  4. Operating points at 95/90/80/70/60% survey-weighted specificity.
  5. Race-free sensitivity model (race/ethnicity removed as a predictor).
  6. Demographic-only logistic baselines (age+sex; +race, PIR, BMI) to show
     the incremental value of blood pressure and self-reported conditions.
  7. Self-report bias check: measured hypertension among adults reporting
     no hypertension diagnosis, by income-to-poverty ratio.
  8. Subgroup sensitivity/specificity/PPV/NPV at the deployed threshold and
     subgroup calibration (calibration-in-the-large, logistic slope).
  9. Outcome-component completeness (creatinine and/or UACR) and
     performance restricted to participants with both.
 10. CKD awareness (self-reported vs measured CKD) by income-to-poverty ratio.
Calibration also includes the logistic intercept, a flexible spline
calibration curve with design-based pointwise CIs, ICI/E50/E90, and the
Brier skill score.

Outputs (ckd_pipeline/outputs/):
  stage2_metrics_ci.json
  stage2_subgroup_auroc_with_ci.csv
  tableS3_missingness.csv, stage2_mi_sensitivity.json
  tableS4_operating_points.csv
  stage2_race_free_sensitivity.json
  stage2_demographic_baselines.json
  stage2_unreported_hypertension.json
  stage2_calibration_flexible.csv, tableS5_subgroup_operating.csv
  stage2_outcome_components.json, stage2_ckd_awareness.json
(The XGBoost vs logistic regression comparison is in
src/stage2_model_comparison.py.)
"""

import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.metrics import roc_curve

from train_nhanes_model import (
    RAW, PROC, OUT, SEED, FEATURES, weighted_auroc, weighted_auprc,
    weighted_brier, calibration_deciles, sensitivity_at_specificity,
)

N_BOOT = 1000
XGB_PARAMS = dict(n_estimators=500, max_depth=4, learning_rate=0.05,
                  subsample=0.9, colsample_bytree=0.9,
                  eval_metric="logloss", random_state=SEED, n_jobs=-1)


# ── Data ────────────────────────────────────────────────────────────────
def load_cohort_with_design():
    df = pd.read_csv(os.path.join(PROC, "nhanes_phs_cohort.csv"))
    design = []
    for cycle, path in [("P_2017-2020", "P_2017-2020/P_DEMO.xpt"),
                        ("L_2021-2023", "L_2021-2022/DEMO_L.xpt")]:
        d = pd.read_sas(os.path.join(RAW, path), format="xport")
        d = d[["SEQN", "SDMVSTRA", "SDMVPSU"]].copy()
        d["SEQN"] = d["SEQN"].astype(int)
        d["cycle"] = cycle
        design.append(d)
    df = df.merge(pd.concat(design), on=["SEQN", "cycle"], how="left")
    assert df["SDMVSTRA"].notna().all(), "missing design variables"
    # Strata codes are cycle-specific; key them by cycle to be safe
    df["stratum"] = df["cycle"] + "_" + df["SDMVSTRA"].astype(int).astype(str)
    df["psu"] = df["stratum"] + "_" + df["SDMVPSU"].astype(int).astype(str)
    return df


# ── Rao-Wu rescaled bootstrap weight replicates ─────────────────────────
def rao_wu_replicates(df, n_boot=N_BOOT, seed=SEED):
    """Return an (n_boot, n) array of replicate weights."""
    rng = np.random.default_rng(seed)
    base_w = df["mec_weight"].values
    strata = {s: g["psu"].unique() for s, g in df.groupby("stratum")}
    psu_idx = {p: np.where(df["psu"].values == p)[0] for p in df["psu"].unique()}
    reps = np.empty((n_boot, len(df)))
    for b in range(n_boot):
        mult = np.zeros(len(df))
        for psus in strata.values():
            n_h = len(psus)
            m_h = n_h - 1
            counts = pd.Series(rng.choice(psus, size=m_h, replace=True)).value_counts()
            for p, c in counts.items():
                mult[psu_idx[p]] = c * n_h / m_h
        reps[b] = base_w * mult
    return reps


def logistic_calibration(y, p, w):
    """Weighted logistic recalibration slope (y ~ logit(p)) and
    calibration-in-the-large (weighted observed − mean predicted)."""
    lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    fit = LogisticRegression(penalty=None, max_iter=1000)
    fit.fit(lp.reshape(-1, 1), y, sample_weight=w)
    citl = float((w * y).sum() / w.sum() - (w * p).sum() / w.sum())
    return float(fit.coef_[0, 0]), citl


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def logistic_intercept(y, p, w):
    """Calibration intercept: a in logit(P(y=1)) = a + logit(p), i.e. logit(p)
    as an offset with slope fixed at 1 (weighted, solved by Newton)."""
    lp, a = _logit(p), 0.0
    for _ in range(50):
        mu = 1 / (1 + np.exp(-(a + lp)))
        step = np.sum(w * (y - mu)) / np.sum(w * mu * (1 - mu))
        a += step
        if abs(step) < 1e-10:
            break
    return float(a)


def brier_skill(y, p, w):
    """1 − Brier / Brier of the prevalence-only null model."""
    prev = np.average(y, weights=w)
    return float(1 - weighted_brier(y, p, w) / (prev * (1 - prev)))


CAL_GRID = np.round(np.arange(0.01, 0.81, 0.01), 2)


def flexible_calibration(y, p, w):
    """Flexible calibration curve: weighted logistic regression of y on a
    cubic spline of logit(p). Returns the smoothed observed risk on CAL_GRID
    and ICI / E50 / E90 (weighted mean / median / 90th percentile of
    |smoothed observed − predicted|; Austin & Steyerberg, Stat Med 2019)."""
    from sklearn.preprocessing import SplineTransformer
    model = make_pipeline(SplineTransformer(n_knots=4, degree=3),
                          LogisticRegression(penalty=None, max_iter=2000))
    model.fit(_logit(p).reshape(-1, 1), y, logisticregression__sample_weight=w)
    p_cal = model.predict_proba(_logit(p).reshape(-1, 1))[:, 1]
    err = np.abs(p_cal - p)
    order = np.argsort(err)
    cw = np.cumsum(w[order]) / w.sum()
    return {"curve": model.predict_proba(_logit(CAL_GRID).reshape(-1, 1))[:, 1],
            "ici": float(np.average(err, weights=w)),
            "e50": float(err[order][np.searchsorted(cw, 0.5)]),
            "e90": float(err[order][np.searchsorted(cw, 0.9)])}


def ci(values):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)])
    return [round(float(np.percentile(v, 2.5)), 4),
            round(float(np.percentile(v, 97.5)), 4)]


def sens_at_threshold(y, p, w, thr):
    pos = y == 1
    return float(w[pos & (p >= thr)].sum() / w[pos].sum())


# ── Comparator: logistic regression on identical features and folds ────
def lr_oof(df, features=FEATURES):
    X = df[features]
    y = df["ckd"].values
    w = df["mec_weight"].values
    numeric = [f for f in features if f != "race_eth"]
    transformers = [(make_pipeline(SimpleImputer(strategy="median"),
                                   StandardScaler()), numeric)]
    if "race_eth" in features:
        transformers.append((OneHotEncoder(handle_unknown="ignore"), ["race_eth"]))
    pre = make_column_transformer(*transformers)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y))
    for tr, va in skf.split(X, y):
        model = make_pipeline(pre, LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=2000))
        model.fit(X.iloc[tr], y[tr], logisticregression__sample_weight=w[tr])
        oof[va] = model.predict_proba(X.iloc[va])[:, 1]
    return oof


# ── Multiple-imputation sensitivity ─────────────────────────────────────
def mi_sensitivity(df, m=5):
    X = df[FEATURES].values
    y = df["ckd"].values
    w = df["mec_weight"].values
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    aurocs = []
    for k in range(m):
        oof = np.zeros(len(y))
        for tr, va in skf.split(X, y):
            imp = IterativeImputer(sample_posterior=True, max_iter=10,
                                   random_state=SEED + k)
            Xtr = imp.fit_transform(X[tr])
            Xva = imp.transform(X[va])
            model = xgb.XGBClassifier(**XGB_PARAMS)
            model.fit(Xtr, y[tr], sample_weight=w[tr])
            oof[va] = model.predict_proba(Xva)[:, 1]
        aurocs.append(weighted_auroc(y, oof, w))
        print(f"    imputation {k + 1}/{m}: AUROC={aurocs[-1]:.4f}")
    return aurocs


# ── Operating points ────────────────────────────────────────────────────
def operating_points(y, p, w, targets=(0.95, 0.90, 0.80, 0.70, 0.60)):
    rows = []
    for t in targets:
        sens, spec, thr = sensitivity_at_specificity(y, p, w, t)
        flag = p >= thr
        tp = w[flag & (y == 1)].sum()
        fp = w[flag & (y == 0)].sum()
        fn = w[~flag & (y == 1)].sum()
        tn = w[~flag & (y == 0)].sum()
        rows.append({"target_specificity": t,
                     "threshold": round(thr, 3),
                     "sensitivity": round(sens, 3),
                     "specificity": round(spec, 3),
                     "ppv": round(float(tp / (tp + fp)), 3),
                     "npv": round(float(tn / (tn + fn)), 3),
                     "pct_flagged": round(float((tp + fp) / w.sum() * 100), 1)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_cohort_with_design()
    y = df["ckd"].values
    p = df["oof_prob"].values
    w = df["mec_weight"].values
    print(f"Cohort n={len(df)}, strata={df['stratum'].nunique()}, "
          f"PSUs={df['psu'].nunique()}")

    # 1. Point estimates + design-based bootstrap CIs
    _, cal_slope, cal_int = calibration_deciles(y, p, w)
    sens, _, thr = sensitivity_at_specificity(y, p, w, 0.90)
    p_lr = lr_oof(df)  # full-feature LR, used by the nested baselines (section 6)

    print(f"Rao-Wu bootstrap ({N_BOOT} replicates)...")
    reps = rao_wu_replicates(df)
    flex_curves = []
    boot = {k: [] for k in ["auroc", "auprc", "brier", "cal_slope",
                            "logit_slope", "citl",
                            "sens_at_op", "logit_int", "bss", "ici", "e50", "e90"]}
    for rw in reps:
        keep = rw > 0
        yb, pb, wb = y[keep], p[keep], rw[keep]
        boot["auroc"].append(weighted_auroc(yb, pb, wb))
        boot["auprc"].append(weighted_auprc(yb, pb, wb))
        boot["brier"].append(weighted_brier(yb, pb, wb))
        boot["cal_slope"].append(calibration_deciles(yb, pb, wb)[1])
        ls, cl = logistic_calibration(yb, pb, wb)
        boot["logit_slope"].append(ls)
        boot["citl"].append(cl)
        boot["sens_at_op"].append(sens_at_threshold(yb, pb, wb, thr))
        boot["logit_int"].append(logistic_intercept(yb, pb, wb))
        boot["bss"].append(brier_skill(yb, pb, wb))
        flex = flexible_calibration(yb, pb, wb)
        for k in ("ici", "e50", "e90"):
            boot[k].append(flex[k])
        flex_curves.append(flex["curve"])

    # Subgroup AUROC CIs from the same design-based replicates
    race_map = {1: "Mexican American", 2: "Other Hispanic", 3: "NH White",
                4: "NH Black", 6: "NH Asian", 7: "Other/Multi"}
    groups = [("Age <50", df["age"] < 50),
              ("Age 50-64", (df["age"] >= 50) & (df["age"] < 65)),
              ("Age ≥65", df["age"] >= 65),
              ("Female", df["sex"] == 2), ("Male", df["sex"] == 1)]
    groups += [(lab, df["race_eth"] == c) for c, lab in race_map.items()]
    # Individual-level social risk: family income-to-poverty ratio
    groups += [("PIR <1.3", df["pir"] < 1.3),
               ("PIR 1.3-3.49", (df["pir"] >= 1.3) & (df["pir"] < 3.5)),
               ("PIR ≥3.5", df["pir"] >= 3.5)]
    sg_rows = []
    for label, mask in groups:
        mk = mask.values
        vals = []
        for rw in reps:
            k = mk & (rw > 0)
            if len(np.unique(y[k])) == 2:
                vals.append(weighted_auroc(y[k], p[k], rw[k]))
        lo, hi = ci(vals)
        sg_rows.append({"subgroup": label, "n": int(mk.sum()),
                        "events": int(y[mk].sum()),
                        "auroc": round(weighted_auroc(y[mk], p[mk], w[mk]), 4),
                        "ci_lower": lo, "ci_upper": hi})
    sg_ci = pd.DataFrame(sg_rows)
    sg_ci.to_csv(os.path.join(OUT, "stage2_subgroup_auroc_with_ci.csv"), index=False)

    auroc = weighted_auroc(y, p, w)
    flex = flexible_calibration(y, p, w)
    curves = np.vstack(flex_curves)
    pd.DataFrame({"predicted": CAL_GRID, "observed_smooth": flex["curve"],
                  "ci_lower": np.percentile(curves, 2.5, axis=0),
                  "ci_upper": np.percentile(curves, 97.5, axis=0)}).round(4).to_csv(
        os.path.join(OUT, "stage2_calibration_flexible.csv"), index=False)
    metrics_ci = {
        "ci_method": "Rao-Wu rescaled bootstrap over SDMVPSU within SDMVSTRA, "
                     f"{N_BOOT} replicates, MEC weights, fixed OOF predictions",
        "auroc": round(auroc, 4), "auroc_ci": ci(boot["auroc"]),
        "auprc": round(weighted_auprc(y, p, w), 4), "auprc_ci": ci(boot["auprc"]),
        "brier": round(weighted_brier(y, p, w), 4), "brier_ci": ci(boot["brier"]),
        "calibration_slope": round(cal_slope, 4),
        "calibration_slope_ci": ci(boot["cal_slope"]),
        "calibration_intercept": round(cal_int, 4),
        "logistic_calibration_slope": round(logistic_calibration(y, p, w)[0], 4),
        "logistic_calibration_slope_ci": ci(boot["logit_slope"]),
        "calibration_in_the_large": round(logistic_calibration(y, p, w)[1], 4),
        "calibration_in_the_large_ci": ci(boot["citl"]),
        "logistic_calibration_intercept": round(logistic_intercept(y, p, w), 4),
        "logistic_calibration_intercept_ci": ci(boot["logit_int"]),
        "ici": round(flex["ici"], 4), "ici_ci": ci(boot["ici"]),
        "e50": round(flex["e50"], 4), "e50_ci": ci(boot["e50"]),
        "e90": round(flex["e90"], 4), "e90_ci": ci(boot["e90"]),
        "brier_null": round(float(np.average(y, weights=w) * (1 - np.average(y, weights=w))), 4),
        "brier_skill_score": round(brier_skill(y, p, w), 4),
        "brier_skill_score_ci": ci(boot["bss"]),
        "threshold_90pct_spec": round(thr, 4),
        "sensitivity_at_90pct_spec": round(sens, 4),
        "sensitivity_ci": ci(boot["sens_at_op"]),
    }
    with open(os.path.join(OUT, "stage2_metrics_ci.json"), "w") as f:
        json.dump(metrics_ci, f, indent=2)

    # 3. Missingness + MI
    miss = pd.DataFrame({
        "predictor": FEATURES,
        "n_missing": [int(df[c].isna().sum()) for c in FEATURES],
        "pct_missing": [round(df[c].isna().mean() * 100, 1) for c in FEATURES],
    })
    miss.to_csv(os.path.join(OUT, "tableS3_missingness.csv"), index=False)
    print("Multiple imputation (m=5)...")
    mi = mi_sensitivity(df)
    mi_out = {"m": 5, "method": "IterativeImputer(sample_posterior=True) fit "
                                "within each training fold",
              "auroc_per_imputation": [round(a, 4) for a in mi],
              "auroc_mean": round(float(np.mean(mi)), 4),
              "auroc_native_missing": round(auroc, 4),
              "delta_vs_native": round(float(np.mean(mi)) - auroc, 4)}
    with open(os.path.join(OUT, "stage2_mi_sensitivity.json"), "w") as f:
        json.dump(mi_out, f, indent=2)

    # 4. Operating points
    op = operating_points(y, p, w)
    op.to_csv(os.path.join(OUT, "tableS4_operating_points.csv"), index=False)

    # 5. Race-free sensitivity model (race/ethnicity dropped as a predictor)
    print("Race-free XGBoost...")
    feats_nr = [f for f in FEATURES if f != "race_eth"]
    Xnr = df[feats_nr].values
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    p_nr = np.zeros(len(y))
    for tr, va in skf.split(Xnr, y):
        model = xgb.XGBClassifier(**XGB_PARAMS)
        model.fit(Xnr[tr], y[tr], sample_weight=w[tr])
        p_nr[va] = model.predict_proba(Xnr[va])[:, 1]
    d_nr = [weighted_auroc(y[rw > 0], p[rw > 0], rw[rw > 0])
            - weighted_auroc(y[rw > 0], p_nr[rw > 0], rw[rw > 0]) for rw in reps]
    race_free = {
        "auroc_race_free": round(weighted_auroc(y, p_nr, w), 4),
        "auroc_with_race": round(auroc, 4),
        "delta_with_minus_free": round(auroc - weighted_auroc(y, p_nr, w), 4),
        "delta_ci": ci(d_nr),
        "by_race_eth": {lab: {"with_race": round(weighted_auroc(y[m], p[m], w[m]), 4),
                              "race_free": round(weighted_auroc(y[m], p_nr[m], w[m]), 4)}
                        for c, lab in race_map.items()
                        for m in [(df["race_eth"] == c).values]},
    }
    with open(os.path.join(OUT, "stage2_race_free_sensitivity.json"), "w") as f:
        json.dump(race_free, f, indent=2)

    # 6. Incremental value over demographic-only baselines (nested LR models)
    print("Demographic-only baselines...")
    nested = {
        "age_sex": ["age", "sex"],
        "demographics_bmi": ["age", "sex", "race_eth", "pir", "bmi"],
        "full": FEATURES,
    }
    p_nest = {k: (p_lr if k == "full" else lr_oof(df, f)) for k, f in nested.items()}
    baselines = {"model": "L2 logistic regression, same folds/spec as comparator"}
    for k, f in nested.items():
        boots = [weighted_auroc(y[rw > 0], p_nest[k][rw > 0], rw[rw > 0]) for rw in reps]
        baselines[k] = {"features": f,
                        "auroc": round(weighted_auroc(y, p_nest[k], w), 4),
                        "auroc_ci": ci(boots)}
    for k in ["age_sex", "demographics_bmi"]:
        d = [weighted_auroc(y[rw > 0], p_lr[rw > 0], rw[rw > 0])
             - weighted_auroc(y[rw > 0], p_nest[k][rw > 0], rw[rw > 0]) for rw in reps]
        baselines[f"delta_full_minus_{k}"] = {
            "estimate": round(baselines["full"]["auroc"] - baselines[k]["auroc"], 4),
            "ci": ci(d)}
    with open(os.path.join(OUT, "stage2_demographic_baselines.json"), "w") as f:
        json.dump(baselines, f, indent=2)

    # 7. Self-report bias check: measured hypertension (≥140/90 mm Hg) among
    #    adults reporting no hypertension diagnosis, by income-to-poverty ratio
    unaware = {"definition": "weighted % with mean SBP>=140 or DBP>=90 among "
                             "htn_self==0 and BP measured"}
    meas_htn = ((df["sbp"] >= 140) | (df["dbp"] >= 90)).values
    base = ((df["htn_self"] == 0) & df["sbp"].notna()).values
    for label, mask in [("All", np.ones(len(df), bool)),
                        ("PIR <1.3", (df["pir"] < 1.3).values),
                        ("PIR 1.3-3.49", ((df["pir"] >= 1.3) & (df["pir"] < 3.5)).values),
                        ("PIR ≥3.5", (df["pir"] >= 3.5).values)]:
        m = base & mask
        est = float((w[m] * meas_htn[m]).sum() / w[m].sum() * 100)
        boots = [float((rw[m] * meas_htn[m]).sum() / rw[m].sum() * 100) for rw in reps]
        unaware[label] = {"n": int(m.sum()), "pct": round(est, 1),
                          "ci": [round(v, 1) for v in np.percentile(boots, [2.5, 97.5])]}
    with open(os.path.join(OUT, "stage2_unreported_hypertension.json"), "w") as f:
        json.dump(unaware, f, indent=2)

    # 8. Subgroup performance at the deployed threshold and subgroup
    #    calibration (AUROC parity alone says nothing about who is missed)
    print("Subgroup operating metrics and calibration...")
    flag = p >= thr

    def op_metrics(yy, ff, ww, pp):
        tp = ww[ff & (yy == 1)].sum(); fn = ww[~ff & (yy == 1)].sum()
        fp = ww[ff & (yy == 0)].sum(); tn = ww[~ff & (yy == 0)].sum()
        return {"sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp),
                "ppv": tp / (tp + fp) if tp + fp > 0 else np.nan,
                "npv": tn / (tn + fn), "pct_flagged": (tp + fp) / ww.sum() * 100,
                "observed_prev": np.average(yy, weights=ww) * 100,
                "mean_predicted": np.average(pp, weights=ww) * 100,
                "citl": np.average(yy, weights=ww) - np.average(pp, weights=ww),
                "logistic_slope": logistic_calibration(yy, pp, ww)[0]}

    op_rows = []
    for label, mask in [("All", pd.Series(True, index=df.index))] + groups:
        mk = mask.values
        est = op_metrics(y[mk], flag[mk], w[mk], p[mk])
        bt = {k: [] for k in est}
        for rw in reps:
            k_ = mk & (rw > 0)
            if len(np.unique(y[k_])) == 2:
                for k, v in op_metrics(y[k_], flag[k_], rw[k_], p[k_]).items():
                    bt[k].append(v)
        row = {"subgroup": label, "n": int(mk.sum()), "events": int(y[mk].sum())}
        for k, v in est.items():
            lo, hi = ci(bt[k])
            row[k] = round(float(v), 4)
            row[f"{k}_ci"] = f"{lo:.4f}–{hi:.4f}"
        op_rows.append(row)
    sg_op = pd.DataFrame(op_rows)
    sg_op.to_csv(os.path.join(OUT, "tableS5_subgroup_operating.csv"), index=False)

    # 9. Outcome components: the CKD label is eGFR<60 OR UACR>=30, so a
    #    participant missing one component can only be positive on the other
    has_scr, has_uacr = df["scr"].notna().values, df["uacr"].notna().values
    both = has_scr & has_uacr
    comp = {"n_both": int(both.sum()),
            "n_creatinine_only": int((has_scr & ~has_uacr).sum()),
            "n_uacr_only": int((~has_scr & has_uacr).sum())}
    for name, mk in [("all", np.ones(len(df), bool)), ("both", both),
                     ("creatinine_only", has_scr & ~has_uacr),
                     ("uacr_only", ~has_scr & has_uacr)]:
        if mk.sum():
            comp[f"weighted_prev_pct_{name}"] = round(float(np.average(y[mk], weights=w[mk]) * 100), 2)
    comp["auroc_oof_restricted_to_both"] = round(weighted_auroc(y[both], p[both], w[both]), 4)
    comp["auroc_oof_restricted_to_both_ci"] = ci(
        [weighted_auroc(y[both & (rw > 0)], p[both & (rw > 0)], rw[both & (rw > 0)]) for rw in reps])
    # Refit the model on participants with both components only
    db = df[both].reset_index(drop=True)
    Xb, yb_, wb_ = db[FEATURES].values, db["ckd"].values, db["mec_weight"].values
    pb_ = np.zeros(len(yb_))
    for tr, va in StratifiedKFold(5, shuffle=True, random_state=SEED).split(Xb, yb_):
        m_ = xgb.XGBClassifier(**XGB_PARAMS)
        m_.fit(Xb[tr], yb_[tr], sample_weight=wb_[tr])
        pb_[va] = m_.predict_proba(Xb[va])[:, 1]
    comp["auroc_refit_on_both"] = round(weighted_auroc(yb_, pb_, wb_), 4)
    with open(os.path.join(OUT, "stage2_outcome_components.json"), "w") as f:
        json.dump(comp, f, indent=2)

    # 10. CKD awareness: self-reported kidney disease (KIQ022, the item that
    #     corresponds to the BRFSS question behind CDC PLACES) vs measured CKD
    kiq = []
    for cycle, path in [("P_2017-2020", "P_2017-2020/P_KIQ_U.xpt"),
                        ("L_2021-2023", "L_2021-2022/KIQ_U_L.xpt")]:
        k_ = pd.read_sas(os.path.join(RAW, path), format="xport")[["SEQN", "KIQ022"]]
        k_["SEQN"] = k_["SEQN"].astype(int); k_["cycle"] = cycle
        kiq.append(k_)
    da = df.merge(pd.concat(kiq), on=["SEQN", "cycle"], how="left")
    told = da["KIQ022"].map({1.0: 1, 2.0: 0}).values  # 7/9/missing -> NaN
    has_q = ~np.isnan(told)
    aware = {"item": "KIQ022: ever told by a health professional you had weak or failing kidneys",
             "n_answered": int(has_q.sum())}
    pir_groups = [("All", np.ones(len(da), bool)), ("PIR <1.3", (da["pir"] < 1.3).values),
                  ("PIR 1.3-3.49", ((da["pir"] >= 1.3) & (da["pir"] < 3.5)).values),
                  ("PIR ≥3.5", (da["pir"] >= 3.5).values)]
    for label, mk in pir_groups:
        m_all = mk & has_q
        m_ckd = m_all & (y == 1)
        def stat(ww):
            return (np.average(y[m_all], weights=ww[m_all]) * 100,
                    np.average(told[m_all], weights=ww[m_all]) * 100,
                    np.average(told[m_ckd], weights=ww[m_ckd]) * 100)
        est = stat(w)
        bt = np.array([stat(rw) for rw in reps if rw[m_ckd].sum() > 0])
        aware[label] = {
            "n": int(m_all.sum()), "n_ckd": int(m_ckd.sum()),
            "measured_ckd_pct": round(est[0], 1),
            "self_reported_kidney_disease_pct": round(est[1], 1),
            "self_reported_kidney_disease_pct_ci": [round(v, 1) for v in np.percentile(bt[:, 1], [2.5, 97.5])],
            "awareness_among_ckd_pct": round(est[2], 1),
            "awareness_among_ckd_pct_ci": [round(v, 1) for v in np.percentile(bt[:, 2], [2.5, 97.5])],
        }
    lo, hi = aware["PIR <1.3"], aware["PIR ≥3.5"]
    aware["gradient_low_vs_high_income"] = {
        "measured_ckd_ratio": round(lo["measured_ckd_pct"] / hi["measured_ckd_pct"], 2),
        "self_reported_ratio": round(lo["self_reported_kidney_disease_pct"]
                                     / hi["self_reported_kidney_disease_pct"], 2)}
    with open(os.path.join(OUT, "stage2_ckd_awareness.json"), "w") as f:
        json.dump(aware, f, indent=2)

    print(sg_op.to_string(index=False))
    print(json.dumps(comp, indent=2))
    print(json.dumps(aware, indent=2))
    print(sg_ci.to_string(index=False))
    print(json.dumps(metrics_ci, indent=2))
    print(miss.to_string(index=False))
    print(json.dumps(mi_out, indent=2))
    print(op.to_string(index=False))
    print(json.dumps(race_free, indent=2))
    print(json.dumps(baselines, indent=2))
    print(json.dumps(unaware, indent=2))
