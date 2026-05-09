"""
step1_download_nhanes.py
------------------------
Downloads NHANES public-use data files and the NCHS Public-use Linked Mortality
File for cycles 2003-2018 (eight 2-year cycles, suffix C through J).

This replaces the synthetic-data pipeline. All cohort definition, feature
engineering, and outcome assignment happens downstream against real,
publicly-released NHANES data — no probabilistic label assignment, no
parameter-tuned synthetic generator. The reviewer's tautology critique is
addressed at the data layer.

Outputs:
  data/raw/nhanes/<cycle>/<file>.xpt    e.g. 2017-2018/DEMO_J.xpt
  data/raw/nhanes/mortality/<cycle>.dat e.g. mortality/2017-2018.dat

Run from project root:
  python ckd_pipeline/step1_download_nhanes.py

Idempotent — files already present on disk are skipped.
"""

import os
import sys
import time
import urllib.request
import urllib.error

# ── Paths (independent of legacy config.py) ───────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RAW_DIR     = os.path.join(BASE_DIR, "data", "raw")
NHANES_DIR  = os.path.join(RAW_DIR, "nhanes")
MORT_DIR    = os.path.join(NHANES_DIR, "mortality")
os.makedirs(NHANES_DIR, exist_ok=True)
os.makedirs(MORT_DIR, exist_ok=True)


# ── NHANES cycles and their suffix codes ──────────────────────────────────
# NHANES file naming convention: each 2-year cycle gets a single-letter suffix.
# C=2003-04, D=2005-06, E=2007-08, F=2009-10, G=2011-12, H=2013-14,
# I=2015-16, J=2017-18.
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


# ── Files we need per cycle ───────────────────────────────────────────────
# Each entry is the file stem (the cycle suffix is appended later).
# Categories listed for reference; the code just iterates the names.
#
# Demographics:        DEMO     — age, sex, race/ethnicity, education,
#                                 poverty income ratio, language
# Biochem:             BIOPRO   — serum creatinine (for eGFR via CKD-EPI 2021)
# Albumin/creatinine:  ALB_CR   — UACR (urine albumin-creatinine ratio)
# Glycohemoglobin:     GHB      — HbA1c
# Blood pressure:      BPX      — systolic/diastolic, multiple readings
# Body measures:       BMX      — height, weight, BMI, waist circumference
# Cholesterol total:   TCHOL    — total cholesterol
# Cholesterol HDL:     HDL      — HDL cholesterol
#
# Comorbidity questionnaires:
# Diabetes:            DIQ      — diabetes diagnosis, age at dx, treatment
# Blood pressure Q:    BPQ      — hypertension diagnosis, medication
# Medical conditions:  MCQ      — heart disease, stroke, cancer, etc.
# Kidney conditions:   KIQ_U    — self-reported kidney conditions
# Hospital utilization:HUQ      — recent hospitalizations
#
# Medications:
# Prescription drugs:  RXQ_RX   — current prescription medications
#
# SDOH (individual level — addresses ecological-bias critique):
# Income:              INQ      — poverty income ratio, family income
# Food security:       FSQ      — household food security questionnaire
# Insurance:           HIQ      — insurance type and coverage
# Housing:             HOQ      — housing characteristics
# Occupation:          OCQ      — employment status
NHANES_FILES = [
    "DEMO",
    "BIOPRO",
    "ALB_CR",
    "GHB",
    "BPX",
    "BMX",
    "TCHOL",
    "HDL",
    "DIQ",
    "BPQ",
    "MCQ",
    "KIQ_U",
    "HUQ",
    "RXQ_RX",
    "INQ",
    "FSQ",
    "HIQ",
    "HOQ",
    "OCQ",
]


# ── NHANES download URL pattern ───────────────────────────────────────────
# Verified working pattern (April 2026):
#   https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/<year_start>/DataFiles/<STEM>_<SUFFIX>.xpt
# Note: case matters — files served as .xpt (lowercase) at this path.
NHANES_URL_TMPL = (
    "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/"
    "{year_start}/DataFiles/{stem}_{suffix}.xpt"
)


# ── NCHS Linked Mortality File URL pattern ────────────────────────────────
# Public-use mortality file (follow-up through Dec 31, 2019):
#   https://ftp.cdc.gov/pub/HEALTH_STATISTICS/NCHS/datalinkage/linked_mortality/
#       NHANES_<YYYY>_<YYYY>_MORT_2019_PUBLIC.dat
# The .dat is fixed-width text. Column specs are documented at:
#   https://www.cdc.gov/nchs/data-linkage/mortality-public.htm
MORT_URL_TMPL = (
    "https://ftp.cdc.gov/pub/HEALTH_STATISTICS/NCHS/datalinkage/"
    "linked_mortality/NHANES_{cycle_start}_{cycle_end}_MORT_2019_PUBLIC.dat"
)


# ── Download helper ───────────────────────────────────────────────────────
def download(url, dest_path, label, max_retries=3):
    """
    Download a single file with retries. Idempotent: skips if file already
    exists with a non-zero, plausible size.
    """
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024:
        print(f"  [SKIP] {label}  ({os.path.getsize(dest_path):,} bytes already present)")
        return True

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "sdoh-ckd-pred/1.0 (NHANES analysis)"},
    )
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                data = resp.read()
            # Sanity check: a real .xpt or .dat is at least a few KB.
            # CDC returns a 20KB HTML "Page Not Found" for missing files —
            # detect that by looking for an HTML signature.
            if data[:15].lower().startswith(b"<!doctype html") or b"<html" in data[:200].lower():
                print(f"  [MISS] {label}  (server returned HTML — file does not exist for this cycle)")
                return False
            with open(dest_path, "wb") as f:
                f.write(data)
            print(f"  [OK]   {label}  ({len(data):,} bytes)")
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as e:
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  [retry {attempt}/{max_retries} after {wait}s] {label}: {e}")
                time.sleep(wait)
            else:
                print(f"  [FAIL] {label}: {e}")
                return False


# ── NHANES file download per cycle ────────────────────────────────────────
def download_cycle(cycle_label, suffix):
    """Download all required NHANES XPT files for one 2-year cycle."""
    year_start = cycle_label.split("-")[0]
    cycle_dir = os.path.join(NHANES_DIR, cycle_label)
    os.makedirs(cycle_dir, exist_ok=True)

    print(f"\n  Cycle {cycle_label} (suffix {suffix})")
    n_ok = 0
    n_miss = 0
    for stem in NHANES_FILES:
        url = NHANES_URL_TMPL.format(
            year_start=year_start, stem=stem, suffix=suffix
        )
        fname = f"{stem}_{suffix}.xpt"
        dest = os.path.join(cycle_dir, fname)
        result = download(url, dest, fname)
        if result:
            n_ok += 1
        else:
            n_miss += 1
    print(f"    → {n_ok} files downloaded, {n_miss} not available for this cycle")


# ── Linked Mortality File download per cycle ──────────────────────────────
def download_mortality(cycle_label):
    """Download the NCHS Public-use Linked Mortality File for one cycle."""
    cycle_start, cycle_end = cycle_label.split("-")
    url = MORT_URL_TMPL.format(cycle_start=cycle_start, cycle_end=cycle_end)
    fname = f"{cycle_label}.dat"
    dest = os.path.join(MORT_DIR, fname)
    download(url, dest, f"mortality {cycle_label}")


# ── Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 64)
    print("SDOH-CKDPred — Step 1: Downloading NHANES + Linked Mortality")
    print("=" * 64)
    print(f"  Output directory: {NHANES_DIR}")

    print("\n[1/2] NHANES public-use data files (cycles 2003-2018)")
    for cycle_label, suffix in CYCLES:
        download_cycle(cycle_label, suffix)

    print("\n[2/2] NCHS Public-use Linked Mortality File (through Dec 31, 2019)")
    for cycle_label, _ in CYCLES:
        download_mortality(cycle_label)

    print("\n" + "=" * 64)
    print("Step 1 complete.")
    print("Note: some files [MISS] are expected — not every cycle includes")
    print("every supplementary questionnaire (e.g., BIOPRO, INQ are added")
    print("in later cycles). The cohort assembler in step2 handles this.")
    print("Next: python ckd_pipeline/step2_assemble_nhanes_cohort.py")
    print("=" * 64)
