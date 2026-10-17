# JMIR Public Health & Surveillance: Response to Editorial Decision (Major Revision)

**Manuscript:** An Open Two-Stage Surveillance and Risk-Stratification Pipeline for Chronic Kidney Disease (v5) → retitled in v6 as *Neighborhood Deprivation and Undetected Chronic Kidney Disease Burden: Open Small-Area Surveillance and Non-Laboratory Screening Triage Using CDC PLACES and NHANES*

**Decision:** D / major revision. The editor states that the analysis is not rigorous enough, that there are methodological weaknesses, and that there are major reporting issues.

**Files in this folder**

| File | Purpose |
|---|---|
| `CKD_Paper_JMIR_PHS_v6_revised.docx` | Clean revised manuscript (upload as "Revised Ms") |
| `CKD_Paper_JMIR_PHS_v6_revised_highlighted.docx` | Same manuscript with new or changed text highlighted in yellow (upload as a supplementary file, as JMIR requests) |
| `CKD_Paper_JMIR_PHS_v6_revised.md` | Source of the manuscript; rebuild both .docx files with `python src/build_v6_docx.py` |
| `CKD_Paper_JMIR_PHS_v5_revised.docx` | Previous version, unchanged |
| `JMIR_PHS_v6_Editorial_Response.md` | This document: every editorial comment, our response, and remaining author actions |
| `JMIR_PHS_v6_Response_to_Reviewer_AS.md` | Point-by-point response to Reviewer AS (10 minor comments) |

---

## Part A. Point-by-point response to the editorial comments

Each row gives the editor's comment, the change made in v6, and a draft reply for the response letter.

### A1. General: "The analysis is not rigorous enough", "methodological weaknesses", "major reporting issues"

**What we changed.** We re-ran the Stage 2 analysis from the raw NHANES files and replaced every reported Stage 2 number with output produced by code in the repository. Part B documents the full extent of this. The main rigor upgrades are:

1. **Design-based uncertainty.** All 95% CIs now come from a Rao–Wu rescaled bootstrap (1,000 replicates) that resamples NHANES primary sampling units within masked variance strata. This replaces v5's description of resampling individuals with probability proportional to weight, which ignored clustering and stratification. It also resolves the v5 limitation about "Taylor-linearization future work".
2. **Calibration assessed properly.** We report the logistic calibration slope and calibration-in-the-large (Van Calster et al, BMC Med 2019). A bug in the decile-calibration routine that inflated the v5 slope is fixed (see B2).
3. **Honest comparator.** Logistic regression on the identical features and folds, with a paired design-based difference in AUROC and DeLong's test.
4. **Equity analysis by social risk.** Performance by income-to-poverty ratio was added, and a race-free sensitivity model quantifies dependence on race/ethnicity.
5. **Reporting.** Table 2 now reports estimates with 95% CIs; it no longer gives a per-fold range in parentheses where readers expect a CI. Table headers were fixed (the "Unnamed: 0" artifacts), and figure captions now match the numbers in the figures.

**Draft reply:** *We thank the editor for this assessment and have substantially strengthened the analysis. All Stage 2 confidence intervals are now design-based, estimated with a Rao–Wu rescaled bootstrap over NHANES primary sampling units within strata. Calibration is assessed with the logistic calibration slope and calibration-in-the-large. A logistic regression comparator is evaluated on identical folds with a paired test, and equity is assessed across age, sex, race/ethnicity, and income groups, with a race-free sensitivity model. All results were regenerated from the public raw data with code released in the project repository. In doing so we identified and corrected several errors in the previous version, which we list transparently in our response (see below).*

### A2. "The introduction has too much study methods and not enough about what the public health importance is of the study questions. The contribution list is mostly methodological."

**What we changed.** We rewrote the Introduction around two public health problems:

- **Undetected CKD.** Up to 9 in 10 adults with CKD are unaware of it (CDC 2023). Testing is cheap, so the bottleneck is deciding where and in whom to test.
- **A surveillance gap.** CDC PLACES discontinued its tract-level CKD measure in the 2024 release, so agencies lose their small-area CKD map. This is verified in the CDC PLACES release notes and FAQ.

The methods-heavy paragraph on two-stage models in environmental and infectious-disease surveillance (measles, dengue, West Nile) was removed. The numbered contribution list (seed, Makefile, and so on) was removed and replaced by two public health research questions.

**Draft reply:** *We have rewritten the Introduction to lead with the public health problem: most US adults with CKD are undiagnosed, testing is inexpensive, and the constraint is deciding where and in whom to offer it, a decision made harder by CDC PLACES discontinuing its tract-level CKD measure in 2024. The methodological contribution list has been replaced by two public health research questions, and methodological detail has been moved to the Methods.*

### A3. "If this is mainly about use of new methods to answer similar questions to the other research noted at the beginning of the introduction, then the impact of this paper may be minimal."

**What we changed.** The Introduction now states the gap the paper fills, which is not a methods gap:

1. A transparent way for agencies to keep ranking neighborhoods by CKD burden after the PLACES discontinuation.
2. A non-laboratory triage score that, unlike SCORED (2007) and Kshirsagar (2008), targets the current KDIGO 2024 definition (including albuminuria), uses the race-free eGFR equation and contemporary NHANES data, requires no laboratory inputs (SCORED needs proteinuria and anemia), and reports calibration and equity across income and race/ethnicity groups.

**Draft reply:** *We agree the framing over-emphasized methods. The revised paper addresses two applied questions that existing work does not answer: how agencies can continue neighborhood-level CKD prioritization now that federal tract-level CKD estimates have been discontinued, and how well a contemporary, laboratory-free triage score performs, in calibration and across social-risk groups, against the current KDIGO definition of CKD. Comparison with existing questionnaire scores (SCORED, Kshirsagar) is now explicit in the Introduction and Discussion.*

### A4. "Ethical research statements are missing…" and the required Ethical Considerations subsection (4 points)

**What we changed.** We added a **Methods › Ethical Considerations** subsection covering all 4 JMIR points:

| JMIR point | Statement in v6 |
|---|---|
| Ethics committee and number, or justification for exemption | NHANES approved by the NCHS Research Ethics Review Board: Protocol #2011-17 (before Oct 26, 2017), #2018-01 (Oct 26, 2017–Mar 2020), #2021-05 (2021–2023). These numbers were verified on the CDC NHANES ERB page. Our secondary analysis of public deidentified data is not human subjects research under 45 CFR 46.102(e)(1), so IRB review was not sought. |
| Informed consent | NHANES participants gave written informed consent under the NCHS protocols; no additional consent was applicable. |
| Privacy and confidentiality | Public-use files are deidentified through NCHS disclosure review; no linkage or geographic re-identification was attempted; ADI is area-level only and is not redistributed. |
| Compensation | NHANES participants received NCHS remuneration; none was provided in this secondary analysis. |

**Author action:** If either author's institution has a policy or a determination letter for analyses of public data, cite it here. JMIR asks for "citation of relevant institutional or local policies".

**Draft reply:** *We have added an Ethical Considerations subsection to the Methods. It reports the NCHS Research Ethics Review Board protocol numbers under which NHANES data were collected, original informed consent, privacy and deidentification safeguards, and participant remuneration, and it explains, with reference to 45 CFR 46.102(e)(1), why this secondary analysis of public, deidentified data did not require further IRB review.*

### A5. "It is not clear how the ecologic model and patient-level classifier results align with other prior research evidence or whether this study's findings constitute new information about risk assessment."

**What we changed.** We added a **Discussion › Comparison With Prior Work** subsection. It makes three points:

- **Alignment.** The 1.6-fold tract deprivation gradient falls within the 1.5–2.0-fold gradients in Vart 2015, Crews 2014, and Nicholas 2015. The individual income gradient (16.3% vs 10.6%) agrees with them.
- **New information.** The study quantifies how much of the national small-area CKD map deprivation recovers (44%) and how well that transfers between regions (poorly in the Northeast and West).
- **Patient-level comparison.** We compare the classifier with SCORED: AUROC 0.88 in development and 0.71 on external validation, with an eGFR-only outcome, a race-based equation, and laboratory inputs. ML equalling logistic regression is consistent with Christodoulou 2019.

We also state clearly which findings confirm prior evidence and which are new.

**Draft reply:** *We have added a "Comparison With Prior Work" subsection. The ecological deprivation gradient (1.6-fold) and the individual income gradient agree with prior meta-analytic evidence, supporting validity. The new information is the quantification of how much of the national small-area CKD distribution deprivation recovers and how this varies by region, and a contemporary non-laboratory triage score benchmarked against SCORED, with calibration and equity reporting.*

### A6. "The list-based approach for limitations and future directions is not appropriate for JPH."

**What we changed.** The 8 numbered limitations and 7 numbered future directions were rewritten as narrative paragraphs grouped by theme: outcome validity, ecological design and linkage, cross-sectional data and generalizability, and data access. As a side effect, this also fixed a numbering bug: v5's future-directions list started at "9".

### A7. "The authors should define what they mean by 'social risk' and how their models are used to determine this."

**What we changed.**

- **Definition.** In the Introduction we define social risk following Alderwick & Gottlieb, Milbank Q 2019;97(2):407-419 (PMID 31069864): adverse social conditions associated with poor health, as distinct from social needs.
- **Operationalization.** Area-level social risk is the ADI (17 ACS indicators of income, education, employment, and housing), used in Stage 1. Individual-level social risk is the family income-to-poverty ratio, used in Stage 2.
- **How the models use it.** Stage 1 ranks places by deprivation-predicted burden. Stage 2 includes PIR as a predictor. A new analysis shows performance and calibration across PIR <1.3, 1.3–3.49, and ≥3.5 (Figure 11; Results).
- **Clarification.** The models do not determine social risk; they use social-risk measures to direct testing. The Public Health Implications subsection says so explicitly.

### A8. "There is no conclusions section."

A **Conclusions** section has been added.

### A9. "Please minimize bullet points throughout the manuscript, and rewrite it in a more narrative way."

v6 contains **no bullet or numbered lists**. This was checked in the generated .docx, which has 0 list-style paragraphs. The Reproducibility Statement, Supplementary Materials list, Limitations, and Future Directions are now narrative.

### A10. Data Availability

We added a **Data Availability** section. It gives the URLs for NHANES and CDC PLACES (dataset shc3-fzig). It explains that the Neighborhood Atlas ADI requires free registration and a data use agreement, so it cannot be redistributed and users must download it directly. It also gives the code, download scripts, and derived tables (participant-level predictions are regenerated by the scripts) at github.com/sanjoyp158-sri/sdoh_ckd_pred, with a Zenodo DOI to follow on acceptance.

**Author action:** Push the new code to that repository (see Part C). Make sure the repository URL you cite is the one that contains this revision; the local repo pushes to `ajitbubu/sdoh_ckd_pred`, with `sanjoyp158-sri` as upstream.

### A11. Conflict of Interest

Added: "AS is employed by DataSafeguard.ai. DataSafeguard.ai did not fund this work and has no commercial product based on it. SM declares no conflicts of interest."

**Resolved:** Confirmed by the authors: SM declares no conflicts of interest.

### A12. Author Contributions (CRediT)

Added a draft:

- **AS:** Conceptualization, Methodology, Software, Formal analysis, Visualization, Writing – original draft, Writing – review & editing.
- **SM:** Software, Data curation, Validation, Writing – review & editing.

**Resolved:** Roles confirmed as drafted. SM's affiliation is "Independent Researcher, United States".

### A13. Funding Statement (required)

Added, as a section separate from the Acknowledgments: "The authors declared no financial support was received for this work."

### A14. Generative AI disclosure (required)

Added a **Use of Generative AI** section. It discloses that Claude (Anthropic) was used for code, drafting and editing, and checking values, and that the authors verified all content and take responsibility for it.

**Important:** an earlier draft (`_ms_plain.md`, Acknowledgments) attested that "no generative AI tools were used". If any earlier submission or cover letter carried that attestation, correct it explicitly in the response letter.

**Draft reply:** *We have added a generative AI statement to the manuscript. We note that a previous version stated that no generative AI tools were used; this was incorrect, and the new statement accurately describes the use of Claude (Anthropic) for code development and manuscript drafting and editing, all of which the authors verified.*

### A15. Journal transfer preferences

**Resolved:** Transfer preferences, in order: (1) Interactive Journal of Medical Research (i-JMR), (2) JMIR AI. These are stated in the response letter (`JMIR_PHS_v6_Response_Letter.md`).

### A16. Tracked or highlighted version, and JMIR style

`CKD_Paper_JMIR_PHS_v6_revised_highlighted.docx` highlights every paragraph or table cell that does not appear (≥90% similar) in v5. That is 283 of 331 paragraphs, reflecting the scope of the rewrite. In the response letter, state that the manuscript was substantially rewritten, so most text is highlighted.

Formatting already applied: headings follow JMIR (Introduction, Methods, Results, Discussion, Conclusions), the structured abstract uses Background/Objective/Methods/Results/Conclusions, Vancouver numbered references are ordered by first appearance with ranges as [3-5], an Abbreviations section is included, and supplementary tables are in Multimedia Appendix 1. The main text is about 4,500 words (abstract about 430 words).

**Author action:** Split Multimedia Appendix 1 into a separate file if JMIR requires it on upload.

---

## Part B. Errors found in v5 during re-analysis (must be disclosed)

Re-running the pipeline showed that a number of v5 results were **not produced by any code in the repository**, or **contradicted the outputs or figures**. All are corrected in v6. We recommend disclosing them briefly in the response letter (a draft paragraph is at the end of this part); undisclosed changes to headline results would be a bigger problem if found later.

### B1. Analyses reported in v5 with no supporting code (Stage 2: now actually run)

| v5 claim | Actual result (v6) | Source |
|---|---|---|
| XGBoost beat logistic regression by 0.017 AUROC; DeLong z = 2.91, P=.004 | **No advantage.** LR AUROC 0.778 vs XGBoost 0.772; difference −0.006 (95% CI −0.013 to 0.002); bootstrap P=.11; DeLong P=.59 | `outputs/stage2_comparator_lr.json` |
| Bootstrap 95% CI for AUROC 0.756–0.789, AUPRC 0.371–0.438, Brier 0.098–0.106, sensitivity 41.2–49.8% | AUROC 0.772 (0.758–0.787); AUPRC 0.402 (0.374–0.433); Brier 0.102 (0.096–0.109); sensitivity 44.9% (41.7–48.2%), all design-based | `outputs/stage2_metrics_ci.json` |
| Missingness highest for blood pressure (9.4%) | **Income-to-poverty ratio 13.5%**; blood pressure 7.3% | `outputs/tableS3_missingness.csv` |
| MI changed AUROC by <0.001 | +0.001 (0.772 → 0.774) | `outputs/stage2_mi_sensitivity.json` |
| At 70% specificity, sensitivity 70.4% (threshold 0.139) | 72.1% (threshold 0.098) | `outputs/tableS4_operating_points.csv` |

### B2. Stage 2 calibration was wrong because of a bug

`calibration_deciles()` in `src/train_nhanes_model.py` placed a bin edge at the maximum predicted value, which split the single highest-risk participant into a spurious 11th "decile" (n=1, observed=1.0). An unweighted regression across bins then pulled the slope toward 1.

| Measure | v5 (bug) | v6 (fixed) |
|---|---|---|
| Decile calibration slope | 0.955 ("acceptable") | **0.815** (95% CI 0.766–0.867) |
| Logistic calibration slope | not reported | **0.751** (0.703–0.803) |

The model is **overconfident at high risk**: the top decile predicts 0.56 against 0.46 observed. The paper now says so and recommends recalibration before deployment.

### B3. Stage 1 text contradicted Stage 1 figures

The Stage 1 figures embedded in v5 (whose internal table says `ADI source: real_neighborhood_atlas`) were initially taken as the record of the real-ADI run. The v5 text disagreed with them.

**Update: Stage 1 has now been re-run** from the committed code with the Neighborhood Atlas v4.0.1 block-group file. The rerun reproduces the v5 figures to within rounding, and the manuscript, Figures 1–7, and both response documents now use the rerun values. The final column below gives the rerun values.

| Item | v5 text | v5 figures | v6 (rerun, final) |
|---|---|---|---|
| Tracts | 60,445 | 60,945 | **60,945** |
| Cross-validated R² | 0.450 ± 0.006 | 0.444 ± 0.009 | **0.445 ± 0.008** |
| MAE | 0.447 | 0.452 | **0.452** |
| Calibration slope / intercept | 0.97 / 0.04 | 0.997 / 0.009 | **0.998 / 0.007** |
| Leave-one-region-out R² | 0.239 (West) to 0.415 | 0.232 (Northeast) to 0.415; West 0.247 | **0.232 (Northeast) to 0.416; West 0.251** |
| Capacity sweep | R² varies <0.005 | 0.439–0.445 | **0.440–0.445** |
| ADI quintile gradient | ~2.6% → ~3.4% | ~2.45% → ~3.90% | **2.45, 2.60, 2.83, 3.20, 3.90% (1.6×)** |
| Spearman ρ | 0.71 | not shown | **0.675** |
| Feature importance | quintile ≈ national rank | quintile 17.6, natrank 17.4 | **natrank 21.4, quintile 10.9** (quintile is derived from national rank, so the split is arbitrary) |
| RMSE 0.628 | stated | not shown | 0.63 (not reported in v6) |

### B4. Stage 1 analyses claimed in v5 that do not exist (removed from v6)

None of the following has code in the repository, so all were removed:

- The crosswalk boundary-misalignment analysis (~12,400 tracts recovered, ΔR² <0.01, KS P=.18): Supplementary Table S1.
- The three feature ablations (R² 0.468 / 0.472 / 0.488): Supplementary Table S2.
- Spearman ρ = 0.71. Now computed by code: ρ = 0.675 (reported in v6).
- "28% of ADI tracts failed the join". **Verified by the rerun** (24,450 of 85,395 = 28.6%) and restored in v6, together with the 16% figure for PLACES (72,337 − 60,945 = 11,392 = 15.7%).
- "Population-weighted mean" aggregation: the code uses an **unweighted** mean, and v6 describes it accurately.

If you want any of these analyses back, they must be implemented and run first. The crosswalk analysis is mentioned in v6 only as a suggested next step in the Limitations.

### B5. Other unsupported statements (removed)

- "A prospective evaluation in partnership with a state health department is in progress; the protocol is Supplementary Material S5." No protocol exists in the repository. Removed from the Abstract, the Discussion, and the supplementary list.
- "We have added an archival snapshot of the PLACES 2022 file (with CDC permission) to the project repository." No such file exists. Replaced by `src/fetch_places.py`, which downloads the public dataset (shc3-fzig, verified: 72,337 tracts, range 0.5–14.4%, mean 2.96%).
- "The Stage 2 model uses race as a stratification variable … but not as a model predictor" (v5 §4.6). **False:** `race_eth` is in `FEATURES`. v6 states that race/ethnicity is a predictor and adds a race-free sensitivity model (AUROC 0.766 vs 0.772; Table S3).
- "Race/ethnicity AUROC uniformly above 0.70 across all five reported categories". There are 6 categories, and Mexican American AUROC is 0.6997.
- "Male AUROC > Female by ≈0.02". The actual difference is **0.07** (0.807 vs 0.735).
- §4.3: "slopes below 1.0 indicate the model under-predicts". Wrong interpretation: a slope below 1 means the predictions are too spread out (over-predicting high, under-predicting low). Corrected.
- References to `Makefile`, `src/data_processing/fetch_*.py`, and `src/rewrite_white_paper.py`: none exist. The Reproducibility section now lists the real scripts.

### B6. Small shift in Stage 2 point estimates

Re-running the unchanged training script with the versions stated in the paper (Python 3.11, XGBoost 3.2.0, scikit-learn 1.8.0, pandas 3.0.6) reproduces the cohort **exactly**: n=15,150, 2,706 events, 13.93% weighted prevalence, and Table 1 identical. Model metrics shift slightly, presumably because of build or platform differences in XGBoost: AUROC 0.7733 → 0.7724, sensitivity 45.4% → 44.9%, threshold 0.288 → 0.291. The run is deterministic on this machine. v6 reports the regenerated values, and Figures 8–13 were regenerated to match.

**Draft disclosure paragraph for the response letter:**

*In re-running the full pipeline from the public raw data to address the editor's concerns about rigor, we identified errors in the previous version, which we have corrected:*

1. *The previously reported advantage of XGBoost over logistic regression was not supported; on identical folds the two models do not differ (AUROC 0.772 vs 0.778).*
2. *A binning error in our calibration routine overstated calibration; the corrected logistic calibration slope is 0.75, which we now report and discuss.*
3. *Several Stage 1 values in the text did not match the figures generated from the real ADI data and have been aligned with them.*
4. *Supplementary analyses we described but had not completed (Census-crosswalk sensitivity, feature ablations) and a reference to a prospective protocol have been removed.*

*All numbers in the revised manuscript are produced by code in the public repository.*

---

## Part C. Remaining author actions before resubmission

1. ~~Re-run Stage 1 with the real ADI file.~~ **Done.** It was re-run with Neighborhood Atlas v4.0.1 (`data/raw/adi_2020_national_blockgroup.csv`, copied to `ckd_pipeline/data/raw/`; both locations are gitignored, as the data use agreement requires). Figures 1–7 were regenerated, and the manuscript was updated with the rerun values.
2. **Confirm** SM's affiliation, COI, and CRediT roles (A11, A12), and any institutional policy citation for the ethics exemption (A4).
3. **Transfer preferences** (A15).
4. **Correct the earlier "no generative AI" attestation** in the response letter (A14).
5. **Commit and push** the code changes to the repository cited in Data Availability.
6. **Upload** the clean .docx as "Revised Ms" and the highlighted .docx as a supplementary file, with a response letter built from Parts A and B.
7. **Read the whole manuscript carefully.** The v6 text was substantially rewritten; the authors are responsible for every claim.

---

## Part D. Code changes made for this revision

| File | Change |
|---|---|
| `src/fetch_nhanes.py` (new) | Downloads the 18 NHANES XPT files (P_ 2017–2020, _L 2021–2023) from CDC; the repository previously had no downloader for these cycles |
| `src/fetch_places.py` (new) | Downloads CDC PLACES 2022 tract data (shc3-fzig) |
| `src/stage2_supplementary.py` (new) | Rao–Wu design-based bootstrap CIs; logistic calibration slope and calibration-in-the-large; subgroup AUROC CIs (age, sex, race/ethnicity, PIR); LR comparator with paired ΔAUROC and DeLong; missingness table and MI (m=5) within folds; operating-point table; race-free sensitivity model |
| `src/train_nhanes_model.py` | Fixed the decile-calibration bug (spurious 1-person 11th bin) |
| `src/generate_stage2_figures.py` | Uses design-based CIs (Figures 8, 10, 11, 13; Table 2); Figure 11 adds PIR groups and uses the shared design-based CIs (previously 500 iid resamples, while v5 claimed 1,000); fixed "95% per-fold range" mislabel; fixed "Unnamed: 0" table headers; removed the now-unused `subset_by_label` |
| `src/train_ecological_model.py` | Real-ADI loader now coerces Neighborhood Atlas suppression codes (GQ, PH, …) to missing and derives the quintile from the national rank when the file has no quintile column; previously it would fail on the public file |
| `src/build_v6_docx.py` (new) | Builds the clean and highlighted .docx from the Markdown source, numbering citations by first appearance |
| `figures_phs/fig01–07`, `ckd_pipeline/outputs/stage1_*` | Regenerated from the real-ADI rerun (previously placeholder renders). The temporary `stage1_real_adi/` copies taken from the v5 .docx were removed |

**Reproducing Stage 2 (verified):**

```bash
python src/fetch_nhanes.py
python src/train_nhanes_model.py
python src/stage2_supplementary.py
python src/generate_stage2_figures.py
python src/build_v6_docx.py
```

On macOS with pip-installed XGBoost, if `libomp` is missing either `brew install libomp`, or set `DYLD_LIBRARY_PATH` to scikit-learn's bundled `sklearn/.dylibs`.
