"""
step8_subgroup_calibration.py
-----------------------------
Compute calibration metrics per demographic/geographic subgroup on the
external validation cohort, and render a single reliability-diagram panel
with one curve per subgroup.

Addresses reviewer concern: equal AUROC across subgroups does not imply
equal calibration. Fairness-focused reviewers expect calibration
decomposed by subgroup (Brier, intercept, slope, and Hosmer-Lemeshow or
smoothed reliability curve).

Outputs
-------
outputs/table5_subgroup_calibration.csv
figures/fig11_subgroup_calibration.png
"""

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.metrics import brier_score_loss
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression

from config import *


def preprocess(df):
    from sklearn.preprocessing import LabelEncoder
    d = df.copy()
    le = LabelEncoder()
    d["sex_encoded"] = le.fit_transform(d["sex"])
    d["egfr_x_adi"] = d["egfr_baseline"] * d["adi_nat_rank"]
    d["uacr_x_food_desert"] = d["uacr_baseline"] * d["food_desert"]
    return d


def _logit(p, eps=1e-6):
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def calibration_intercept_slope(y_true, y_prob):
    """Fit logistic regression: y ~ a + b * logit(p).
       Calibration intercept = a (0 if perfect);
       Calibration slope     = b (1 if perfect)."""
    lr = LogisticRegression(fit_intercept=True, C=1e8, solver="lbfgs",
                            max_iter=1000)
    X = _logit(y_prob).reshape(-1, 1)
    lr.fit(X, y_true)
    slope = float(lr.coef_[0, 0])
    intercept = float(lr.intercept_[0])
    return intercept, slope


def hosmer_lemeshow(y_true, y_prob, n_bins=10):
    """Hosmer-Lemeshow goodness-of-fit: returns chi2 and p-value."""
    from scipy import stats
    df = pd.DataFrame({"y": y_true, "p": y_prob})
    df["bin"] = pd.qcut(df["p"], n_bins, labels=False, duplicates="drop")
    obs = df.groupby("bin")["y"].agg(["sum", "count"]).rename(
        columns={"sum": "obs", "count": "n"})
    exp = df.groupby("bin")["p"].sum().to_frame("exp")
    t = obs.join(exp)
    t["chi2_term"] = (t["obs"] - t["exp"])**2 / (t["exp"] * (1 - t["exp"]/t["n"]))
    chi2 = float(t["chi2_term"].sum())
    k = t.shape[0]
    dof = max(k - 2, 1)
    p = float(1 - stats.chi2.cdf(chi2, dof))
    return chi2, p, dof


if __name__ == "__main__":
    print("=" * 60)
    print("SDOH-CKDPred — Step 8: Subgroup Calibration")
    print("=" * 60)

    df_ext = pd.read_csv(os.path.join(PROC_DIR, "cohort_external_val.csv"))
    feats  = joblib.load(os.path.join(MODEL_DIR, "feature_list.pkl"))
    booster = xgb.Booster()
    booster.load_model(os.path.join(MODEL_DIR, "sdoh_ckdpred_final.json"))

    df = preprocess(df_ext)
    X  = df[feats].values
    y  = df["outcome_stage45_24mo"].values
    dmat = xgb.DMatrix(X, feature_names=feats)
    p  = booster.predict(dmat)

    df["prob"] = p
    df["y"]    = y

    subgroups = [
        ("Overall",          np.ones(len(df), dtype=bool)),
        ("African American", df["race_ethnicity"] == "African_American"),
        ("Hispanic/Latino",  df["race_ethnicity"] == "Hispanic_Latino"),
        ("White",            df["race_ethnicity"] == "White"),
        ("Rural",            df["urbanicity"]     == "Rural"),
        ("Urban",            df["urbanicity"]     == "Urban"),
        ("High ADI (Q5)",    df["adi_quintile"]   == 5),
    ]

    rows, curves = [], {}
    for label, mask in subgroups:
        mask_arr = mask.values if hasattr(mask, "values") else mask
        n = int(mask_arr.sum())
        if n < 50:
            continue
        y_s = y[mask_arr]
        p_s = p[mask_arr]
        brier = brier_score_loss(y_s, p_s)
        intercept, slope = calibration_intercept_slope(y_s, p_s)
        chi2, pval, dof = hosmer_lemeshow(y_s, p_s, n_bins=10)
        rows.append({
            "Subgroup":              label,
            "N":                     n,
            "Events":                int(y_s.sum()),
            "Prevalence":            round(float(y_s.mean()), 4),
            "Brier":                 round(brier, 4),
            "Calibration_Intercept": round(intercept, 4),
            "Calibration_Slope":     round(slope, 4),
            "HL_chi2":               round(chi2, 3),
            "HL_dof":                dof,
            "HL_pvalue":             round(pval, 4),
        })
        # Reliability curve
        frac_pos, mean_pred = calibration_curve(y_s, p_s, n_bins=10,
                                                strategy="quantile")
        curves[label] = (mean_pred, frac_pos)
        print(f"  {label:20s}  N={n:6d}  Brier={brier:.4f}  "
              f"intercept={intercept:+.3f}  slope={slope:.3f}  "
              f"HL chi2={chi2:.2f} (dof={dof}) p={pval:.3f}")

    # ── CSV ───────────────────────────────────────────────────────────────
    out_csv = os.path.join(OUTPUT_DIR, "table5_subgroup_calibration.csv")
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\n  Wrote {out_csv}")

    # ── Figure 11 ─────────────────────────────────────────────────────────
    plt.rcParams.update({"font.family": FONT_FAMILY, "font.size": 10})
    fig, ax = plt.subplots(figsize=(7.2, 6.0), dpi=FIGURE_DPI)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, linewidth=1,
            label="Perfect calibration")

    colors = {
        "Overall":          "#1F5C8B",
        "African American": "#C0392B",
        "Hispanic/Latino":  "#D4AC0D",
        "White":            "#2E75B6",
        "Rural":            "#1E8449",
        "Urban":            "#7D3C98",
        "High ADI (Q5)":    "#D35400",
    }
    markers = {"Overall": "o", "African American": "s",
               "Hispanic/Latino": "^", "White": "D",
               "Rural": "v", "Urban": ">", "High ADI (Q5)": "P"}

    for label, (mp, fp) in curves.items():
        ax.plot(mp, fp, marker=markers.get(label, "o"),
                color=colors.get(label, "#555555"),
                linewidth=1.6, markersize=5.5, alpha=0.9,
                label=label)

    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Mean predicted probability (bin)")
    ax.set_ylabel("Observed event fraction")
    ax.set_title("Figure 11. Subgroup Calibration (External Validation)",
                 fontsize=11, fontweight="bold", loc="left")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="lower right", frameon=True, fontsize=8.5)

    # Annotate overall Brier / slope on the plot for quick read
    over = next(r for r in rows if r["Subgroup"] == "Overall")
    note = (f"Overall: Brier={over['Brier']:.3f}  "
            f"Intercept={over['Calibration_Intercept']:+.2f}  "
            f"Slope={over['Calibration_Slope']:.2f}")
    ax.text(0.02, 0.97, note, transform=ax.transAxes,
            fontsize=8.5, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#BBBBBB", alpha=0.9))

    plt.tight_layout()
    fig_path = os.path.join(FIGURE_DIR, "fig11_subgroup_calibration.png")
    fig.savefig(fig_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Wrote {fig_path}")
    print("\nDone.")
