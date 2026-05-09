"""
src/train_ecological_model.py
-----------------------------
Stage 1 of the JMIR PHS two-stage pipeline.

Trains an XGBoost regressor on census-tract Area Deprivation Index (ADI)
features to predict CDC PLACES 2022 tract-level CKD crude prevalence.

Pipeline per manuscript v3 (Sec 2.2):
  • Inner-join ADI block-group → tract aggregates with PLACES 2022 tracts.
  • Three CV strategies: (a) random 5-fold, (b) leave-one-Census-region-out,
    (c) capacity sensitivity sweep across 5 hyperparameter settings.
  • Report R², MAE, RMSE, calibration slope/intercept, gain importance.

==================================================================
IMPORTANT: ADI DATA STATUS
==================================================================
The ADI 2020 block-group file from the University of Wisconsin Neighborhood
Atlas requires registration and is NOT auto-downloadable. The file currently
present at ckd_pipeline/data/raw/adi_2020_national.csv is a SYNTHETIC
PLACEHOLDER (33,001 ZCTA-keyed rows with random ADI values), not real data.

For Stage 1 numbers to reproduce the manuscript's R² ≈ 0.450, the real ADI
file must be downloaded:
  1. Register at https://www.neighborhoodatlas.medicine.wisc.edu/
  2. Download '2020 ADI Download — National Block Group'
  3. Save to ckd_pipeline/data/raw/adi_2020_national_blockgroup.csv

This script detects whether a real block-group ADI file is present:
  • If yes: aggregates to tract via mean across constituent block-groups
    and runs the manuscript pipeline.
  • If no: generates a tract-level placeholder by random assignment to
    PLACES tracts and runs the pipeline structure (will NOT reproduce
    the R² ≈ 0.45 figure but verifies code paths).

Outputs:
  outputs/stage1_metrics.json
  outputs/stage1_random_5fold_results.csv
  outputs/stage1_loro_results.csv
  outputs/stage1_capacity_sweep.csv
  outputs/stage1_calibration.csv
  outputs/stage1_predictions_by_quintile.csv
  outputs/stage1_feature_importance.csv
  outputs/stage1_status.txt    — flags whether real or placeholder ADI was used
"""

import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE_DIR, "ckd_pipeline", "data", "raw")
PROC = os.path.join(BASE_DIR, "ckd_pipeline", "data", "processed")
OUT = os.path.join(BASE_DIR, "ckd_pipeline", "outputs")
for d in [PROC, OUT]:
    os.makedirs(d, exist_ok=True)

SEED = 42
np.random.seed(SEED)


# Census region by state abbreviation
CENSUS_REGION = {
    # Northeast
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast",
    "NH": "Northeast", "RI": "Northeast", "VT": "Northeast",
    "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast",
    # Midwest
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest", "OH": "Midwest",
    "WI": "Midwest", "IA": "Midwest", "KS": "Midwest", "MN": "Midwest",
    "MO": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    # South
    "DE": "South", "FL": "South", "GA": "South", "MD": "South",
    "NC": "South", "SC": "South", "VA": "South", "DC": "South",
    "WV": "South", "AL": "South", "KY": "South", "MS": "South",
    "TN": "South", "AR": "South", "LA": "South", "OK": "South",
    "TX": "South",
    # West
    "AZ": "West", "CO": "West", "ID": "West", "MT": "West",
    "NV": "West", "NM": "West", "UT": "West", "WY": "West",
    "AK": "West", "CA": "West", "HI": "West", "OR": "West", "WA": "West",
}


# ── ADI loader (real or placeholder) ─────────────────────────────────────
def load_adi_tract_level(places_tracts):
    """
    Returns (adi_tract_df, source). adi_tract_df has columns:
      TractFIPS, adi_natrank, adi_staternk, adi_quintile.
    Falls back to placeholder if real ADI file is not present.
    """
    real_bg_path = os.path.join(RAW, "adi_2020_national_blockgroup.csv")
    if os.path.exists(real_bg_path):
        print(f"  [REAL ADI] loading {real_bg_path}")
        bg = pd.read_csv(real_bg_path, dtype={"FIPS": str})
        # Block-group FIPS is 12 chars; tract FIPS is 11 chars (block-group is +1 digit)
        bg["TractFIPS"] = bg["FIPS"].str[:11]
        # Aggregate to tract by mean
        cols = [c for c in bg.columns if c.upper().startswith("ADI")]
        if not cols:
            cols = ["ADI_NATRANK", "ADI_STATERNK", "ADI_QUINTILE"]
        adi_tract = bg.groupby("TractFIPS")[cols].mean().reset_index()
        adi_tract.columns = [c.lower() if c != "TractFIPS" else c for c in adi_tract.columns]
        return adi_tract, "real_neighborhood_atlas"

    # Fallback: generate tract-level placeholder by random assignment to PLACES tracts.
    print(f"  [PLACEHOLDER ADI] real block-group ADI not present at {real_bg_path}")
    print(f"                   Generating synthetic tract-level ADI for pipeline test.")
    rng = np.random.default_rng(SEED)
    n = len(places_tracts)
    return pd.DataFrame({
        "TractFIPS": places_tracts,
        "adi_natrank": np.clip(rng.normal(50, 25, n), 1, 100),
        "adi_staternk": np.clip(rng.normal(50, 25, n), 1, 100),
        "adi_quintile": rng.choice([1, 2, 3, 4, 5], size=n),
    }), "placeholder_synthetic"


# ── Load CDC PLACES tract CKD prevalence ─────────────────────────────────
def load_places():
    path = os.path.join(RAW, "cdc_places", "places_2022_tract.csv")
    df = pd.read_csv(path, usecols=["StateAbbr", "CountyFIPS", "TractFIPS",
                                     "TotalPopulation", "KIDNEY_CrudePrev"],
                     dtype={"TractFIPS": str, "CountyFIPS": str})
    df = df.dropna(subset=["KIDNEY_CrudePrev", "TractFIPS"])
    df["region"] = df["StateAbbr"].map(CENSUS_REGION)
    df = df.dropna(subset=["region"])
    return df


# ── Build analytic dataset ───────────────────────────────────────────────
def build_dataset():
    print("\n  Loading PLACES 2022 tract CKD prevalence...")
    places = load_places()
    print(f"    PLACES tracts (with state+CKD): {len(places):,}")

    print("\n  Loading ADI...")
    adi, source = load_adi_tract_level(places["TractFIPS"].tolist())
    print(f"    ADI source: {source}")
    print(f"    ADI tract rows: {len(adi):,}")

    df = places.merge(adi, on="TractFIPS", how="inner")
    print(f"\n  Joined PLACES ∩ ADI: {len(df):,} tracts")
    return df, source


# ── Cross-validation runners ─────────────────────────────────────────────
FEATURES = ["adi_natrank", "adi_staternk", "adi_quintile"]
TARGET   = "KIDNEY_CrudePrev"


def fit_xgb(X_tr, y_tr, X_va, y_va, **params):
    p = dict(n_estimators=600, max_depth=5, learning_rate=0.05,
              subsample=0.9, colsample_bytree=0.9, random_state=SEED, n_jobs=-1)
    p.update(params)
    m = xgb.XGBRegressor(**p)
    m.fit(X_tr, y_tr)
    pred = m.predict(X_va)
    return m, pred


def random_5fold(df):
    print("\n  Random 5-fold CV...")
    X, y = df[FEATURES].values, df[TARGET].values
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    rows = []
    oof = np.zeros(len(y))
    for k, (tr, va) in enumerate(kf.split(X), 1):
        _, pred = fit_xgb(X[tr], y[tr], X[va], y[va])
        oof[va] = pred
        r2  = r2_score(y[va], pred)
        mae = mean_absolute_error(y[va], pred)
        rmse = np.sqrt(mean_squared_error(y[va], pred))
        rows.append({"fold": k, "r2": round(r2, 4),
                      "mae": round(mae, 4), "rmse": round(rmse, 4)})
        print(f"    Fold {k}: R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")
    df["oof_pred"] = oof
    return pd.DataFrame(rows), df


def leave_one_region_out(df):
    print("\n  Leave-one-Census-region-out CV...")
    rows = []
    for region in ["Northeast", "Midwest", "South", "West"]:
        train_mask = df["region"] != region
        test_mask  = df["region"] == region
        if test_mask.sum() == 0:
            continue
        X_tr = df.loc[train_mask, FEATURES].values
        y_tr = df.loc[train_mask, TARGET].values
        X_te = df.loc[test_mask, FEATURES].values
        y_te = df.loc[test_mask, TARGET].values
        _, pred = fit_xgb(X_tr, y_tr, X_te, y_te)
        # Calibration slope from decile-binned regression
        bins = pd.qcut(pred, q=10, duplicates="drop")
        cal = pd.DataFrame({"pred": pred, "obs": y_te, "bin": bins})
        decile_means = cal.groupby("bin").agg(mp=("pred", "mean"),
                                               mo=("obs",  "mean")).reset_index()
        slope, intercept, _, _, _ = stats.linregress(decile_means["mp"],
                                                       decile_means["mo"])
        rows.append({
            "held_out_region": region,
            "n_test": int(test_mask.sum()),
            "r2":   round(r2_score(y_te, pred), 4),
            "mae":  round(mean_absolute_error(y_te, pred), 4),
            "rmse": round(np.sqrt(mean_squared_error(y_te, pred)), 4),
            "calibration_slope": round(float(slope), 4),
            "calibration_intercept": round(float(intercept), 4),
        })
        print(f"    Hold out {region:<10s}: R²={rows[-1]['r2']:.4f}  "
               f"MAE={rows[-1]['mae']:.4f}  cal_slope={rows[-1]['calibration_slope']:.3f}")
    return pd.DataFrame(rows)


def capacity_sweep(df):
    print("\n  Capacity sensitivity sweep (5 settings)...")
    settings = [
        dict(n_estimators=200,  max_depth=3, learning_rate=0.10),
        dict(n_estimators=400,  max_depth=4, learning_rate=0.08),
        dict(n_estimators=600,  max_depth=5, learning_rate=0.05),
        dict(n_estimators=800,  max_depth=6, learning_rate=0.04),
        dict(n_estimators=1000, max_depth=7, learning_rate=0.03),
    ]
    X, y = df[FEATURES].values, df[TARGET].values
    rows = []
    for s in settings:
        kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
        r2s = []
        for tr, va in kf.split(X):
            _, pred = fit_xgb(X[tr], y[tr], X[va], y[va], **s)
            r2s.append(r2_score(y[va], pred))
        rows.append({**s, "r2_mean": round(float(np.mean(r2s)), 4),
                     "r2_std": round(float(np.std(r2s)), 4)})
        print(f"    {s}  →  R² = {rows[-1]['r2_mean']:.4f} ± {rows[-1]['r2_std']:.4f}")
    return pd.DataFrame(rows)


def calibration_report(df):
    bins = pd.qcut(df["oof_pred"], q=10, duplicates="drop")
    cal = (df.groupby(bins)
              .agg(mean_predicted=("oof_pred", "mean"),
                   observed=(TARGET, "mean"),
                   n=("TractFIPS", "count"))
              .reset_index(drop=True))
    cal["decile"] = np.arange(1, len(cal) + 1)
    slope, intercept, _, _, _ = stats.linregress(cal["mean_predicted"],
                                                   cal["observed"])
    return cal, float(slope), float(intercept)


def predictions_by_quintile(df):
    return (df.groupby(df["adi_quintile"].round().astype(int))
              .agg(predicted=("oof_pred", "mean"),
                   observed=(TARGET, "mean"),
                   n=("TractFIPS", "count"))
              .reset_index()
              .rename(columns={"adi_quintile": "ADI_quintile"}))


def feature_importance(df):
    X, y = df[FEATURES].values, df[TARGET].values
    m, _ = fit_xgb(X, y, X, y)  # use full data for final importance
    booster = m.get_booster()
    gain = booster.get_score(importance_type="gain")
    return pd.DataFrame([
        {"feature": FEATURES[int(k[1:])], "gain_importance": v}
        for k, v in gain.items()
    ]).sort_values("gain_importance", ascending=False).reset_index(drop=True)


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("Stage 1: Census-tract ecological model (ADI → CDC PLACES CKD)")
    print("=" * 64)

    df, adi_source = build_dataset()

    rand_results, df = random_5fold(df)
    loro_results = leave_one_region_out(df)
    capacity_results = capacity_sweep(df)
    cal_df, cal_slope, cal_intercept = calibration_report(df)
    quintile_df = predictions_by_quintile(df)
    importance_df = feature_importance(df)

    metrics = {
        "n_tracts": int(len(df)),
        "adi_source": adi_source,
        "random_5fold_r2_mean":  round(float(rand_results["r2"].mean()), 4),
        "random_5fold_r2_std":   round(float(rand_results["r2"].std()), 4),
        "random_5fold_mae_mean": round(float(rand_results["mae"].mean()), 4),
        "calibration_slope":     round(cal_slope, 4),
        "calibration_intercept": round(cal_intercept, 4),
        "loro_r2_min": round(float(loro_results["r2"].min()), 4),
        "loro_r2_max": round(float(loro_results["r2"].max()), 4),
        "manuscript_target_r2": 0.450,
    }

    # Save outputs
    with open(os.path.join(OUT, "stage1_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    rand_results.to_csv(os.path.join(OUT, "stage1_random_5fold_results.csv"), index=False)
    loro_results.to_csv(os.path.join(OUT, "stage1_loro_results.csv"), index=False)
    capacity_results.to_csv(os.path.join(OUT, "stage1_capacity_sweep.csv"), index=False)
    cal_df.to_csv(os.path.join(OUT, "stage1_calibration.csv"), index=False)
    quintile_df.to_csv(os.path.join(OUT, "stage1_predictions_by_quintile.csv"), index=False)
    importance_df.to_csv(os.path.join(OUT, "stage1_feature_importance.csv"), index=False)
    df[["TractFIPS", "StateAbbr", "region", TARGET, "oof_pred",
         "adi_quintile"]].to_csv(os.path.join(OUT, "stage1_oof_predictions.csv"),
                                  index=False)

    with open(os.path.join(OUT, "stage1_status.txt"), "w") as f:
        f.write(f"ADI source: {adi_source}\n")
        if adi_source == "placeholder_synthetic":
            f.write("\n*** PLACEHOLDER ADI USED — STAGE 1 NUMBERS ARE NOT THE\n")
            f.write("*** MANUSCRIPT NUMBERS. Download real ADI 2020 from\n")
            f.write("*** https://www.neighborhoodatlas.medicine.wisc.edu/\n")
            f.write(f"*** and save to {os.path.join(RAW, 'adi_2020_national_blockgroup.csv')}\n")
            f.write("*** then re-run.\n")

    print("\n" + "=" * 64)
    print("Stage 1 metrics:")
    for k, v in metrics.items():
        print(f"  {k:<30s}  {v}")
    if adi_source == "placeholder_synthetic":
        print("\n  ⚠  PLACEHOLDER ADI used — Stage 1 numbers are NOT the manuscript's.")
        print("     Download real ADI block-group file to reproduce R² ≈ 0.450.")
    print("=" * 64)
