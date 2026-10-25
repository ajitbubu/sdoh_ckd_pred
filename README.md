# SDOH-CKDPred: open CKD small-area surveillance and screening triage

Analysis code for the manuscript "Neighborhood Deprivation and Undetected Chronic Kidney Disease Burden: Open Small-Area Surveillance and Non-Laboratory Screening Triage Using CDC PLACES and NHANES" (JMIR Public Health and Surveillance, manuscript 101575). Every number, table, and figure in the manuscript is produced by the scripts in `src/` from public data.

The study has 2 separate, unlinked analyses:

- **Stage 1 (ecological).** Relates the Neighborhood Atlas Area Deprivation Index (ADI, 2020) to the CDC PLACES 2022 tract-level prevalence of self-reported diagnosed CKD in 60,945 US census tracts (gradient-boosted regression; random, spatially blocked, and leave-one-region-out cross-validation).
- **Stage 2 (individual).** Identifies adults with single-visit laboratory markers of CKD (race-free eGFR <60 mL/min/1.73 m² or UACR ≥30 mg/g) in NHANES 2017–March 2020 and 2021–August 2023 (n=15,150) using only information available without laboratory testing. The primary model is a survey-weighted logistic regression, with coefficients published in `ckd_pipeline/outputs/stage2_lr_coefficients.csv`; XGBoost is the comparator. Confidence intervals use a Rao–Wu bootstrap over NHANES primary sampling units.

Neither model is a medical device. The Stage 2 score prioritizes laboratory testing and does not replace it.

## Data

| Source | How it is obtained | Saved to |
|---|---|---|
| NHANES 2017–March 2020 (P_) and 2021–2023 (_L) public-use files | `python src/fetch_nhanes.py` | `ckd_pipeline/data/raw/nhanes/` |
| CDC PLACES 2022, census tract, GIS-friendly (dataset shc3-fzig) | `python src/fetch_places.py` | `ckd_pipeline/data/raw/cdc_places/` |
| Neighborhood Atlas ADI 2020, national block-group file | Manual download after free registration at https://www.neighborhoodatlas.medicine.wisc.edu/ (data use agreement; not redistributed here) | `ckd_pipeline/data/raw/adi_2020_national_blockgroup.csv` |

The Stage 1 script stops with an error if the ADI file is absent. Synthetic ADI is used only with the explicit testing flag `--allow-placeholder`, and the output file records the source (`adi_source` in `stage1_metrics.json`).

## Reproducing the results

Python 3.11. The XGBoost wheel on macOS needs the OpenMP runtime (`brew install libomp`).

```bash
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/fetch_nhanes.py
.venv/bin/python src/fetch_places.py
# place the ADI block-group file (see Data)
.venv/bin/python src/train_ecological_model.py        # Stage 1
.venv/bin/python src/train_nhanes_model.py            # Stage 2 cohort, primary model, XGBoost comparator
.venv/bin/python src/stage2_supplementary.py          # design-based CIs, calibration, subgroups, sensitivity analyses, coefficients
.venv/bin/python src/stage2_model_comparison.py 1000  # logistic regression vs XGBoost, CV refit in 1,000 bootstrap replicates (about 2 hours)
.venv/bin/python src/generate_ecological_figures.py
.venv/bin/python src/generate_stage2_figures.py
.venv/bin/python src/build_v6_docx.py                 # manuscript and appendices (needs pandoc)
```

All random seeds are 42. Outputs are written to `ckd_pipeline/outputs/`, `figures_phs/`, and `tables_phs/`.

## Repository layout

```
src/                   pipeline scripts (download, Stage 1, Stage 2, figures, manuscript build)
ckd_pipeline/outputs/  metric files cited in the manuscript (Multimedia Appendix 2)
figures_phs/           figures
tables_phs/            tables
docs/                  manuscript source (Markdown), TRIPOD+AI checklist, style reference for the build
```

## Citation

See [CITATION.cff](CITATION.cff). Please also cite the data sources: the Neighborhood Atlas (Kind and Buckingham, N Engl J Med 2018), CDC PLACES, and NHANES.

## License

[AUTHORS: choose a license, e.g., MIT, and add a LICENSE file; the repository currently has none.]
