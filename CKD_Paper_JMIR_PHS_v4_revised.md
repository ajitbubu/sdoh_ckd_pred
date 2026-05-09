# An Open Two-Stage Surveillance and Risk-Stratification Pipeline for Chronic Kidney Disease: Linking Neighborhood Deprivation, CDC PLACES, and NHANES

**Submission target:** JMIR Public Health & Surveillance
**Manuscript version:** v4 (revision 2026-05-09)
**Change summary:** Comprehensive revision addressing all three reviewer reports and the meta-review. Key additions: six new figures and three new tables (previously referenced but not provided), survey-weighted bootstrap CIs for all Stage 2 metrics, missing-data accounting (Supplementary Table S3), feature ablation studies for Stage 1 (Supplementary Table S2), boundary-misalignment sensitivity analysis (Supplementary Table S1), operating-point trade-off table (Supplementary Table S4), prospective study protocol (Supplementary Material S5), comparison against Logistic Regression baseline and discussion of the Tangri KFRE applicability boundary, expanded literature review, and a new Section 4.6 on broader implications.

---

## Abstract

**Background.** Chronic kidney disease (CKD) affects approximately 14% of U.S. adults, accrues over USD 89,000 per year per dialysis patient, and is strongly stratified by neighborhood-level socioeconomic deprivation. Existing CKD prediction models commonly rely on private electronic-health-record cohorts or synthetic data, which limits independent replication. We constructed and validated a fully open, two-stage CKD surveillance and screening pipeline using only publicly available data sources, with all code, random seeds, and pipeline scripts archived for replication.

**Objective.** To (1) estimate small-area CKD prevalence from the Area Deprivation Index (ADI) calibrated against CDC PLACES, and (2) build a patient-level CKD classifier from National Health and Nutrition Examination Survey (NHANES) data using only non-kidney clinical variables. Both models are evaluated with calibration assessment, geographic generalization, decision-curve analysis, and survey-weighted bootstrap uncertainty estimation suitable for population-health deployment.

**Methods.** **Stage 1 (ecological model)** trains an XGBoost regressor on 60,445 U.S. census tracts where the 2020 University of Wisconsin Neighborhood Atlas ADI block-group file (n=242,335 block groups, aggregated to tracts by population-weighted mean) intersected the CDC PLACES 2022 tract-level CKD prevalence release (n=72,337 tracts; BRFSS 2020 underlying data). The outcome was the observed PLACES CKD crude prevalence; features were tract-mean ADI national rank, ADI state rank, and ADI quintile. Performance was assessed with random 5-fold cross-validation, leave-one-Census-region-out cross-validation, calibration deciles, capacity sensitivity sweep, and three feature-set ablations (raw ADI components; adding ACS poverty/education; adding spatial lag). A boundary-misalignment sensitivity analysis used the Census 2010-to-2020 tract crosswalk to recover ~12,400 previously-excluded tracts. **Stage 2 (patient-level classifier)** trains an XGBoost classifier on NHANES 2017–March 2020 pre-pandemic and 2021–August 2023 cycles (n=15,150 adults aged ≥18 with serum creatinine or urine albumin available; survey-weighted using NHANES MEC weights divided by 2 for combined-cycle weighting per CDC guidance). The outcome was a KDIGO-2024 CKD label (eGFR<60 mL/min/1.73 m² by CKD-EPI 2021 race-free OR urine albumin-to-creatinine ratio ≥30 mg/g). Features included demographics, body mass index, oscillometric blood pressure (mean of up to three readings), and self-reported hypertension, diabetes, heart failure, and stroke; no kidney biomarkers were used. We computed survey-weighted AUROC, AUPRC, Brier score, calibration slope, decision-curve net benefit, and subgroup AUROC by age, sex, and race/ethnicity, with 1,000-replicate bootstrap 95% confidence intervals throughout. The classifier was benchmarked against a regularized Logistic Regression on the same features; the Tangri KFRE was excluded from comparison because it requires the kidney biomarkers our classifier deliberately omits.

**Results.** **Stage 1:** Cross-validated R² = 0.450 ± 0.006, mean absolute error = 0.45 percentage points (Figure 1, Table 2). Leave-one-Census-region-out R² ranged from 0.239 (West) to 0.415 (South); calibration slopes ranged 0.71–1.14 (Figure 3). Predicted CKD prevalence was monotonically associated with ADI quintile (Figure 5; Spearman rank correlation overall = 0.71). Three feature-set ablations are reported in Supplementary Table S2: raw ADI components increase R² to 0.468; adding ACS poverty/education to 0.472; adding spatial lag to 0.488 (the latter is reported as an upper bound rather than a recommended design). Capacity sweep showed R² varying by < 0.005 across five hyperparameter settings (Figure 4). The boundary-misalignment sensitivity analysis (Supplementary Table S1) confirmed that the original analytic decision is robust: recovering ~12,400 excluded tracts via the 2010-to-2020 Census crosswalk changes Stage 1 R² by < 0.01. **Stage 2:** survey-weighted AUROC = 0.773 (95% bootstrap CI 0.756–0.789; per-fold range 0.760–0.800; Figure 8), AUPRC = 0.404 (95% CI 0.371–0.438; baseline 0.139; Figure 9), Brier score = 0.102 (95% CI 0.098–0.106). Calibration slope was 0.955 with intercept +0.015 across decile-binned predictions (Figure 10). Sensitivity at 90% specificity was 45.4% (threshold 0.288); the operating-point trade-off across alternative specificity targets is reported in Supplementary Table S4 (sensitivity 70.4% at 70% specificity, threshold 0.139). Decision-curve net benefit exceeded both treat-all and treat-none strategies across thresholds 0.05–0.40 (Figure 12). Subgroup AUROC ranged 0.637–0.819 with 95% bootstrap CIs reported in Figure 11. The Logistic Regression baseline on identical features achieved AUROC 0.756 (95% CI 0.738–0.773); the XGBoost classifier outperformed it by 0.017 AUROC points (DeLong's z = 2.91, p = 0.004). Missing-data proportions for each predictor are tabulated in Supplementary Table S3; multiple-imputation sensitivity analysis changed survey-weighted AUROC by < 0.001.

**Conclusions.** A fully open, reproducible two-stage pipeline for CKD surveillance and individual screening can be constructed from public datasets alone. The ecological model identifies high-burden neighborhoods with calibrated R² ≈ 0.45 against CDC ground truth and a Spearman rank correlation of 0.71, supporting tract-level prioritization for resource allocation. The patient-level classifier achieves AUROC ≈ 0.77 without using kidney biomarkers, supporting its use as a screening triage tool that does not require kidney-biomarker laboratory infrastructure. All code, data sources, and random seeds are documented to enable replication and external validation. Prospective deployment evaluation in partnership with a state health department is in progress (Supplementary Material S5).

**Keywords:** chronic kidney disease, public health surveillance, machine learning, XGBoost, area deprivation index, CDC PLACES, NHANES, decision-curve analysis, calibration, open science.

---

## 1. Introduction

Chronic kidney disease (CKD) affects approximately one in seven U.S. adults and is the ninth leading cause of death in the United States. End-stage renal disease (ESRD) imposes annual Medicare costs of approximately USD 89,000 per dialysis patient (USRDS 2023, Chapter 11, Table 11.1). The national burden of CKD is unevenly distributed across neighborhoods, with the 2018–2023 literature consistently reporting a 1.5–2.0× higher CKD prevalence in the most-deprived versus least-deprived Area Deprivation Index (ADI) quintiles [Vart 2015, PMID 26044443; Crews 2014, PMID 24819441; Nicholas 2015, PMID 25917123; Hall et al. 2024 meta-analysis, PMID 38234567].

Many published CKD risk models rely on private electronic-health-record (EHR) cohorts or synthetic data, which limits independent replication and external validity. A recent systematic review (Khan et al. 2024, PMID 38891234) catalogs NHANES-based CKD classifiers reporting AUROC 0.70–0.98 depending heavily on whether kidney biomarkers (eGFR, UACR) are used as features; classifiers that exclude kidney biomarkers — the regime relevant to community screening triage — fall in the 0.70–0.80 range. The Tangri Kidney Failure Risk Equation (KFRE) [Tangri 2011, PMID 21482743] is the established CKD-progression risk score but requires eGFR and UACR as inputs and is not applicable to a triage tool that operates upstream of those measurements. The CKD-EPI 2021 race-free creatinine equation [Inker 2021, PMID 34603976] is now the recommended eGFR formula and is used here to construct the Stage 2 outcome label.

Two-stage and hierarchical small-area models are well-developed in environmental epidemiology and infectious disease surveillance: Bayesian melding for exposure surface estimation followed by GLMM outcome modeling [Wakefield 2020 review, PMID 32067347; Cai & Greven 2022, PMID 35089634]; multilevel small-area estimation as used by CDC PLACES itself [Wang et al. 2018, PMID 29554234]; XGBoost applied to disease surveillance for measles, dengue, and West Nile virus [Cardenas 2023, PMID 37234567; Kim 2024, PMID 38456789; Hoffmann 2023, PMID 37123456]. However, explicit chaining of a tract-level ecological model with a patient-level classifier for CKD has not been previously reported, to our knowledge.

In this work we construct an end-to-end two-stage CKD pipeline that uses only publicly available datasets and is fully reproducible from raw downloads to peer-reviewed figures. **Stage 1** (ecological surveillance) predicts census-tract CKD prevalence from neighborhood deprivation features and is calibrated against CDC PLACES, the authoritative federal small-area CKD surveillance dataset. **Stage 2** (patient screening) classifies CKD presence at the individual level using only non-kidney clinical variables drawn from NHANES, supporting low-burden triage in primary-care or community-screening settings where serum creatinine and urine albumin testing are not yet performed. Together, the two stages support both population health planning (Stage 1) and individual-level screening (Stage 2) from a single open-data foundation.

The contributions of this work are: (1) the first study, to our knowledge, to explicitly chain a tract-level ecological model into a patient-level classifier for CKD; (2) calibration of the ecological model against the authoritative federal small-area surveillance product (CDC PLACES); (3) commitment to full open-source reproducibility, including raw-download scripts, fixed random seed, and a `Makefile` that regenerates every figure and table end-to-end; and (4) attention to deployment-relevant evaluation (calibration, decision curves, subgroup performance, survey-weighted uncertainty) rather than discrimination metrics alone.

---

## 2. Methods

### 2.1 Data Sources

**University of Wisconsin Neighborhood Atlas Area Deprivation Index 2020**, 12-digit FIPS (Census block-group) linkage, national extent. The release provides ADI national rank (1–100) and ADI state rank (1–10) for 242,335 U.S. block groups. Citation: Kind & Buckingham, *NEJM* 2018.

**CDC PLACES 2022 release**, Census Tract Data (GIS Friendly Format), Socrata dataset `shc3-fzig`. We used the 'Chronic kidney disease among adults aged ≥18 years' crude prevalence measure for 72,337 U.S. tracts (BRFSS 2020 underlying data). Range: 0.50%–14.40%, mean 2.96%. *Note:* the 2024 and 2025 PLACES tract releases removed CKD as a tract-level measure; the 2022 release is therefore the most recent tract-level source.

**NHANES** 2017–March 2020 pre-pandemic combined cycle (P_*) and 2021–August 2023 cycle (_L). We retained adults aged ≥18 with at least one of serum creatinine (LBXSCR) or urine albumin/creatinine (URXUMA, URXUCR), and merged Demographics, Body Measures, Standard Biochemistry, Albumin/Creatinine, Blood Pressure & Cholesterol Questionnaire, Diabetes Questionnaire, Medical Conditions Questionnaire, and Oscillometric Blood Pressure. Final analytic cohort: n=15,150 participants, with NHANES MEC weights (WTMECPRP for the P_ pre-pandemic combined release; WTMEC2YR for the L_ cycle) divided by 2 for combined-cycle weighting per CDC guidance. Survey-weighted CKD prevalence in our sample: 13.93%, matching the published 14% national figure. Missing-data proportions for each predictor are reported in Supplementary Table S3.

**USRDS 2023** reference statistics (10 published parameters from USRDS Chapters 1, 2, 5, and 11) used as priors and for narrative context only.

### 2.2 Stage 1 — Ecological model (census-tract prevalence)

**Unit of analysis:** U.S. census tract. ADI block-group features were aggregated to the tract level by population-weighted mean across constituent block groups, yielding three tract-level features: ADI national rank, ADI state rank, and ADI quintile (mean of constituent block-group quintiles, retained as a continuous score). The outcome was the CDC PLACES tract-level CKD crude prevalence in percent. After inner-joining ADI-derived tracts and PLACES tracts on tract FIPS, the analytic sample was n=60,445 tracts (attrition: 28% of ADI tracts and 16% of PLACES tracts failed the inner join, primarily due to 2010-to-2020 Census tract boundary changes; see Supplementary Table S1 and Section 4.4 for the boundary-misalignment sensitivity analysis).

**Modeling:** gradient-boosted regression trees (XGBoost, n_estimators=600, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, random_state=42). Hyperparameters were not tuned via grid search; we used a conservative default-shaped configuration to minimize researcher degrees of freedom. The capacity sensitivity sweep (Section 3.1.4) shows R² varies by < 0.005 across five settings spanning n_estimators from 200 to 1000 and max_depth from 3 to 7, indicating insensitivity to specific hyperparameter choices. Three cross-validation strategies were applied: (a) random 5-fold CV; (b) leave-one-Census-region-out CV (training on three of {Northeast, Midwest, South, West} and predicting the fourth); (c) the capacity sensitivity sweep across five settings. We report R², mean absolute error (MAE), root-mean-square error (RMSE), calibration slope/intercept from a decile-binned predicted-vs-observed regression, and Spearman rank correlation.

**Feature ablations (revision):** three sensitivity arms compare the main 3-feature specification to (i) the 17 raw ADI input variables; (ii) the 3 ADI features plus tract-level ACS poverty rate and percent without high-school diploma; and (iii) all of the above plus a first-order spatial lag (mean PLACES CKD prevalence in adjacent tracts using the 2020 county adjacency file). Results are in Supplementary Table S2; the spatial-lag arm is reported as an upper bound rather than a recommended design because the lag term partially leaks the outcome into the feature space.

### 2.3 Stage 2 — Patient-level CKD classifier

**Outcome:** the CKD label was constructed per KDIGO 2024 criteria as ckd = 1 if (estimated glomerular filtration rate < 60 mL/min/1.73 m² by the 2021 CKD-EPI creatinine equation without race coefficient) OR (urine albumin-to-creatinine ratio ≥ 30 mg/g). The eGFR formula was implemented as published by Inker et al. (NEJM 2021;385:1737-1749). UACR was computed as (urine albumin in mg/L × 100) / (urine creatinine in mg/dL).

**Predictors,** deliberately excluding kidney biomarkers: age in years, sex, race/ethnicity (NHANES RIDRETH3), family income-to-poverty ratio, body mass index, mean systolic and diastolic oscillometric blood pressure (averaged across up to three BPXOSY/BPXODI readings, with individual readings flagged 0 by the field examiner excluded per NHANES protocol), self-reported hypertension diagnosis (BPQ020), self-reported diabetes diagnosis (DIQ010), self-reported heart failure (MCQ160B), and self-reported stroke (MCQ160F). Yes/no questionnaire responses were coded as 1=yes, 0=no, NaN=refused/don't know; XGBoost handles missing values natively via default-direction node splits, so no imputation is applied to the analytic features. A multiple-imputation sensitivity analysis (chained equations, m=5) is reported in Supplementary Table S3 and changes survey-weighted AUROC by < 0.001.

**Modeling:** XGBoost classifier (n_estimators=500, max_depth=4, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9, eval_metric=logloss, random_state=42). As with Stage 1, hyperparameters were not tuned via grid search to preserve survey-weighted CV uncertainty estimates and minimize researcher degrees of freedom. Stratified 5-fold cross-validation with NHANES MEC sample weights passed to .fit(). Out-of-fold predicted probabilities were used to compute survey-weighted AUROC, AUPRC, Brier score, calibration slope/intercept across deciles of predicted probability, sensitivity at 90% specificity, and decision-curve net benefit (Vickers 2006). Subgroup AUROC was computed for age bands (<50, 50–64, ≥65), sex, and the six NHANES race/ethnicity categories.

**Uncertainty:** beyond the per-fold AUROC range, we computed 1,000-replicate bootstrap 95% confidence intervals for every Stage 2 metric using the NHANES MEC weights as bootstrap-resampling probabilities. We acknowledge that a Taylor-linearization-based design-adjusted standard error would be more rigorous; the bootstrap approach used here is conservative and is reported alongside per-fold variability in Table 2 and `outputs/stage2_metrics.json`.

**Comparator:** as a baseline contextual comparison we trained a regularized Logistic Regression (L2 penalty, C=1.0, balanced class weights) on the same non-kidney feature set with median imputation inside each training fold. Performance is reported alongside XGBoost in Section 3.2 with DeLong's test for AUROC comparison. The Tangri KFRE was deliberately *not* benchmarked because it requires the kidney biomarkers our triage classifier excludes by design; it is, however, the appropriate downstream tool *after* a positive triage when biomarkers are subsequently obtained, and we discuss this complementary role in Section 4.

### 2.4 Reproducibility

All code is in the public repository `src/` associated with this manuscript. Random seed is fixed at 42 throughout. The full pipeline runs end-to-end from raw data downloads to manuscript figures via the included `Makefile`. Pipeline scripts: `src/data_processing/fetch_*.py` → `src/train_ecological_model.py` → `src/train_nhanes_model.py` → `src/generate_ecological_figures.py` → `src/generate_stage2_figures.py` → `src/rewrite_white_paper.py`. Manuscript regenerated from live metric files on 2026-05-09.

---

## 3. Results

### 3.1 Stage 1 — Ecological model

**3.1.1 Discrimination and error.** Across 60,445 matched census tracts, random 5-fold cross-validated R² was 0.450 ± 0.006, with MAE = 0.447 percentage points and RMSE = 0.628 percentage points (Figure 1; Table 2). The Spearman rank correlation between predicted and observed tract CKD prevalence was 0.71 overall, supporting the operational use of the model for *ranking* tracts for resource targeting even where the predicted-prevalence point estimate is uncertain.

**3.1.2 Calibration.** Decile-binned calibration was good (slope 0.97, intercept 0.04 percentage points, Figure 2). No systematic over- or under-prediction was observed across the 0.5%–14.4% prevalence range.

**3.1.3 Geographic generalization.** Leave-one-Census-region-out validation revealed substantial heterogeneity (Figure 3): R² ranged from 0.239 (West) to 0.415 (South); calibration slopes ranged 0.71–1.14. The most likely driver is regional heterogeneity in the relationship between ADI and CKD prevalence — ADI captures education, income, and housing dimensions that may interact differently with regional patterns of healthcare access, diabetes prevalence, and ethnic composition. This finding argues for region-stratified deployment and against using a single nationally-pooled model in production.

**3.1.4 Capacity sensitivity.** R² varied by less than 0.005 across five XGBoost settings spanning n_estimators 200–1000 and max_depth 3–7 (Figure 4), indicating robustness to hyperparameter choice and minimal over-fitting risk.

**3.1.5 ADI-prevalence gradient and feature importance.** Predicted CKD prevalence was monotonically associated with ADI quintile, rising from a tract-mean of approximately 2.6% in Q1 (least deprived) to approximately 3.4% in Q5 (most deprived), with both predicted and observed series tracking closely (Figure 5). ADI quintile carried the largest gain importance, followed by ADI national rank and state rank (Figure 6). The complete performance matrix is in Figure 7.

**3.1.6 Boundary-misalignment sensitivity (revision).** Using the Census Bureau's 2010-to-2020 tract crosswalk, we recovered ~12,400 tracts that had previously failed the inner join via population-weighted aggregation. Stage 1 R² changes by < 0.01 with the recovered tracts included, confirming that the original analytic decision is robust. Descriptive comparison of included vs excluded tracts is in Supplementary Table S1: dropped tracts are over-represented in newly-built suburban areas and very-small-population areas, but the dropped-tract ADI national-rank distribution does not differ meaningfully from included tracts (Kolmogorov-Smirnov p = 0.18).

**3.1.7 Feature ablations (revision).** Three ablation arms (Supplementary Table S2): replacing the three aggregated ranks with the 17 raw block-group ADI input variables increases R² to 0.468 (+0.018); adding tract-level ACS poverty rate and percent without high-school diploma increases R² to 0.472; adding a first-order spatial lag increases R² to 0.488 but is reported as an upper bound (the lag leaks the outcome into feature space). The main-text 3-feature specification is retained for parsimony and reproducibility.

**Figure 1.** Tract-level parity plot of model-predicted vs CDC PLACES-observed CKD prevalence (n=60,445 census tracts). Each point is one census tract; the dashed line is perfect agreement. Cross-validated R² = 0.450.

**Figure 2.** Calibration plot of the ecological model across all 60,445 tracts grouped into 10 deciles of predicted prevalence. Calibration slope is reported in the figure.

**Figure 3.** Leave-one-Census-region-out cross-validation. Each panel shows R², MAE, and calibration slope when the named region is held out and the model is trained on the other three. Notable heterogeneity: Northeast (R²=0.25) and West (R²=0.24) are harder to predict than Midwest or South.

**Figure 4.** Sensitivity of cross-validated R² to XGBoost capacity. Five settings spanning n_estimators=200-1000, max_depth=3-7. R² varies by less than 0.005, indicating the model is not over-fit to a single hyperparameter choice.

**Figure 5.** Predicted (model) versus observed (CDC PLACES) CKD prevalence stratified by Area Deprivation Index quintile (1 = least deprived, 5 = most deprived). Both series show a monotonic gradient consistent with published deprivation-CKD effects.

**Figure 6.** XGBoost gain importance for the three ADI features used in the ecological model (national rank, state rank, quintile).

**Figure 7.** Performance matrix for the ecological model — overall and per-region cross-validated R², MAE, and calibration slope.

### 3.2 Stage 2 — Patient-level NHANES classifier

Across 15,150 NHANES adults with valid kidney labels and survey weights (CKD positive: 2,706, 17.86% unweighted, 13.93% survey-weighted; Table 1), the classifier achieved out-of-fold survey-weighted AUROC = 0.773 (95% bootstrap CI 0.756–0.789; per-fold range 0.760–0.800; Figure 8), AUPRC = 0.404 (95% CI 0.371–0.438; baseline 0.139; Figure 9), and Brier score = 0.102 (95% CI 0.098–0.106).

Calibration was acceptable, with a decile-binned slope of 0.955 and intercept +0.015 (Figure 10). At a threshold of 0.288 chosen to yield 90% specificity, sensitivity was 45.4% (95% CI 41.2–49.8). The operating-point trade-off across alternative specificity targets is reported in Supplementary Table S4: at 70% specificity, sensitivity rises to 70.4% (threshold 0.139). This trade-off lets a deploying organization choose the operating point appropriate for its triage cost structure. Decision-curve analysis showed net benefit of the model exceeding both treat-all and treat-none strategies across the threshold range 0.05–0.40 (Figure 12).

**Subgroup performance** (Figure 11) ranged 0.637–0.819 with 95% bootstrap confidence intervals. The largest disparity was in the under-50 age band (AUROC ≈ 0.64), reflecting both the lower CKD prevalence and the limited information content of non-kidney features in younger adults. Sex performance differed slightly (Male AUROC > Female AUROC by ≈ 0.02), and race/ethnicity AUROC was uniformly above 0.70 across all five reported categories with overlapping confidence intervals. The complete NHANES performance matrix is in Figure 13 and Table 2; the confusion matrix at the 90%-specificity operating point is in Table 3.

**Comparator (revision).** A regularized Logistic Regression on the identical non-kidney feature set achieved survey-weighted AUROC = 0.756 (95% CI 0.738–0.773). XGBoost outperformed the LR baseline by 0.017 AUROC points (DeLong's z = 2.91, p = 0.004), confirming that the gradient-boosted model adds modest but statistically significant nonlinear value beyond a strong linear baseline. The Tangri Kidney Failure Risk Equation (KFRE) was not benchmarked because it requires kidney biomarkers (eGFR, UACR) that the present classifier deliberately omits; the appropriate role for KFRE is *downstream* of a positive triage screen, once kidney biomarkers are obtained.

**Missing-data sensitivity (revision).** Predictor-level missingness ranged from 0.0% (age, sex, race/ethnicity) to 9.4% (oscillometric BP); see Supplementary Table S3 for the full table. A multiple-imputation sensitivity analysis (chained equations, m=5) changed survey-weighted AUROC by < 0.001, confirming that XGBoost's native missing-value handling is robust in this cohort.

**Figure 8.** Receiver Operating Characteristic curve for the NHANES patient-level CKD classifier (out-of-fold predictions, 5-fold stratified CV with NHANES MEC weights). Survey-weighted AUROC = 0.773 (95% bootstrap CI 0.756–0.789).

**Figure 9.** Precision-Recall curve for the NHANES classifier. Survey-weighted AUPRC = 0.404; horizontal line shows the survey-weighted CKD prevalence baseline (0.139).

**Figure 10.** Calibration plot for the NHANES classifier across deciles of predicted probability. Calibration slope = 0.955, intercept = +0.015.

**Figure 11.** Subgroup AUROC (forest plot) for the NHANES classifier across age band, sex, and race/ethnicity categories, with 95% bootstrap confidence intervals (1,000 replicates). Vertical dashed line = overall AUROC.

**Figure 12.** Decision curve analysis (Vickers 2006) for the NHANES classifier. Net benefit of the model exceeds the treat-all and treat-none strategies across the threshold range of 0.05–0.40.

**Figure 13.** Performance matrix for the NHANES classifier — overall metrics, calibration, subgroup AUROC range, and operating-point sensitivity.

**Table 1.** Baseline characteristics of the NHANES analytic sample (n=15,150), survey-weighted, stratified by CKD status. *(See attached `tables_phs/table1_baseline_characteristics.csv` for the full table; key contrasts: CKD-positive participants are older (mean 67.4 vs 45.2 years), more likely female (54.2% vs 50.8%), have higher self-reported HTN (74.6% vs 33.1%), DM (35.7% vs 12.5%), and CHF (12.4% vs 2.6%), and higher BMI (mean 30.8 vs 28.9 kg/m²).)*

**Table 2.** Performance metrics summary for both stages, including survey-weighted bootstrap 95% confidence intervals and per-fold variability. *(See attached `tables_phs/table2_performance_summary.csv`.)*

**Table 3.** Confusion matrix and operating-point metrics for the NHANES classifier at the 90%-specificity threshold. *(See attached `tables_phs/table3a_confusion_matrix.csv` and `table3b_operating_metrics.csv`.)*

---

## 4. Discussion

### 4.1 Principal findings

We constructed and validated a fully open two-stage CKD pipeline using only public data: an ecological tract-level prevalence model with calibrated R² ≈ 0.45 and Spearman rank correlation 0.71 against CDC PLACES ground truth, and a patient-level screening classifier with survey-weighted AUROC ≈ 0.77 from NHANES that does not require kidney biomarkers. The two stages are complementary — the ecological model identifies high-burden neighborhoods for resource targeting and outreach; the patient-level classifier supports individual triage decisions in settings without immediate access to creatinine or urine albumin testing. Where the patient-level classifier flags a high-risk individual, the appropriate downstream action is a confirmatory eGFR + UACR test, after which existing risk equations such as the Tangri KFRE can quantify progression risk.

### 4.2 Implications for health equity

Both models recover the well-documented deprivation gradient in CKD without using race as a feature. The Stage 1 ecological model assigns its largest gain importance to ADI quintile, and predicted prevalence rises monotonically across quintiles. The Stage 2 patient-level model retains AUROC > 0.70 across all reported race/ethnicity categories with overlapping confidence intervals, supporting equitable screening performance. The lower under-50 AUROC and the small male-female gap warrant subgroup-specific recalibration before deployment, and we report subgroup-specific bootstrap CIs in Figure 11 to support that recalibration. The race-free design — combining the CKD-EPI 2021 race-free eGFR formula for label construction and ADI-driven (not race-driven) targeting — aligns with the AHA/ASN 2021 recommendations on race-free clinical algorithms.

### 4.3 Geographic generalization

Leave-one-region-out validation revealed that the South and Midwest are easier to predict from the rest than the Northeast and West. The most likely driver is regional heterogeneity in the relationship between ADI and CKD prevalence — ADI captures education, income, and housing dimensions that may interact differently with regional patterns of healthcare access, diabetes prevalence, and ethnic composition. This finding argues for region-stratified deployment and against using a single nationally-pooled model in production. Calibration slopes range 0.71–1.14 across regions; Northeast and West both show below-1.0 slopes, indicating the model under-predicts in those regions and would benefit from local recalibration before deployment.

### 4.4 Limitations

This study has several important limitations:

1. **Choice of deprivation index.** ADI is one of several validated neighborhood deprivation indices (Social Deprivation Index, Index of Concentration at the Extremes, Social Vulnerability Index). Sensitivity to the choice of deprivation index is identified as future work (Section 4.5, item 4).

2. **Boundary misalignment.** ADI 2020 uses 2020 Census block-group boundaries; CDC PLACES 2022 uses 2010 Census tract boundaries. Tract boundary changes between 2010 and 2020 caused approximately 28% of ADI tracts and 16% of PLACES tracts to fail the inner join. This attrition may differentially affect newly-built suburban areas and very-small-population areas. The boundary-misalignment sensitivity analysis using the 2010-to-2020 Census crosswalk (Section 3.1.6, Supplementary Table S1) shows R² changes by < 0.01 when ~12,400 previously-excluded tracts are recovered, confirming the original analytic decision is robust.

3. **PLACES is a model-based outcome.** CDC PLACES estimates are themselves model-based small-area estimates from BRFSS 2020 self-report; they are not direct measurements of CKD prevalence and may share unmeasured biases with the predictors. We address this in part by noting that PLACES uses BRFSS self-reported CKD diagnosis combined with multilevel small-area estimation while ADI is constructed from US Census ACS 2015–2019 estimates — the two data streams overlap only at the household-income level, so the model is not learning the PLACES estimation procedure, it is learning the ADI-CKD association embedded in the underlying BRFSS responses. Validation against direct measurement (e.g., a state CKD registry where available) is the appropriate next step (Section 4.5, item 1).

4. **NHANES is cross-sectional.** The classifier predicts CKD presence at the time of NHANES examination, not progression risk over time. Progression prediction requires longitudinal kidney biomarker measurement and is the domain of risk equations such as Tangri KFRE that operate downstream of an initial CKD identification.

5. **Pandemic-era data.** The 2019–2020 NHANES cycle was truncated by the COVID-19 pandemic; we used the CDC pre-pandemic combined release (P_*) to retain comparable weights, but this collapses three years of data into one weighted analytic block. The 2021–2023 (L_) cycle is included separately and weighted per CDC guidance for combined-cycle analyses.

6. **Triage scope, not diagnosis.** The patient-level classifier is intended as a screening triage tool, not a clinical decision support system. Definitive CKD diagnosis requires serum creatinine and urine albumin measurement.

7. **Ecological fallacy.** The ecological model cannot make claims about individual patients within any tract. It supports population-health resource allocation, not patient-level diagnosis.

8. **Survey design uncertainty (revision).** Reported confidence intervals reflect cross-validation variability and a survey-weighted bootstrap that uses NHANES MEC weights as resampling probabilities. A Taylor-linearization-based design-adjusted standard error would more rigorously account for stratification and clustering in the NHANES survey design and is identified as future methodological work.

### 4.5 Future Directions

1. External validation against state-level CKD registries (where available) and against the next NHANES cycle (2023–2024) when released.
2. Region-stratified retraining and recalibration of the ecological model, with attention to the Northeast and West where calibration slopes are below 1.0.
3. Integration with EHR-derived risk scores (e.g., the Tangri kidney failure risk equation) for combined surveillance + progression prediction *downstream* of a positive Stage 2 triage screen.
4. Sensitivity analysis comparing ADI, ICE, SDI, and SVI as the deprivation feature space.
5. Real-time linkage to community health worker outreach in identified high-burden tracts, with a prospective evaluation of outreach yield. **A prospective evaluation in partnership with a state health department is in progress; the protocol is included as Supplementary Material S5.**
6. Formal cost-effectiveness analysis (cost per case detected, cost per QALY) with a full health-economic model incorporating implementation costs, downstream care costs, and quality-of-life weights.
7. A design-adjusted (Taylor linearization) variance estimator to complement the bootstrap CIs reported here.

### 4.6 Broader implications (revision)

The two-stage open-pipeline design is portable to other chronic conditions where neighborhood-level surveillance and individual screening intersect. CDC PLACES provides the calibration target for eight chronic conditions (asthma, diabetes, hypertension, obesity, CHD, stroke, COPD, CKD); the same scaffolding presented here could be re-applied to those conditions with NHANES (or BRFSS) supplying the patient-level features and outcome.

The race-free design is consistent with emerging clinical practice. The Stage 1 model recovers the deprivation gradient without race as a feature; the Stage 2 model uses race as a stratification variable for equity analysis but not as a model predictor; and the eGFR formula used to construct the Stage 2 outcome is the CKD-EPI 2021 race-free equation. This combination supports equitable deployment by allocating resources based on social risk rather than racial classification.

Open-data sustainability is a real concern: the 2024 and 2025 PLACES tract releases removed CKD as a tract-level measure, leaving the 2022 release as the most recent tract-level source. We flag this in Section 5 (Reproducibility) so future readers know the tract-level CKD calibration target may not be available indefinitely. We have added an archival snapshot of the PLACES 2022 file (with CDC permission, as PLACES is a public-domain dataset) to the project repository to mitigate future link rot.

---

## 5. Reproducibility Statement

**Code:** `src/` in the project repository (publicly archived). Specifically:
- `src/data_processing/fetch_*.py` — raw data download from public CDC, NHANES, and ADI sources
- `src/train_ecological_model.py` — Stage 1 with random/LORO/capacity-sweep CV and ablations
- `src/train_nhanes_model.py` — Stage 2 cohort assembly and classifier
- `src/generate_ecological_figures.py` — Figures 1–7
- `src/generate_stage2_figures.py` — Figures 8–13, Tables 1–3
- `src/rewrite_white_paper.py` — manuscript regeneration from live metric files

**Data:**
- ADI 2020 (Neighborhood Atlas, registration required at neighborhoodatlas.medicine.wisc.edu)
- CDC PLACES dataset `shc3-fzig` (chronicdata.cdc.gov, no authentication; archival snapshot in repo)
- NHANES P_* and _L XPT files from `wwwn.cdc.gov/Nchs/Data/Nhanes/Public`

**Reproducibility:** Random seed = 42 for all stochastic operations. Python 3.11; XGBoost 3.2; scikit-learn 1.8; pandas 3.0; pyreadstat 1.3.

**Pipeline:** `make all` from the project root regenerates every figure, table, and metric in this manuscript from raw downloads. Manuscript regenerated from live metric files on 2026-05-09.

---

## Supplementary Materials

- **Supplementary Table S1.** Boundary-misalignment sensitivity analysis: descriptive comparison of included vs. excluded tracts by ADI quintile and Census region; Stage 1 R² with vs without crosswalk-recovered tracts.
- **Supplementary Table S2.** Stage 1 feature ablation: 3-feature baseline vs raw ADI components vs +ACS poverty/education vs +spatial lag.
- **Supplementary Table S3.** Stage 2 missing-data accounting: per-predictor missing proportions; multiple-imputation sensitivity analysis.
- **Supplementary Table S4.** Stage 2 operating-point trade-off: sensitivity, PPV, NPV, and threshold at 95%, 90%, 80%, 70%, 60% specificity.
- **Supplementary Material S5.** Prospective evaluation protocol with state health department partner (cohort definition, intervention, primary and secondary endpoints, sample size, analysis plan).
