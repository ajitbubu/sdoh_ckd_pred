# Response to JMIR AI Reviewer — Methodological Revisions

**Manuscript:** AI-Enabled Early Detection of Chronic Kidney Disease in Underserved Communities Using Social Determinants of Health: Development and Pilot Simulation Study

**Status:** Major revision in response to methodological concerns raised by the original reviewer.

---

## Summary of changes

We thank the reviewer for the careful and substantive critique. The three concerns raised — circularity in synthetic labeling, absence of real-world noise/missingness, and ecological bias from ZCTA-level SDOH — are well-founded, and on reflection we agreed that they could not be addressed through revisions to the original synthetic-data framework. We have therefore **rebuilt the methodology end-to-end on real, publicly-available patient data** rather than retain the synthetic cohort.

The revised study uses:

- **NHANES (cycles 2005-2014)** as the primary analytic dataset, linked to the **NCHS Public-use Linked Mortality File** (follow-up through December 31, 2019) for outcome ascertainment.
- **5-year all-cause mortality** among adults with baseline Stage 2-3 CKD as the primary outcome (replacing the synthetic Stage 4-5 progression endpoint, which is not observable in cross-sectional NHANES).
- **Individual-level, questionnaire-based SDOH** variables (educational attainment, poverty income ratio, food security questionnaire score, insurance type, employment, housing tenure) replacing the ZCTA-level neighborhood aggregates of the original submission.
- **CKD-EPI 2021 race-free eGFR** (per Eneanya et al. 2019, originally cited as ref [15]) replacing race-coefficient eGFR.

The paper's identity has been revised accordingly: the title, abstract, framing, and study population now describe a nationally representative US adult cohort with baseline early-stage CKD, with subgroup analyses to examine performance across racial/ethnic, educational, and socioeconomic strata. The "rural underserved" framing and the simulated pilot deployment / cost-effectiveness sections have been removed because they cannot be supported by the revised analytic approach.

We address each of the reviewer's three concerns directly below.

---

## Point 1 — Tautological prediction (circular labeling)

**Reviewer's concern:** The synthetic cohort generated outcome labels probabilistically from clinical and SDOH features, then trained an XGBoost classifier on those same features. The resulting AUROC of 0.87 reflected the simulator's parameters, not clinical discovery.

**Our response:** This concern is correct, and on review of our own simulator code we confirmed that the outcome probability function in `step2_generate_cohort.py` was tuned to produce a target AUROC gap of 0.07 between the full and clinical-only models, and that the SHAP feature importance percentages reported in the original submission (eGFR slope 18.4%, baseline eGFR 15.2%, UACR 12.8%, ADI 9.1%, food desert 7.3%, etc.) corresponded directly to coefficient magnitudes encoded in the generator. We agree these results constituted recovery of simulator parameters rather than clinical signal.

**Resolution:** The synthetic generator has been retired. All cohort labels in the revised manuscript are observed events from the NCHS National Death Index linkage — no probabilistic assignment, no parameter-tuning to target performance values. The mortality status and underlying cause of death are independently ascertained by NCHS via deterministic and probabilistic record linkage; the analytic pipeline has no access to the labeling mechanism.

**Revised primary results** (NHANES cycles 2005-2014, N = 2,911, 646 5-year mortality events):

| Model | AUROC (5-fold CV OOF, 95% CI) |
|---|---|
| Clinical-only Logistic Regression | 0.754 (0.734-0.774) |
| Clinical-only XGBoost | 0.731 (0.708-0.753) |
| SDOH-augmented XGBoost (full) | 0.745 (0.723-0.765) |

Apples-to-apples DeLong's test (SDOH-augmented XGBoost vs. Clinical-only XGBoost): z = 2.75, **p = 0.006**. The SDOH features provide a small but statistically significant improvement of 0.014 AUROC points when model class is held constant.

Notably, a regularized Logistic Regression on clinical features alone outperforms both XGBoost variants (0.754 vs. 0.745 and 0.731), which is consistent with the small cohort size (N ≈ 2,911) favoring strong inductive bias over flexible non-linear models. We report this honestly in the revised manuscript.

These results contrast sharply with the original synthetic-cohort claim of a 0.07 AUROC improvement and underscore the reviewer's point that the simulated improvement was an artifact.

---

## Point 2 — Absence of real-world noise and missingness

**Reviewer's concern:** The synthetic cohorts were fully observed by construction; in real EHR data, HbA1c, blood pressure, medication adherence, and many other variables are routinely missing. The original results were therefore likely optimistic.

**Resolution:** NHANES is a real population survey with real measurement uncertainty and real missingness:

- HbA1c is missing for participants who did not complete the morning fasting examination (approximately 35% of the analytic cohort across cycles 2005-2014).
- UACR (urine albumin/creatinine) is computed only for participants who provided a valid urine specimen at the mobile examination center (~12% missing).
- Blood pressure is averaged from up to 4 readings per participant; some readings are excluded by the field examiner per NHANES protocol, so individual readings are missing.
- Medication adherence cannot be observed in NHANES (which does not include pharmacy fill data) and is not used as a feature; insurance coverage from HIQ is included instead.

XGBoost's native handling of missing values is used throughout the revised pipeline — no imputation is applied to the analytic features. The Logistic Regression baseline uses median imputation within each training fold, with the imputer fit on training data only and applied to the validation fold (i.e., no leakage). These choices are documented in the revised Methods → Statistical Analysis section.

---

## Point 3 — Ecological bias from ZCTA-level SDOH

**Reviewer's concern:** Even setting aside the circularity, ZCTA-level SDOH features applied to individual-level risk scores carry an ecological-bias risk: not every individual in a high-deprivation ZCTA experiences high deprivation, and aggregation can attenuate or distort associations.

**Resolution:** The revised SDOH layer is entirely individual-level. NHANES collects each of the following from the participant directly:

- Educational attainment (DMDEDUC2)
- Family poverty income ratio (INDFMPIR), based on self-reported family income relative to the federal poverty line
- Household food security category (FSDHH), derived from the 18-item Household Food Security Survey Module
- Insurance coverage and type (HIQ011, HIQ031A-J)
- Employment status (OCQ150)
- Housing tenure (HOQ065)

These are responses from the individual participant, not aggregates from their neighborhood. The ecological-fallacy concern raised by the reviewer is structurally resolved by this design.

We have added a Limitations subsection acknowledging that NHANES does not provide ZIP-code-level geographic identifiers in the public-use file, so neighborhood-level SDOH (ADI, CDC PLACES, food desert designation) could not be incorporated. We frame this as a future-work direction requiring restricted-access NHANES geographic files or a population with linked ZIP-level data.

---

## Other changes prompted by the methodology rebuild

These changes were necessary as a direct consequence of moving to real NHANES data, but we summarize them here for the reviewer's awareness:

1. **Outcome change** — from 24-month CKD progression (Stage 2-3 → Stage 4-5) to 5-year all-cause mortality among adults with baseline Stage 2-3 CKD. NHANES is cross-sectional and does not provide longitudinal eGFR for progression ascertainment. CKD-cause mortality is reported as a secondary outcome.

2. **Cohort change** — from a 47,832-patient synthetic rural cohort to an N = 2,911 nationally representative analytic cohort of adults with baseline Stage 2-3 CKD across NHANES cycles 2005-2014. Right-censoring is avoided by restricting the primary analysis to cycles with at least 60 months of follow-up to the December 2019 censoring date; cycles 2015-2018 are reserved as a 3-year sensitivity-validation cohort (N = 1,161, 125 events; AUROC 0.731, 95% CI 0.691-0.772).

3. **Framing change** — the "rural underserved" framing has been removed. The revised cohort is nationally representative and recruited via household sampling, not from rural primary care. We have removed the "Native American" callout from the Abstract and Introduction; NHANES race/ethnicity coding does not include a separate Native American category in the standard public-use file.

4. **Pilot deployment and cost-effectiveness sections removed.** The original Methods → Simulated Deployment, Results → Projected Pilot Deployment Outcomes, Results → Projected Cost-Effectiveness, and Discussion references to the BCR of 3.75:1 have been removed because real NHANES participants did not receive an intervention. The Discussion now contains a brief Implications for Deployment paragraph clearly framed as motivation rather than as a finding.

5. **SHAP analysis** — feature importance is now reported using XGBoost gain-based importance because of a runtime incompatibility between our XGBoost and SHAP versions. The substantive ranking is preserved: clinical features (especially CHF, age, prior stroke, baseline CKD stage) dominate, with individual-level SDOH (insurance coverage, home ownership, poverty income ratio) contributing approximately 24% of total feature importance. The original synthetic paper's SHAP percentages should be disregarded.

6. **Equity analysis** — subgroup AUROCs are now computed using out-of-fold predicted probabilities, which honestly reveal disparities the original synthetic analysis masked: for example, AUROC for participants in the lowest income tertile (PIR-Low) is 0.65 (95% CI 0.61-0.70) versus 0.83 (0.79-0.87) for the highest tertile. We discuss these findings transparently and frame the model as not yet equitably calibrated for low-income subgroups.

---

## What stays from the original submission

- The conceptual framework: a structured argument for integrating SDOH with clinical features in CKD risk modeling, explainable AI for clinical trust, and attention to subgroup performance.
- The motivational background: CKD as a public health priority, the role of social determinants in CKD outcomes, the need for risk models that consider the full clinical and social context.
- The references base, with additions for NHANES methodology, CKD-EPI 2021, and the NCHS Linked Mortality File documentation.

---

## Recommendation on resubmission target

We respectfully request that the editors consider this as a revised submission to JMIR AI. If the editors judge that the substantial methodological and framing changes place the work outside JMIR AI's current scope, we would welcome guidance on transferring to JMIR Medical Informatics or JMIR Formative Research, both of which have published similar SDOH-augmented prediction work.

We thank the reviewer again for the rigorous critique. The original submission would not have served the field; the revised analysis provides honest, defensible, and reproducible evidence about the value (and limits) of integrating individual-level social determinants of health into early-CKD mortality risk prediction.
