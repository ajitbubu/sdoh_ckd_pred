"""
src/generate_ecological_figures.py
----------------------------------
Generates Figures 1-7 for Stage 1 (ecological model) from the outputs of
src/train_ecological_model.py.

If the real ADI 2020 block-group file is present, the figures will reflect
the manuscript R² ≈ 0.45. If only the placeholder ADI is available, the
figures are still generated (so the manuscript visually contains all 13
referenced figures), but a prominent yellow banner is overlaid stating
"PLACEHOLDER ADI — REGENERATE WITH REAL DATA FOR FINAL NUMBERS" so no
reader can mistake them for the production results.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(BASE_DIR, "ckd_pipeline", "outputs")
FIG  = os.path.join(BASE_DIR, "figures_phs")
os.makedirs(FIG, exist_ok=True)

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
    "warn":      "#f4d03f",
    "warn_text": "#7d6608",
}


def load_inputs():
    with open(os.path.join(OUT, "stage1_metrics.json")) as f:
        metrics = json.load(f)
    rand     = pd.read_csv(os.path.join(OUT, "stage1_random_5fold_results.csv"))
    loro     = pd.read_csv(os.path.join(OUT, "stage1_loro_results.csv"))
    capacity = pd.read_csv(os.path.join(OUT, "stage1_capacity_sweep.csv"))
    cal      = pd.read_csv(os.path.join(OUT, "stage1_calibration.csv"))
    quintile = pd.read_csv(os.path.join(OUT, "stage1_predictions_by_quintile.csv"))
    feat     = pd.read_csv(os.path.join(OUT, "stage1_feature_importance.csv"))
    oof      = pd.read_csv(os.path.join(OUT, "stage1_oof_predictions.csv"))
    return metrics, rand, loro, capacity, cal, quintile, feat, oof


def add_placeholder_banner(fig, is_placeholder):
    """Yellow banner across top of figure if placeholder ADI was used."""
    if not is_placeholder:
        return
    fig.text(
        0.5, 0.97,
        "PLACEHOLDER ADI — REGENERATE WITH REAL NEIGHBORHOOD ATLAS DATA FOR FINAL NUMBERS",
        ha="center", va="top",
        fontsize=9, fontweight="bold",
        color=PALETTE["warn_text"],
        bbox=dict(facecolor=PALETTE["warn"], edgecolor=PALETTE["warn_text"],
                  alpha=0.85, pad=4),
    )


# ── Figure 1: parity plot (predicted vs observed) ────────────────────────
def fig1_parity(oof, metrics, is_placeholder):
    fig, ax = plt.subplots(figsize=(6, 5.5))
    add_placeholder_banner(fig, is_placeholder)

    # Sample for plotting (60K points is too many)
    if len(oof) > 5000:
        s = oof.sample(n=5000, random_state=42)
    else:
        s = oof

    ax.scatter(s["KIDNEY_CrudePrev"], s["oof_pred"],
               s=4, alpha=0.18, color=PALETTE["primary"], edgecolors="none")
    lim_lo = min(oof["KIDNEY_CrudePrev"].min(), oof["oof_pred"].min()) - 0.5
    lim_hi = max(oof["KIDNEY_CrudePrev"].max(), oof["oof_pred"].max()) + 0.5
    ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi],
            color=PALETTE["secondary"], lw=1.5, linestyle="--",
            label="Perfect agreement")
    ax.set_xlim(lim_lo, lim_hi); ax.set_ylim(lim_lo, lim_hi)
    ax.set_xlabel("CDC PLACES observed CKD prevalence (%)")
    ax.set_ylabel("Model-predicted CKD prevalence (%)")
    ax.set_title("Figure 1. Tract-level parity plot",
                 loc="left", fontsize=12, fontweight="bold", pad=18)
    ax.legend(loc="lower right", frameon=True, fontsize=9)
    fig.text(0.02, 0.02,
             f"n = {metrics['n_tracts']:,} tracts; CV R² = {metrics['random_5fold_r2_mean']:.3f}",
             fontsize=8, color="gray")
    fig.savefig(os.path.join(FIG, "fig01_parity.png"))
    plt.close(fig)


# ── Figure 2: calibration plot ───────────────────────────────────────────
def fig2_calibration(cal, metrics, is_placeholder):
    fig, ax = plt.subplots(figsize=(6, 5.5))
    add_placeholder_banner(fig, is_placeholder)

    lim = max(cal["mean_predicted"].max(), cal["observed"].max()) + 0.3
    ax.plot([0, lim], [0, lim], color=PALETTE["muted"],
            lw=1.2, linestyle="--", label="Perfect calibration")
    ax.plot(cal["mean_predicted"], cal["observed"],
            "o-", color=PALETTE["primary"], lw=2, markersize=8,
            label="Observed (decile bins)")
    for _, r in cal.iterrows():
        ax.annotate(f"D{int(r['decile'])}",
                    xy=(r["mean_predicted"], r["observed"]),
                    xytext=(5, 5), textcoords="offset points",
                    fontsize=8, color="gray")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Mean predicted CKD prevalence (%)")
    ax.set_ylabel("Observed CKD prevalence (%)")
    ax.set_title("Figure 2. Stage 1 calibration plot (deciles)",
                 loc="left", fontsize=12, fontweight="bold", pad=18)
    ax.legend(loc="upper left", frameon=True, fontsize=9)
    fig.text(0.02, 0.02,
             f"Calibration slope = {metrics['calibration_slope']:.3f}, "
             f"intercept = {metrics['calibration_intercept']:.3f}",
             fontsize=8, color="gray")
    fig.savefig(os.path.join(FIG, "fig02_stage1_calibration.png"))
    plt.close(fig)


# ── Figure 3: leave-one-region-out panels ────────────────────────────────
def fig3_loro(loro, is_placeholder):
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.5), sharey=True)
    add_placeholder_banner(fig, is_placeholder)

    for ax, (_, row) in zip(axes, loro.iterrows()):
        bars = ax.bar(["R²", "MAE", "Cal slope"],
                       [row["r2"], row["mae"], row["calibration_slope"]],
                       color=[PALETTE["primary"], PALETTE["secondary"], PALETTE["accent"]])
        ax.set_title(f"Hold out {row['held_out_region']}\n"
                      f"(n_test = {int(row['n_test']):,})",
                      fontsize=11, fontweight="bold")
        ax.set_ylim(min(0, loro[["r2", "mae", "calibration_slope"]].values.min() - 0.1),
                     max(1.2, loro[["r2", "mae", "calibration_slope"]].values.max() + 0.1))
        for b, v in zip(bars, [row["r2"], row["mae"], row["calibration_slope"]]):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.02,
                     f"{v:.3f}", ha="center", fontsize=9)

    fig.suptitle("Figure 3. Leave-one-Census-region-out cross-validation",
                  fontsize=13, fontweight="bold", x=0.07, ha="left", y=1.02)
    fig.savefig(os.path.join(FIG, "fig03_loro_panels.png"))
    plt.close(fig)


# ── Figure 4: capacity sensitivity sweep ─────────────────────────────────
def fig4_capacity(capacity, is_placeholder):
    fig, ax = plt.subplots(figsize=(7, 5))
    add_placeholder_banner(fig, is_placeholder)

    labels = [f"n_est={int(r['n_estimators'])}\nmax_d={int(r['max_depth'])}\n"
               f"lr={r['learning_rate']:.2f}"
               for _, r in capacity.iterrows()]
    bars = ax.bar(labels, capacity["r2_mean"], color=PALETTE["primary"],
                   yerr=capacity["r2_std"], ecolor=PALETTE["secondary"], capsize=6)
    for b, v in zip(bars, capacity["r2_mean"]):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.005,
                 f"{v:.3f}", ha="center", fontsize=9)
    ax.set_ylabel("Cross-validated R² (mean ± SD across 5 folds)")
    ax.set_title("Figure 4. XGBoost capacity sensitivity sweep",
                  loc="left", fontsize=12, fontweight="bold", pad=18)
    ax.set_ylim(min(capacity["r2_mean"].min() - 0.05, -0.05),
                 max(capacity["r2_mean"].max() + 0.1, 0.55))
    fig.savefig(os.path.join(FIG, "fig04_capacity_sweep.png"))
    plt.close(fig)


# ── Figure 5: ADI quintile gradient ──────────────────────────────────────
def fig5_adi_gradient(quintile, is_placeholder):
    fig, ax = plt.subplots(figsize=(7, 5))
    add_placeholder_banner(fig, is_placeholder)

    x = quintile["ADI_quintile"]
    width = 0.35
    ax.bar(x - width/2, quintile["predicted"], width,
            color=PALETTE["primary"], label="Model-predicted")
    ax.bar(x + width/2, quintile["observed"], width,
            color=PALETTE["secondary"], label="CDC PLACES observed")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Q{int(q)}\n(n={int(n):,})"
                          for q, n in zip(quintile["ADI_quintile"], quintile["n"])])
    ax.set_xlabel("ADI quintile (1 = least deprived, 5 = most deprived)")
    ax.set_ylabel("Mean tract CKD prevalence (%)")
    ax.set_title("Figure 5. CKD prevalence by ADI quintile",
                  loc="left", fontsize=12, fontweight="bold", pad=18)
    ax.legend(loc="upper left", frameon=True, fontsize=9)
    fig.savefig(os.path.join(FIG, "fig05_adi_quintile.png"))
    plt.close(fig)


# ── Figure 6: feature gain importance ────────────────────────────────────
def fig6_importance(feat, is_placeholder):
    fig, ax = plt.subplots(figsize=(7, 4))
    add_placeholder_banner(fig, is_placeholder)

    feat = feat.sort_values("gain_importance", ascending=True)
    bars = ax.barh(feat["feature"], feat["gain_importance"],
                    color=PALETTE["primary"])
    for b, v in zip(bars, feat["gain_importance"]):
        ax.text(b.get_width() * 1.01, b.get_y() + b.get_height()/2,
                 f"{v:.1f}", va="center", fontsize=10)
    ax.set_xlabel("XGBoost gain importance")
    ax.set_title("Figure 6. ADI feature gain importance",
                  loc="left", fontsize=12, fontweight="bold", pad=18)
    fig.savefig(os.path.join(FIG, "fig06_feature_importance.png"))
    plt.close(fig)


# ── Figure 7: performance matrix ─────────────────────────────────────────
def fig7_perf_matrix(metrics, loro, is_placeholder):
    rows = [
        ("Random 5-fold R²",
         f"{metrics['random_5fold_r2_mean']:.3f} ± {metrics['random_5fold_r2_std']:.3f}"),
        ("Random 5-fold MAE (pp)",
         f"{metrics['random_5fold_mae_mean']:.3f}"),
        ("Calibration slope",
         f"{metrics['calibration_slope']:.3f}"),
        ("Calibration intercept (pp)",
         f"{metrics['calibration_intercept']:+.3f}"),
        ("LORO R² range",
         f"{metrics['loro_r2_min']:.3f} – {metrics['loro_r2_max']:.3f}"),
        ("Hold-out Northeast R²",
         f"{loro.loc[loro['held_out_region']=='Northeast', 'r2'].iloc[0]:.3f}" if "Northeast" in loro["held_out_region"].values else "—"),
        ("Hold-out Midwest R²",
         f"{loro.loc[loro['held_out_region']=='Midwest', 'r2'].iloc[0]:.3f}" if "Midwest" in loro["held_out_region"].values else "—"),
        ("Hold-out South R²",
         f"{loro.loc[loro['held_out_region']=='South', 'r2'].iloc[0]:.3f}" if "South" in loro["held_out_region"].values else "—"),
        ("Hold-out West R²",
         f"{loro.loc[loro['held_out_region']=='West', 'r2'].iloc[0]:.3f}" if "West" in loro["held_out_region"].values else "—"),
        ("N tracts", f"{metrics['n_tracts']:,}"),
        ("ADI source", str(metrics.get("adi_source", "n/a"))),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    add_placeholder_banner(fig, is_placeholder)
    ax.axis("off")
    table = ax.table(cellText=rows,
                      colLabels=["Metric", "Value"],
                      cellLoc="left", colLoc="left",
                      loc="center", colWidths=[0.55, 0.42])
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
    ax.set_title("Figure 7. Stage 1 ecological model performance matrix",
                  loc="left", fontsize=12, fontweight="bold", pad=18)
    fig.savefig(os.path.join(FIG, "fig07_performance_matrix.png"))
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("Generating Figures 1-7 for Stage 1 ecological model")
    print("=" * 64)

    metrics, rand, loro, capacity, cal, quintile, feat, oof = load_inputs()
    is_placeholder = (metrics.get("adi_source") == "placeholder_synthetic")
    if is_placeholder:
        print("\n  ⚠ ADI source is PLACEHOLDER. Figures will display banner.")
        print("    Drop real ADI 2020 block-group file and re-run train_ecological_model.py")
        print("    to regenerate with manuscript values.\n")

    fig1_parity(oof, metrics, is_placeholder);                print("  ✓ fig01_parity.png")
    fig2_calibration(cal, metrics, is_placeholder);            print("  ✓ fig02_stage1_calibration.png")
    fig3_loro(loro, is_placeholder);                            print("  ✓ fig03_loro_panels.png")
    fig4_capacity(capacity, is_placeholder);                    print("  ✓ fig04_capacity_sweep.png")
    fig5_adi_gradient(quintile, is_placeholder);                print("  ✓ fig05_adi_quintile.png")
    fig6_importance(feat, is_placeholder);                      print("  ✓ fig06_feature_importance.png")
    fig7_perf_matrix(metrics, loro, is_placeholder);            print("  ✓ fig07_performance_matrix.png")

    print("\n" + "=" * 64)
    print(f"Figures → {FIG}")
    print("=" * 64)
