"""
src/generate_stage2_figures.py
------------------------------
Generates Figures 8-13 from the Stage 2 NHANES classifier outputs, plus
Tables 1-3. All figures are publication-quality 300 DPI PNGs with a
consistent style (Anthropic-neutral palette, clean axes).

Inputs (from train_nhanes_model.py):
  data/processed/nhanes_phs_cohort.csv
  outputs/stage2_oof_predictions.csv
  outputs/stage2_metrics.json
  outputs/stage2_calibration_deciles.csv
  outputs/stage2_subgroup_auroc.csv
  outputs/stage2_decision_curve.csv

Outputs (figures/ and tables/):
  figures/fig08_roc.png
  figures/fig09_pr.png
  figures/fig10_calibration.png
  figures/fig11_subgroup_forest.png
  figures/fig12_decision_curve.png
  figures/fig13_performance_matrix.png
  tables/table1_baseline_characteristics.csv
  tables/table2_performance_summary.csv
  tables/table3_confusion_at_operating_point.csv
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (roc_curve, precision_recall_curve,
                              roc_auc_score, average_precision_score)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(BASE_DIR, "ckd_pipeline", "data", "processed")
OUT  = os.path.join(BASE_DIR, "ckd_pipeline", "outputs")
FIG  = os.path.join(BASE_DIR, "figures_phs")
TBL  = os.path.join(BASE_DIR, "tables_phs")
for d in [FIG, TBL]:
    os.makedirs(d, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "--",
    "figure.dpi": 100, "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

PALETTE = {
    "primary":   "#1f4e79",
    "secondary": "#c55a11",
    "accent":    "#2e75b6",
    "muted":     "#9b9b9b",
    "good":      "#548235",
    "bad":       "#a52a2a",
}


def load_inputs():
    cohort = pd.read_csv(os.path.join(PROC, "nhanes_phs_cohort.csv"))
    oof    = pd.read_csv(os.path.join(OUT, "stage2_oof_predictions.csv"))
    with open(os.path.join(OUT, "stage2_metrics.json")) as f:
        metrics = json.load(f)
    cal    = pd.read_csv(os.path.join(OUT, "stage2_calibration_deciles.csv"))
    sg     = pd.read_csv(os.path.join(OUT, "stage2_subgroup_auroc.csv"))
    dc     = pd.read_csv(os.path.join(OUT, "stage2_decision_curve.csv"))
    return cohort, oof, metrics, cal, sg, dc


# ── Figure 8: ROC curve ──────────────────────────────────────────────────
def fig8_roc(oof, metrics):
    y, p, w = oof["ckd"].values, oof["oof_prob"].values, cohort_weights(oof)
    fpr, tpr, _ = roc_curve(y, p, sample_weight=w)
    auc_w = roc_auc_score(y, p, sample_weight=w)

    fig, ax = plt.subplots(figsize=(6, 5.2))
    ax.plot(fpr, tpr, color=PALETTE["primary"], lw=2.5,
            label=f"NHANES classifier (AUROC = {auc_w:.3f})")
    ax.plot([0, 1], [0, 1], color=PALETTE["muted"], lw=1.2,
            linestyle="--", label="Chance")
    ax.set_xlabel("False positive rate (1 − specificity)")
    ax.set_ylabel("True positive rate (sensitivity)")
    ax.set_title("Figure 8. ROC curve, Stage 2 NHANES classifier",
                 loc="left", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.005)
    ax.legend(loc="lower right", frameon=True, fontsize=10)
    fig.text(0.02, 0.02,
             f"5-fold CV, NHANES MEC weights, n={metrics['n']:,}, "
             f"per-fold AUROC range {metrics['auroc_per_fold_min']:.3f}–"
             f"{metrics['auroc_per_fold_max']:.3f}",
             fontsize=8, color="gray")
    fig.savefig(os.path.join(FIG, "fig08_roc.png"))
    plt.close(fig)


# ── Figure 9: Precision-Recall curve ─────────────────────────────────────
def fig9_pr(oof, metrics):
    y, p, w = oof["ckd"].values, oof["oof_prob"].values, cohort_weights(oof)
    precision, recall, _ = precision_recall_curve(y, p, sample_weight=w)
    auprc = average_precision_score(y, p, sample_weight=w)
    prev = (y * w).sum() / w.sum()

    fig, ax = plt.subplots(figsize=(6, 5.2))
    ax.plot(recall, precision, color=PALETTE["primary"], lw=2.5,
            label=f"NHANES classifier (AUPRC = {auprc:.3f})")
    ax.axhline(prev, color=PALETTE["muted"], lw=1.2, linestyle="--",
               label=f"Prevalence baseline ({prev*100:.1f}%)")
    ax.set_xlabel("Recall (sensitivity)")
    ax.set_ylabel("Precision (positive predictive value)")
    ax.set_title("Figure 9. Precision-Recall curve, Stage 2 NHANES classifier",
                 loc="left", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.005)
    ax.legend(loc="upper right", frameon=True, fontsize=10)
    fig.savefig(os.path.join(FIG, "fig09_pr.png"))
    plt.close(fig)


# ── Figure 10: Calibration plot by decile ────────────────────────────────
def fig10_calibration(cal, metrics):
    fig, ax = plt.subplots(figsize=(6, 5.2))
    ax.plot([0, cal["mean_predicted"].max() * 1.05],
            [0, cal["mean_predicted"].max() * 1.05],
            color=PALETTE["muted"], lw=1.2, linestyle="--",
            label="Perfect calibration")
    ax.plot(cal["mean_predicted"], cal["observed"],
            "o-", color=PALETTE["primary"], lw=2, markersize=8,
            label="Observed (decile bins)")
    for _, r in cal.iterrows():
        ax.annotate(f"D{int(r['decile'])}",
                    xy=(r["mean_predicted"], r["observed"]),
                    xytext=(5, 5), textcoords="offset points",
                    fontsize=8, color="gray")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed CKD prevalence (survey-weighted)")
    ax.set_title("Figure 10. Calibration by decile, Stage 2 NHANES classifier",
                 loc="left", fontsize=12, fontweight="bold")
    ax.legend(loc="upper left", frameon=True, fontsize=10)
    fig.text(0.02, 0.02,
             f"Calibration slope = {metrics['calibration_slope']:.3f}, "
             f"intercept = {metrics['calibration_intercept']:.3f}",
             fontsize=9, color="gray")
    fig.savefig(os.path.join(FIG, "fig10_calibration.png"))
    plt.close(fig)


# ── Figure 11: Forest plot of subgroup AUROC ─────────────────────────────
def fig11_subgroup_forest(sg, metrics, oof):
    """Compute bootstrap 95% CIs (1000 resamples) and plot forest."""
    rng = np.random.RandomState(42)

    # Add CIs by bootstrapping within each subgroup
    sg = sg.copy()
    sg = sg.dropna(subset=["auroc"])
    sg["ci_lower"] = np.nan
    sg["ci_upper"] = np.nan

    for i, row in sg.iterrows():
        sub = subset_by_label(oof, row["subgroup"])
        if len(sub) < 50:
            continue
        boots = []
        for _ in range(500):
            idx = rng.randint(0, len(sub), size=len(sub))
            ys = sub["ckd"].values[idx]
            ps = sub["oof_prob"].values[idx]
            ws = sub["mec_weight"].values[idx] if "mec_weight" in sub.columns else None
            if len(np.unique(ys)) < 2:
                continue
            boots.append(roc_auc_score(ys, ps, sample_weight=ws))
        if boots:
            sg.at[i, "ci_lower"] = np.percentile(boots, 2.5)
            sg.at[i, "ci_upper"] = np.percentile(boots, 97.5)

    # Order: age bands, sex, race
    order = ["Age <50", "Age 50-64", "Age ≥65", "Female", "Male",
             "Mexican American", "Other Hispanic", "NH White",
             "NH Black", "NH Asian", "Other/Multi"]
    sg["sort_key"] = sg["subgroup"].apply(
        lambda x: order.index(x) if x in order else 999)
    sg = sg.sort_values("sort_key").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    y_positions = np.arange(len(sg))[::-1]
    ax.errorbar(
        sg["auroc"], y_positions,
        xerr=[sg["auroc"] - sg["ci_lower"], sg["ci_upper"] - sg["auroc"]],
        fmt="o", color=PALETTE["primary"], ecolor=PALETTE["accent"],
        markersize=8, capsize=4, lw=1.5,
    )
    ax.axvline(metrics["auroc"], color=PALETTE["secondary"],
                linestyle="--", lw=1.5,
                label=f"Overall AUROC = {metrics['auroc']:.3f}")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"{s} (n={int(n):,})"
                         for s, n in zip(sg["subgroup"], sg["n"])])
    ax.set_xlabel("Survey-weighted AUROC (95% bootstrap CI)")
    ax.set_xlim(0.5, 1.0)
    ax.set_title("Figure 11. Subgroup AUROC, Stage 2 NHANES classifier",
                 loc="left", fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", frameon=True, fontsize=9)
    ax.grid(axis="y", alpha=0.15)
    fig.savefig(os.path.join(FIG, "fig11_subgroup_forest.png"))
    plt.close(fig)
    return sg


# ── Figure 12: Decision curve ────────────────────────────────────────────
def fig12_decision_curve(dc):
    fig, ax = plt.subplots(figsize=(7, 5.2))
    ax.plot(dc["threshold"], dc["model_nb"],
            color=PALETTE["primary"], lw=2.5, label="NHANES classifier")
    ax.plot(dc["threshold"], dc["all_nb"],
            color=PALETTE["secondary"], lw=1.5, linestyle="--",
            label="Treat all")
    ax.plot(dc["threshold"], dc["none_nb"],
            color=PALETTE["muted"], lw=1.5, linestyle=":",
            label="Treat none")
    ax.set_xlabel("Risk threshold")
    ax.set_ylabel("Net benefit")
    ax.set_title("Figure 12. Decision-curve analysis (Vickers 2006)",
                 loc="left", fontsize=12, fontweight="bold")
    ax.set_xlim(0.05, 0.40)
    ax.legend(loc="upper right", frameon=True, fontsize=10)
    fig.savefig(os.path.join(FIG, "fig12_decision_curve.png"))
    plt.close(fig)


# ── Figure 13: Performance matrix ────────────────────────────────────────
def fig13_performance_matrix(metrics, sg):
    rows = [
        ("AUROC (95% per-fold range)",
         f"{metrics['auroc']:.3f} ({metrics['auroc_per_fold_min']:.3f}–"
         f"{metrics['auroc_per_fold_max']:.3f})"),
        ("AUPRC (vs prev baseline)",
         f"{metrics['auprc']:.3f} (baseline {metrics['weighted_prevalence_pct']/100:.3f})"),
        ("Brier score", f"{metrics['brier']:.3f}"),
        ("Calibration slope (intercept)",
         f"{metrics['calibration_slope']:.3f} ({metrics['calibration_intercept']:+.3f})"),
        ("Sensitivity at 90% specificity",
         f"{metrics['sensitivity_at_90pct_spec']*100:.1f}% "
         f"(threshold {metrics['operating_threshold_for_90pct_spec']:.3f})"),
        ("Subgroup AUROC range",
         f"{sg['auroc'].dropna().min():.3f}–{sg['auroc'].dropna().max():.3f}"),
        ("N analytic cohort", f"{metrics['n']:,}"),
        ("Survey-weighted CKD prevalence",
         f"{metrics['weighted_prevalence_pct']:.2f}%"),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=["Metric", "Value"],
        cellLoc="left", colLoc="left",
        loc="center", colWidths=[0.55, 0.42],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    for k, c in table.get_celld().items():
        if k[0] == 0:
            c.set_facecolor(PALETTE["primary"])
            c.set_text_props(color="white", weight="bold")
        elif k[0] % 2 == 1:
            c.set_facecolor("#f4f4f4")
        c.set_edgecolor("#cccccc")
    ax.set_title("Figure 13. Stage 2 NHANES classifier performance matrix",
                 loc="left", fontsize=12, fontweight="bold", pad=12)
    fig.savefig(os.path.join(FIG, "fig13_performance_matrix.png"))
    plt.close(fig)


# ── Tables ────────────────────────────────────────────────────────────────
def table1_baseline(cohort):
    """Table 1: baseline characteristics, survey-weighted, by CKD status."""
    w = cohort["mec_weight"]
    rows = []
    def wmean(col, mask):
        v = cohort.loc[mask, col]
        ww = cohort.loc[mask, "mec_weight"]
        v = v.dropna()
        ww = ww.loc[v.index]
        if len(v) == 0:
            return np.nan, np.nan
        m = (v * ww).sum() / ww.sum()
        sd = np.sqrt((ww * (v - m) ** 2).sum() / ww.sum())
        return m, sd
    def pct(col, val, mask):
        sub = cohort.loc[mask, col]
        ww = cohort.loc[mask, "mec_weight"]
        valid = sub.notna()
        if valid.sum() == 0:
            return np.nan
        return (ww[valid][sub[valid] == val].sum() / ww[valid].sum()) * 100

    for label, mask in [
        ("Overall", cohort.index >= 0),
        ("CKD = 0", cohort["ckd"] == 0),
        ("CKD = 1", cohort["ckd"] == 1),
    ]:
        n = int(mask.sum())
        n_w = float(cohort.loc[mask, "mec_weight"].sum())
        m_age, sd_age = wmean("age", mask)
        pct_female = pct("sex", 2, mask)
        pct_white  = pct("race_eth", 3, mask)
        pct_black  = pct("race_eth", 4, mask)
        pct_hisp   = pct("race_eth", 1, mask) + (pct("race_eth", 2, mask) or 0)
        m_pir, sd_pir = wmean("pir", mask)
        m_bmi, sd_bmi = wmean("bmi", mask)
        m_sbp, sd_sbp = wmean("sbp", mask)
        m_dbp, sd_dbp = wmean("dbp", mask)
        pct_htn   = pct("htn_self", 1, mask)
        pct_dm    = pct("dm_self", 1, mask)
        pct_hf    = pct("hf_self", 1, mask)
        pct_str   = pct("stroke_self", 1, mask)

        rows.append({
            "Stratum": label,
            "N (unweighted)": n,
            "Weighted N (millions)": round(n_w / 1e6, 2),
            "Age (mean ± SD)": f"{m_age:.1f} ± {sd_age:.1f}",
            "Female (%)": round(pct_female, 1) if pct_female else None,
            "NH White (%)": round(pct_white, 1) if pct_white else None,
            "NH Black (%)": round(pct_black, 1) if pct_black else None,
            "Hispanic (%)": round(pct_hisp, 1) if pct_hisp else None,
            "PIR (mean ± SD)": f"{m_pir:.2f} ± {sd_pir:.2f}",
            "BMI (mean ± SD)": f"{m_bmi:.1f} ± {sd_bmi:.1f}",
            "SBP (mmHg, mean ± SD)": f"{m_sbp:.1f} ± {sd_sbp:.1f}",
            "DBP (mmHg, mean ± SD)": f"{m_dbp:.1f} ± {sd_dbp:.1f}",
            "Self-rep HTN (%)": round(pct_htn, 1) if pct_htn else None,
            "Self-rep DM (%)": round(pct_dm, 1) if pct_dm else None,
            "Self-rep HF (%)": round(pct_hf, 1) if pct_hf else None,
            "Self-rep stroke (%)": round(pct_str, 1) if pct_str else None,
        })
    return pd.DataFrame(rows).set_index("Stratum").T


def table2_perf(metrics, sg):
    """Table 2: full performance metrics summary."""
    rows = [
        ("Discrimination — AUROC", f"{metrics['auroc']:.3f} "
         f"({metrics['auroc_per_fold_min']:.3f}–{metrics['auroc_per_fold_max']:.3f})"),
        ("Discrimination — AUPRC", f"{metrics['auprc']:.3f}"),
        ("Calibration — Brier score", f"{metrics['brier']:.3f}"),
        ("Calibration — slope", f"{metrics['calibration_slope']:.3f}"),
        ("Calibration — intercept", f"{metrics['calibration_intercept']:+.3f}"),
        ("Operating point threshold", f"{metrics['operating_threshold_for_90pct_spec']:.3f}"),
        ("Sensitivity @ 90% spec", f"{metrics['sensitivity_at_90pct_spec']*100:.1f}%"),
        ("Subgroup AUROC — minimum", f"{sg['auroc'].dropna().min():.3f}"),
        ("Subgroup AUROC — maximum", f"{sg['auroc'].dropna().max():.3f}"),
        ("N analytic cohort", f"{metrics['n']:,}"),
        ("Events (CKD positive)", f"{metrics['events']:,}"),
        ("Survey-weighted CKD prevalence",
         f"{metrics['weighted_prevalence_pct']:.2f}%"),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def table3_confusion(cohort, metrics):
    op = metrics["operating_threshold_for_90pct_spec"]
    pred = (cohort["oof_prob"] >= op).astype(int)
    actual = cohort["ckd"]
    w = cohort["mec_weight"]
    # Survey-weighted contingency
    tn = float(w[(actual == 0) & (pred == 0)].sum())
    fp = float(w[(actual == 0) & (pred == 1)].sum())
    fn = float(w[(actual == 1) & (pred == 0)].sum())
    tp = float(w[(actual == 1) & (pred == 1)].sum())
    sens = tp / (tp + fn)
    spec = tn / (tn + fp)
    ppv  = tp / (tp + fp)
    npv  = tn / (tn + fn)
    cm = pd.DataFrame({
        "Pred: no CKD": [round(tn / 1e6, 3), round(fn / 1e6, 3)],
        "Pred: CKD":    [round(fp / 1e6, 3), round(tp / 1e6, 3)],
    }, index=["Actual: no CKD (millions wt)", "Actual: CKD (millions wt)"])
    summary = pd.DataFrame([
        ("Operating threshold", round(op, 3)),
        ("Sensitivity (recall)", round(sens, 3)),
        ("Specificity", round(spec, 3)),
        ("Positive predictive value", round(ppv, 3)),
        ("Negative predictive value", round(npv, 3)),
    ], columns=["Metric", "Value"])
    return cm, summary


# ── Helpers ──────────────────────────────────────────────────────────────
def cohort_weights(oof):
    return oof["mec_weight"].values if "mec_weight" in oof.columns else None


def subset_by_label(oof, label):
    """Return the subset of oof for a given subgroup label."""
    if label.startswith("Age <50"):    return oof[oof["age"] < 50]
    if label == "Age 50-64":            return oof[(oof["age"] >= 50) & (oof["age"] < 65)]
    if label.startswith("Age ≥65"):     return oof[oof["age"] >= 65]
    if label == "Female":               return oof[oof["sex"] == 2]
    if label == "Male":                 return oof[oof["sex"] == 1]
    race_map = {"Mexican American": 1, "Other Hispanic": 2, "NH White": 3,
                "NH Black": 4, "NH Asian": 6, "Other/Multi": 7}
    if label in race_map:               return oof[oof["race_eth"] == race_map[label]]
    return oof.iloc[:0]


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("Generating Figures 8-13 + Tables 1-3 for Stage 2")
    print("=" * 64)

    cohort, oof, metrics, cal, sg, dc = load_inputs()
    # Merge cycle/race etc into oof for figure helpers
    oof = oof.merge(cohort[["SEQN", "mec_weight"]].drop_duplicates(),
                     on="SEQN", how="left", suffixes=("", "_dup"))
    if "mec_weight_dup" in oof.columns and oof["mec_weight"].isna().all():
        oof["mec_weight"] = oof["mec_weight_dup"]
    oof["mec_weight"] = oof["mec_weight"].fillna(1.0)

    print("\nFigures:")
    fig8_roc(oof, metrics);                              print("  ✓ fig08_roc.png")
    fig9_pr(oof, metrics);                               print("  ✓ fig09_pr.png")
    fig10_calibration(cal, metrics);                     print("  ✓ fig10_calibration.png")
    sg_with_ci = fig11_subgroup_forest(sg, metrics, oof);print("  ✓ fig11_subgroup_forest.png")
    fig12_decision_curve(dc);                            print("  ✓ fig12_decision_curve.png")
    fig13_performance_matrix(metrics, sg);               print("  ✓ fig13_performance_matrix.png")

    print("\nTables:")
    t1 = table1_baseline(cohort)
    t1.to_csv(os.path.join(TBL, "table1_baseline_characteristics.csv"))
    print("  ✓ table1_baseline_characteristics.csv")

    t2 = table2_perf(metrics, sg_with_ci)
    t2.to_csv(os.path.join(TBL, "table2_performance_summary.csv"), index=False)
    print("  ✓ table2_performance_summary.csv")

    cm_df, op_df = table3_confusion(oof, metrics)
    cm_df.to_csv(os.path.join(TBL, "table3a_confusion_matrix.csv"))
    op_df.to_csv(os.path.join(TBL, "table3b_operating_metrics.csv"), index=False)
    print("  ✓ table3a_confusion_matrix.csv + table3b_operating_metrics.csv")

    # Save subgroup-with-CIs for reference
    sg_with_ci.to_csv(os.path.join(OUT, "stage2_subgroup_auroc_with_ci.csv"),
                       index=False)

    print("\n" + "=" * 64)
    print(f"Figures → {FIG}")
    print(f"Tables  → {TBL}")
    print("=" * 64)
