"""
step2_assemble_nhanes_cohort.py
-------------------------------
Assembles the analytic cohort from NHANES public-use files and the NCHS
Public-use Linked Mortality File. Replaces the synthetic generator.

Cohort definition (per KDIGO 2024):
  • Adults aged ≥20 (NHANES interviews adults ≥18; we use 20 to align with
    most epidemiologic CKD literature).
  • Baseline Stage 2-3 CKD:
      - Stage 2: eGFR 60-89 AND UACR ≥30 mg/g (proteinuria-defined)
      - Stage 3a: eGFR 45-59
      - Stage 3b: eGFR 30-44
  • Non-pregnant (where indicated by RIDEXPRG).
  • Eligible for mortality follow-up (ELIGSTAT = 1).

Outcome:
  • Primary: 5-year all-cause mortality (MORTSTAT=1 AND PERMTH_INT ≤ 60).
  • Secondary: CKD-cause mortality (UCOD_LEADING = "10" for kidney disease).

This script is intentionally explicit about every transformation so the data
audit trail is reviewable. No probabilistic label assignment, no
parameter-tuned outcome model. The label is observed, not constructed.

Inputs:
  data/raw/nhanes/<cycle>/*.xpt
  data/raw/nhanes/mortality/<cycle>.dat

Outputs:
  data/processed/nhanes_cohort.csv
  data/processed/nhanes_cohort_summary.txt   — flow diagram (drop counts)
"""

import os
import sys
import numpy as np
import pandas as pd

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RAW_DIR     = os.path.join(BASE_DIR, "data", "raw", "nhanes")
MORT_DIR    = os.path.join(RAW_DIR, "mortality")
PROC_DIR    = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

CYCLES = [
    ("2003-2004", "C"),
    ("2005-2006", "D"),
    ("2007-2008", "E"),
    ("2009-2010", "F"),
    ("2011-2012", "G"),
    ("2013-2014", "H"),
    ("2015-2016", "I"),
    ("2017-2018", "J"),
]


# ── XPT loader (graceful: returns empty df if file missing) ───────────────
def load_xpt(cycle, stem, suffix):
    path = os.path.join(RAW_DIR, cycle, f"{stem}_{suffix}.xpt")
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_sas(path, format="xport")
        return df
    except Exception as e:
        print(f"  [WARN] could not parse {path}: {e}")
        return pd.DataFrame()


# ── CKD-EPI 2021 race-free eGFR ───────────────────────────────────────────
def egfr_ckdepi_2021(scr_mgdl, age_yrs, sex):
    """
    CKD-EPI 2021 (race-free), per Inker et al. NEJM 2021.
    sex: 1=Male, 2=Female (NHANES RIAGENDR coding).
    Returns eGFR in mL/min/1.73m². NaN where inputs are NaN.
    """
    scr = np.asarray(scr_mgdl, dtype=float)
    age = np.asarray(age_yrs, dtype=float)
    is_female = (np.asarray(sex) == 2)
    kappa = np.where(is_female, 0.7, 0.9)
    alpha = np.where(is_female, -0.241, -0.302)
    sex_factor = np.where(is_female, 1.012, 1.0)
    ratio = scr / kappa
    egfr = (
        142.0
        * np.minimum(ratio, 1.0) ** alpha
        * np.maximum(ratio, 1.0) ** (-1.200)
        * 0.9938 ** age
        * sex_factor
    )
    return egfr


# ── UACR computation from urine albumin and creatinine ───────────────────
def compute_uacr(urxuma_mg_per_l, urxucr_mg_per_dl):
    """
    UACR (mg albumin per g creatinine):
      = (urine albumin [mg/L]) / (urine creatinine [mg/dL] * 0.01) [g/L]
    Equivalent to: urxuma * 100 / urxucr
    """
    a = np.asarray(urxuma_mg_per_l, dtype=float)
    c = np.asarray(urxucr_mg_per_dl, dtype=float)
    return np.where(c > 0, a * 100.0 / c, np.nan)


# ── Mortality file parser (fixed-width per CDC documentation) ────────────
def load_mortality(cycle):
    """
    NCHS Public-use Linked Mortality File layout (per
    https://www.cdc.gov/nchs/data-linkage/mortality-public.htm):
      Column positions (1-indexed):
        1-6    SEQN (NHANES participant ID)
        15     ELIGSTAT  (1=eligible for follow-up, 2=under 18, 3=ineligible)
        16     MORTSTAT  (0=alive at last follow-up, 1=deceased)
        17-19  UCOD_LEADING  (underlying cause leading group, e.g. 010=kidney)
        20     DIABETES_FLAG  (deceased: diabetes mentioned anywhere)
        21     HYPERTEN_FLAG
        43-45  PERMTH_INT  (months from interview to death/censor)
        47-49  PERMTH_EXM  (months from exam to death/censor)
    """
    path = os.path.join(MORT_DIR, f"{cycle}.dat")
    if not os.path.exists(path):
        print(f"  [WARN] mortality file missing for {cycle}")
        return pd.DataFrame()
    colspecs = [
        (0, 6),     # SEQN
        (14, 15),   # ELIGSTAT
        (15, 16),   # MORTSTAT
        (16, 19),   # UCOD_LEADING
        (19, 20),   # DIABETES_FLAG
        (20, 21),   # HYPERTEN_FLAG
        (42, 45),   # PERMTH_INT
        (46, 49),   # PERMTH_EXM
    ]
    names = ["SEQN", "ELIGSTAT", "MORTSTAT", "UCOD_LEADING",
             "MORT_DIAB_FLAG", "MORT_HTN_FLAG", "PERMTH_INT", "PERMTH_EXM"]
    mort = pd.read_fwf(
        path, colspecs=colspecs, names=names,
        dtype=str, na_values=["", "."],
    )
    # Coerce numeric where appropriate
    for col in ["SEQN", "ELIGSTAT", "MORTSTAT", "PERMTH_INT", "PERMTH_EXM"]:
        mort[col] = pd.to_numeric(mort[col], errors="coerce")
    return mort


# ── Diabetes definition (composite per ADA) ──────────────────────────────
def derive_diabetes(diq, ghb, biopro):
    """
    Diabetes flag per ADA composite definition:
      • Self-report (DIQ010 == 1, "Doctor told you have diabetes"), OR
      • HbA1c (LBXGH) ≥ 6.5%, OR
      • Fasting glucose (LBXSGL) ≥ 126 mg/dL.
    Returns a Series indexed by SEQN.
    """
    out = pd.Series(0, index=diq["SEQN"].astype(int) if len(diq) else [],
                     dtype=int)
    if len(diq) and "DIQ010" in diq.columns:
        sr = diq.set_index(diq["SEQN"].astype(int))["DIQ010"]
        out.loc[sr.index] = (sr == 1).astype(int).combine(out.loc[sr.index],
                                                            np.maximum)
    if len(ghb) and "LBXGH" in ghb.columns:
        gh = ghb.set_index(ghb["SEQN"].astype(int))["LBXGH"]
        ids_common = out.index.intersection(gh.index)
        out.loc[ids_common] = np.maximum(
            out.loc[ids_common].values,
            (gh.loc[ids_common] >= 6.5).fillna(False).astype(int).values,
        )
    if len(biopro) and "LBXSGL" in biopro.columns:
        sg = biopro.set_index(biopro["SEQN"].astype(int))["LBXSGL"]
        ids_common = out.index.intersection(sg.index)
        out.loc[ids_common] = np.maximum(
            out.loc[ids_common].values,
            (sg.loc[ids_common] >= 126).fillna(False).astype(int).values,
        )
    return out


# ── Hypertension definition ──────────────────────────────────────────────
def derive_hypertension(bpq, sbp_mean, dbp_mean):
    """
    Hypertension flag:
      • Self-report (BPQ020 == 1, "Doctor told you have high blood pressure"), OR
      • Mean SBP ≥ 130, OR
      • Mean DBP ≥ 80.
    Returns a Series indexed by SEQN.
    """
    out = pd.Series(0, index=bpq["SEQN"].astype(int) if len(bpq) else [],
                     dtype=int)
    if len(bpq) and "BPQ020" in bpq.columns:
        sr = bpq.set_index(bpq["SEQN"].astype(int))["BPQ020"]
        out.loc[sr.index] = (sr == 1).astype(int)
    # BP-derived
    sbp_high = (sbp_mean >= 130).fillna(False)
    dbp_high = (dbp_mean >= 80).fillna(False)
    bp_idx = sbp_mean.index.union(dbp_mean.index)
    bp_flag = pd.Series(0, index=bp_idx, dtype=int)
    bp_flag.loc[sbp_high.index[sbp_high]] = 1
    bp_flag.loc[dbp_high.index[dbp_high]] = 1
    out = out.reindex(out.index.union(bp_flag.index), fill_value=0)
    bp_flag = bp_flag.reindex(out.index, fill_value=0)
    out = out.combine(bp_flag, np.maximum)
    return out


# ── Per-cycle assembly ────────────────────────────────────────────────────
def assemble_cycle(cycle_label, suffix):
    """
    Load all required NHANES files for one cycle, merge by SEQN, derive
    features. Returns one row per cycle participant with cycle column added.
    """
    print(f"\n  Cycle {cycle_label} (suffix {suffix})")

    demo   = load_xpt(cycle_label, "DEMO",   suffix)
    biopro = load_xpt(cycle_label, "BIOPRO", suffix)
    albcr  = load_xpt(cycle_label, "ALB_CR", suffix)
    ghb    = load_xpt(cycle_label, "GHB",    suffix)
    bpx    = load_xpt(cycle_label, "BPX",    suffix)
    bmx    = load_xpt(cycle_label, "BMX",    suffix)
    diq    = load_xpt(cycle_label, "DIQ",    suffix)
    bpq    = load_xpt(cycle_label, "BPQ",    suffix)
    mcq    = load_xpt(cycle_label, "MCQ",    suffix)
    inq    = load_xpt(cycle_label, "INQ",    suffix)
    fsq    = load_xpt(cycle_label, "FSQ",    suffix)
    hiq    = load_xpt(cycle_label, "HIQ",    suffix)
    hoq    = load_xpt(cycle_label, "HOQ",    suffix)
    ocq    = load_xpt(cycle_label, "OCQ",    suffix)

    if len(demo) == 0:
        print(f"    [SKIP] no DEMO file — cycle not yet downloaded?")
        return pd.DataFrame()

    print(f"    DEMO: {len(demo):,}  BIOPRO: {len(biopro):,}  "
          f"ALB_CR: {len(albcr):,}  GHB: {len(ghb):,}  BPX: {len(bpx):,}")

    # Start with demographics — includes age, sex, race, education, PIR
    df = demo[["SEQN", "RIDAGEYR", "RIAGENDR", "RIDRETH3"
               if "RIDRETH3" in demo.columns else "RIDRETH1",
               "DMDEDUC2", "INDFMPIR"]].copy()
    df.columns = ["SEQN", "age", "sex", "race_eth", "education", "pir"]
    df["SEQN"] = df["SEQN"].astype(int)
    df["cycle"] = cycle_label

    # Serum creatinine → eGFR (CKD-EPI 2021)
    if len(biopro) and "LBXSCR" in biopro.columns:
        df = df.merge(biopro[["SEQN", "LBXSCR"]].rename(
            columns={"LBXSCR": "scr"}), on="SEQN", how="left")
        df["SEQN"] = df["SEQN"].astype(int)
        df["egfr"] = egfr_ckdepi_2021(df["scr"], df["age"], df["sex"])
    else:
        df["scr"] = np.nan
        df["egfr"] = np.nan

    # UACR
    if len(albcr) and {"URXUMA", "URXUCR"}.issubset(albcr.columns):
        ac = albcr[["SEQN", "URXUMA", "URXUCR"]].copy()
        ac["SEQN"] = ac["SEQN"].astype(int)
        ac["uacr"] = compute_uacr(ac["URXUMA"], ac["URXUCR"])
        df = df.merge(ac[["SEQN", "uacr"]], on="SEQN", how="left")
    else:
        df["uacr"] = np.nan

    # HbA1c
    if len(ghb) and "LBXGH" in ghb.columns:
        df = df.merge(ghb[["SEQN", "LBXGH"]].rename(
            columns={"LBXGH": "hba1c"}), on="SEQN", how="left")
    else:
        df["hba1c"] = np.nan

    # Blood pressure: mean of available BPXSY1-4 / BPXDI1-4 readings
    if len(bpx):
        sbp_cols = [c for c in bpx.columns if c.startswith("BPXSY")]
        dbp_cols = [c for c in bpx.columns if c.startswith("BPXDI")]
        if sbp_cols and dbp_cols:
            bp = bpx[["SEQN"] + sbp_cols + dbp_cols].copy()
            bp["SEQN"] = bp["SEQN"].astype(int)
            # Treat 0 as missing (NHANES uses 0 for excluded readings)
            bp[sbp_cols + dbp_cols] = bp[sbp_cols + dbp_cols].replace(0, np.nan)
            bp["sbp"] = bp[sbp_cols].mean(axis=1)
            bp["dbp"] = bp[dbp_cols].mean(axis=1)
            df = df.merge(bp[["SEQN", "sbp", "dbp"]], on="SEQN", how="left")
        else:
            df["sbp"] = np.nan
            df["dbp"] = np.nan
    else:
        df["sbp"] = np.nan
        df["dbp"] = np.nan

    # BMI
    if len(bmx) and "BMXBMI" in bmx.columns:
        df = df.merge(bmx[["SEQN", "BMXBMI"]].rename(
            columns={"BMXBMI": "bmi"}), on="SEQN", how="left")
    else:
        df["bmi"] = np.nan

    # Diabetes (composite)
    df_indexed = df.set_index("SEQN")
    diabetes_series = derive_diabetes(diq, ghb, biopro)
    df_indexed["diabetes"] = diabetes_series.reindex(df_indexed.index, fill_value=0)
    df = df_indexed.reset_index()

    # Hypertension (composite)
    sbp_series = df.set_index("SEQN")["sbp"]
    dbp_series = df.set_index("SEQN")["dbp"]
    htn_series = derive_hypertension(bpq, sbp_series, dbp_series)
    df = df.merge(
        htn_series.rename("hypertension").reset_index(),
        on="SEQN", how="left"
    )
    df["hypertension"] = df["hypertension"].fillna(0).astype(int)

    # CHF, stroke, cancer (self-report from MCQ)
    if len(mcq):
        for src, dest in [("MCQ160B", "chf"),
                           ("MCQ160F", "stroke"),
                           ("MCQ220",  "cancer")]:
            if src in mcq.columns:
                m = mcq.set_index(mcq["SEQN"].astype(int))[src]
                df[dest] = df["SEQN"].map(lambda s: int((m.get(s) == 1)))
            else:
                df[dest] = 0
    else:
        df["chf"] = 0
        df["stroke"] = 0
        df["cancer"] = 0

    # SDOH (individual-level — addresses ecological-bias critique)
    if len(fsq):
        # FSDHH: household food security category (1=full, 4=very low)
        if "FSDHH" in fsq.columns:
            f = fsq.set_index(fsq["SEQN"].astype(int))["FSDHH"]
            df["food_security_score"] = df["SEQN"].map(f)
        else:
            df["food_security_score"] = np.nan
    else:
        df["food_security_score"] = np.nan

    if len(hiq):
        # HIQ011: covered by health insurance? 1=yes, 2=no
        if "HIQ011" in hiq.columns:
            h = hiq.set_index(hiq["SEQN"].astype(int))["HIQ011"]
            df["insurance_any"] = df["SEQN"].map(
                lambda s: int(h.get(s) == 1) if s in h.index else np.nan
            )
        else:
            df["insurance_any"] = np.nan
        # HIQ031A-J: insurance type breakdown (Medicaid/Medicare/private/etc.)
        for src, dest in [("HIQ031A", "insurance_private"),
                           ("HIQ031B", "insurance_medicare"),
                           ("HIQ031D", "insurance_medicaid")]:
            if src in hiq.columns:
                v = hiq.set_index(hiq["SEQN"].astype(int))[src]
                df[dest] = df["SEQN"].map(
                    lambda s: int(v.get(s) == 14)
                    if s in v.index and pd.notna(v.get(s)) else 0
                )
            else:
                df[dest] = 0
    else:
        df["insurance_any"] = np.nan
        df["insurance_private"] = 0
        df["insurance_medicare"] = 0
        df["insurance_medicaid"] = 0

    if len(ocq):
        # OCQ150: type of work, used to derive employment status
        if "OCQ150" in ocq.columns:
            o = ocq.set_index(ocq["SEQN"].astype(int))["OCQ150"]
            df["employed"] = df["SEQN"].map(
                lambda s: int(o.get(s) in [1, 2])
                if s in o.index and pd.notna(o.get(s)) else np.nan
            )
        else:
            df["employed"] = np.nan
    else:
        df["employed"] = np.nan

    if len(hoq):
        # HOQ065: home owned/rented (1=owned, 2=rented, 3=other)
        if "HOQ065" in hoq.columns:
            h = hoq.set_index(hoq["SEQN"].astype(int))["HOQ065"]
            df["home_owned"] = df["SEQN"].map(
                lambda s: int(h.get(s) == 1)
                if s in h.index and pd.notna(h.get(s)) else np.nan
            )
        else:
            df["home_owned"] = np.nan
    else:
        df["home_owned"] = np.nan

    return df


# ── Cohort filtering with audit trail ────────────────────────────────────
def filter_cohort(df):
    """
    Apply cohort inclusion/exclusion criteria with an audit trail of drop counts.
    Returns (filtered_df, audit_log).
    """
    log = []
    log.append(("Total NHANES participants (all cycles)", len(df)))

    # Adults aged 20+
    df = df[df["age"] >= 20]
    log.append(("After age ≥ 20", len(df)))

    # Has eGFR
    df = df[df["egfr"].notna()]
    log.append(("After non-missing eGFR", len(df)))

    # Stage 2-3 CKD
    # Stage 2: eGFR 60-89 + UACR ≥30 (proteinuria-defined)
    # Stage 3: eGFR 30-59
    is_stage2 = (df["egfr"] >= 60) & (df["egfr"] < 90) & (df["uacr"] >= 30)
    is_stage3 = (df["egfr"] >= 30) & (df["egfr"] < 60)
    df = df[is_stage2 | is_stage3].copy()
    df["ckd_stage"] = np.where(
        df["egfr"] < 45, "Stage_3b",
        np.where(df["egfr"] < 60, "Stage_3a", "Stage_2"),
    )
    log.append(("After Stage 2-3 CKD definition", len(df)))

    return df, log


# ── Mortality merge ──────────────────────────────────────────────────────
def merge_mortality(cohort_df):
    """Merge mortality data from all cycles. Disambiguate SEQN across cycles."""
    mort_all = []
    for cycle, _ in CYCLES:
        m = load_mortality(cycle)
        if len(m):
            m["cycle"] = cycle
            mort_all.append(m)
    if not mort_all:
        print("  [WARN] no mortality files found")
        return cohort_df
    mort = pd.concat(mort_all, ignore_index=True)
    print(f"  Mortality records loaded: {len(mort):,}")
    cohort_df = cohort_df.merge(
        mort[["SEQN", "cycle", "ELIGSTAT", "MORTSTAT",
              "UCOD_LEADING", "PERMTH_INT", "PERMTH_EXM"]],
        on=["SEQN", "cycle"], how="left",
    )
    return cohort_df


# ── Outcome derivation ───────────────────────────────────────────────────
def derive_outcomes(df):
    """
    Define outcomes from mortality data:
      • mort_5yr: 1 if MORTSTAT==1 AND PERMTH_INT ≤ 60 months (5 years).
      • mort_ckd_5yr: 1 if mort_5yr AND UCOD_LEADING == "010" (kidney disease
        nephritis / nephrotic syndrome / nephrosis).
      • follow_up_months: PERMTH_INT, capped at the censoring date.

    Eligibility for analysis: ELIGSTAT == 1 (eligible for follow-up).
    """
    df = df[df["ELIGSTAT"] == 1].copy()
    df["mort_5yr"] = (
        (df["MORTSTAT"] == 1) & (df["PERMTH_INT"] <= 60)
    ).astype(int)
    df["mort_ckd_5yr"] = (
        (df["mort_5yr"] == 1) & (df["UCOD_LEADING"].astype(str).str.strip() == "010")
    ).astype(int)
    df["follow_up_months"] = df["PERMTH_INT"]
    return df


# ── Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("SDOH-CKDPred — Step 2: Assembling NHANES Analytic Cohort")
    print("=" * 64)

    # 1. Per-cycle assembly
    cycle_dfs = []
    for cycle_label, suffix in CYCLES:
        d = assemble_cycle(cycle_label, suffix)
        if len(d):
            cycle_dfs.append(d)
    if not cycle_dfs:
        print("\n[ERROR] no NHANES data found — run step1_download_nhanes.py first.")
        sys.exit(1)
    df_all = pd.concat(cycle_dfs, ignore_index=True)
    print(f"\n  Combined across cycles: {len(df_all):,} participants")

    # 2. Cohort filtering with audit trail
    print("\n  Applying cohort inclusion/exclusion criteria:")
    df_cohort, audit = filter_cohort(df_all)
    for label, n in audit:
        print(f"    {label:<45s}  N = {n:>7,}")

    # 3. Mortality merge
    print("\n  Merging NCHS Linked Mortality File...")
    df_cohort = merge_mortality(df_cohort)

    # 4. Outcome derivation
    print("\n  Deriving outcomes...")
    df_final = derive_outcomes(df_cohort)
    print(f"    Eligible for follow-up:        N = {len(df_final):>7,}")
    print(f"    5-year all-cause mortality:    N = {df_final['mort_5yr'].sum():>7,}  "
          f"({df_final['mort_5yr'].mean()*100:.1f}%)")
    print(f"    5-year CKD-cause mortality:    N = {df_final['mort_ckd_5yr'].sum():>7,}  "
          f"({df_final['mort_ckd_5yr'].mean()*100:.2f}%)")

    # 5. Save
    out_path = os.path.join(PROC_DIR, "nhanes_cohort.csv")
    df_final.to_csv(out_path, index=False)
    print(f"\n  Saved cohort to {out_path}")

    # 6. Save audit log
    audit_path = os.path.join(PROC_DIR, "nhanes_cohort_summary.txt")
    with open(audit_path, "w") as f:
        f.write("NHANES analytic cohort flow\n")
        f.write("=" * 50 + "\n\n")
        for label, n in audit:
            f.write(f"  {label:<45s}  N = {n:>7,}\n")
        f.write(f"\n  Eligible for mortality follow-up:  N = {len(df_final):>7,}\n")
        f.write(f"  5-year all-cause mortality events:   N = {df_final['mort_5yr'].sum():>7,}\n")
        f.write(f"  5-year CKD-cause mortality events:    N = {df_final['mort_ckd_5yr'].sum():>7,}\n")
    print(f"  Audit log saved to {audit_path}")

    print("\n" + "=" * 64)
    print("Step 2 complete.")
    print("Next: python ckd_pipeline/step3_train_model.py")
    print("=" * 64)
