# Response to Reviewer FE: JMIR Public Health & Surveillance (ms 101575)

This file contains Reviewer FE's 8 major comments, what was changed in v6, the evidence behind each change, and a draft reply. The paste-ready version is in `JMIR_PHS_v6_Response_Letter.md`.

**Overall assessment:** The reviewer is correct on 7 of the 8 points. Several of them, including the repository, the crosswalk analysis, the calibration bin, the sex gap, and DeLong, are errors that we had already found and corrected in v6 for the editor; the reply says so openly. On comment 4, our new NHANES analysis does not support the reviewer's hypothesized direction of bias, and the reply presents that evidence rather than simply conceding the point.

---

## Comment 1: Cited repository does not contain the pipeline; reproducibility cannot be verified

**Verified:** Yes. Reference [23] pointed to `sanjoyp158-sri/sdoh_ckd_pred`, whose last commit was on 2026-04-11. It contains the earlier synthetic-cohort project and none of the Stage 1/2 pipeline. The pipeline lives in `ajitbubu/sdoh_ckd_pred`, whose public `main` was still at v4.

**Changes:**

- **Citation.** The paper now cites `github.com/ajitbubu/sdoh_ckd_pred` and a **Zenodo DOI for the exact version used, minted at submission**. `CITATION.cff` and `.zenodo.json` were added for the release. *Author action: push the branch, merge to main, create release `v6.0.0` with Zenodo–GitHub integration enabled, and paste the DOI into the manuscript (search for `10.5281/zenodo.23441764`, which appears twice).*
- **Metric files.** Multimedia Appendix 2 provides `stage1_metrics.json`, `stage2_metrics.json`, `stage2_metrics_ci.json`, `stage2_comparator_lr.json`, and the other output files.
- **Sentinel value.** The pipeline writes `adi_source: real_neighborhood_atlas`, and the manuscript now quotes that value. The `real_blockgroup` in v5 was wrong.
- **No silent substitution.** `src/train_ecological_model.py` now **stops with an error** if the ADI file is absent. Synthetic ADI is used only with an explicit `--allow-placeholder` flag, for testing the code.
- **`LOGIN_CREDENTIALS.md`.** Removed from the repository and added to `.gitignore`. *Author action: rotate any credentials it contained; it remains in git history and in both public repos until history is purged.*

**Draft reply:**
> We thank the reviewer for checking the repository, and we apologize: reference [23] pointed to an earlier repository from a previous synthetic-cohort version of the project, and the described pipeline was not in it. The revised manuscript cites the correct repository (github.com/ajitbubu/sdoh_ckd_pred) and a Zenodo archive of the exact version that produced the reported results (DOI 10.5281/zenodo.23441764), deposited at submission so that it can be inspected during review. The pipeline's metric files (stage1_metrics.json, stage2_metrics.json, and the supplementary analysis outputs) are supplied as Multimedia Appendix 2. We have corrected the sentinel value in the text (the pipeline records adi_source: real_neighborhood_atlas). We agree that silent substitution was poor design: the Stage 1 script now stops with an error if the Neighborhood Atlas file is absent, and synthetic data can be used only with an explicit testing flag. We also thank the reviewer for flagging the credentials file; it has been removed and the affected credentials are being rotated.

---

## Comment 2: Boundary-misalignment analysis is arithmetically impossible

**Verified:** Yes. Only 11,392 PLACES tracts were unmatched (72,337 − 60,945), so "~12,400 recovered" is impossible. We also found that this analysis, and Supplementary Table S1, were never implemented in the code. Both were removed in v6.

**Draft reply:**
> The reviewer is correct, and we are grateful for the careful check. On re-auditing the pipeline we found that the boundary-misalignment analysis described in Section 3.1.6 and Supplementary Table S1 had not been implemented, and the figures reported for it were not produced by our code. We have removed the analysis and the table. The revised manuscript reports only what the code produces: 60,945 of 72,337 PLACES tracts (84.3%) linked to ADI tracts, and 24,450 of 85,395 ADI tracts (28.6%) had no PLACES match. We identify a crosswalk-based reallocation as a limitation and future step, not as a completed analysis.

---

## Comment 3: The "chaining" of the two stages is not implemented

**Verified:** Yes. Stage 1 output is never used in Stage 2, and public NHANES has no tract geocodes. v6 had already dropped the "first study to chain" claim. It now states explicitly, in the Abstract, Methods, Discussion, and Limitations, that the stages are **separate, unlinked analyses**, and that linking would require restricted NCHS Research Data Center data.

**Draft reply:**
> We agree, and we have taken the reviewer's second option. The novelty claim has been removed. The Abstract and Methods now describe two separate analyses that share a design but are not linked: Stage 1 predictions are not used as inputs, priors, or offsets in Stage 2, and the stages share no records. We state that linking them would require participants' census tracts, which are available only as restricted data through the NCHS Research Data Center, and the Limitations note that we therefore could not test whether combining tract prioritization with individual triage improves detection.

---

## Comment 4: PLACES measures self-reported diagnosed CKD, a different construct, with socially patterned under-ascertainment

**Changes:** The construct is now stated in the Abstract ("prevalence of self-reported diagnosed CKD"), the Methods, the Discussion, the Limitations (now the first and longest limitation), and the Conclusions. We also **quantified it** with the NHANES item that corresponds to the BRFSS question behind PLACES (KIQ022, "Ever told you had weak or failing kidneys?"). The new script section is in `src/stage2_supplementary.py`, with output in `outputs/stage2_ckd_awareness.json`.

| | All | PIR <1.3 | PIR 1.3–3.49 | PIR ≥3.5 |
|---|---|---|---|---|
| CKD markers, % | 14.1 | 16.7 | 16.7 | 10.6 |
| Self-reported kidney disease, % | **3.0** (2.6–3.4) | 4.2 | 3.3 | 2.2 |
| Awareness among those with CKD markers, % | **13.1** (11.4–14.8) | **16.2** (12.8–20.1) | 12.7 (10.2–14.9) | **12.9** (9.9–15.9) |

- **The reviewer's magnitude is confirmed.** Self-report captures about one fifth of measured CKD, and self-reported prevalence (3.0%) matches the PLACES mean (2.96%).
- **The reviewer's direction is not supported at the individual-income level.** Awareness is not lower at low income. The income gradient in self-reported disease (ratio 1.91) is *steeper* than the gradient in CKD markers (1.58), which points away from the null rather than toward it.
- **Caveats, stated in the paper:** individual income is not area deprivation; self-report may capture advanced CKD, which is more socially patterned; and awareness by area deprivation cannot be assessed with public NHANES. The paper therefore says the direction of bias is uncertain and that the Stage 1 gradient is a gradient in *diagnosed* CKD.

**Draft reply:**
> We thank the reviewer for this important point, which we have adopted throughout. The Abstract, Methods, Discussion, Limitations, and Conclusions now state that the Stage 1 outcome is the prevalence of self-reported diagnosed CKD, a different construct from the laboratory markers used in Stage 2.
>
> To quantify the gap and test the hypothesized direction of bias, we used the NHANES item corresponding to the BRFSS question behind PLACES. Self-reported kidney disease was 3.0%, close to the 2.96% PLACES mean, against 14.1% with laboratory markers. Only 13.1% of adults with CKD markers were aware of it, confirming the magnitude the reviewer describes.
>
> However, awareness was not lower at lower income (16.2% at income-to-poverty ratio <1.3 vs 12.9% at ≥3.5), and the income gradient in self-reported disease (ratio 1.91) was steeper than that in CKD markers (1.58). In these data, then, under-ascertainment did not bias the socioeconomic gradient toward the null.
>
> Because individual income is not area deprivation, and self-report may preferentially capture advanced disease, we do not claim this settles the direction of bias at the tract level. The revised Limitations state that the direction and size of the bias are uncertain and that the Stage 1 gradient should be read as a gradient in diagnosed CKD.

---

## Comment 5: Calibration slope is an artifact of a degenerate bin

**Verified:** Yes. The v5 routine created a spurious 11th bin containing a single participant (not 1,515), and that point inflated the slope. This was fixed in v6. For this round we added everything the reviewer requested:

| Measure | Value (95% design-based CI) |
|---|---|
| Logistic calibration slope (y on logit p) | **0.751** (0.703–0.803) |
| Logistic calibration intercept (logit p as offset) | +0.050 (−0.018 to 0.120) |
| Calibration-in-the-large | +0.004 (−0.002 to 0.011) |
| ICI / E50 / E90 | **0.022** (0.017–0.029) / 0.019 / 0.030 |
| Brier skill score vs prevalence-only (null Brier 0.120) | **0.147** (0.123–0.172) |

**Figure 8** now shows a flexible spline-logistic calibration curve with design-based pointwise 95% CIs, plus exactly 10 weighted deciles. Bin sizes are in the new Table S3. The text notes that the curve departs from the diagonal above a predicted risk of about 0.3, near the deployed threshold, which echoes the reviewer's observation.

**Draft reply:**
> The reviewer is right. A binning error created an eleventh bin containing a single participant, which inflated the reported slope; this has been corrected. We now report the logistic calibration slope (0.75, 95% CI 0.70–0.80) and intercept (+0.05, −0.02 to 0.12) from the regression of the outcome on the logit of predicted risk, and calibration-in-the-large. We also report a flexible spline-based calibration curve with design-based pointwise 95% CIs (Figure 8), ICI (0.022), E50 (0.019), and E90 (0.030), and the Brier skill score against the prevalence-only model (0.147, 95% CI 0.123–0.172). Figure 8 now has exactly 10 deciles, with bin sizes in Table S3. As the reviewer notes, the curve departs from the diagonal above a predicted risk of about 0.3, close to the deployed threshold, and we discuss the need for recalibration before deployment.

---

## Comment 6: Sex disparity understated; AUROC parity ≠ equitable performance

**Verified:** Yes. The sex gap is 0.07 (men 0.81, women 0.74, non-overlapping CIs). The v5 text said 0.02 and was corrected in v6. The "5 categories" error was fixed in v6. The text now states that the maximum (0.81) comes from the smallest group (n=845).

**New analysis (Table S6):** sensitivity, specificity, PPV, NPV, proportion flagged, calibration-in-the-large, and calibration slope for every subgroup at the deployed threshold, all with design-based CIs.

| Subgroup | Sensitivity at threshold, % (95% CI) |
|---|---|
| Age <50 / 50–64 / ≥65 | **11.8** (8.2–15.5) / 31.9 / **68.1** |
| Women / men | 43.2 / 47.0 |
| Mexican American | **27.6** (20.3–34.4) |
| Other Hispanic / non-Hispanic Asian | 34.1 / 37.7 |
| Non-Hispanic White / non-Hispanic Black | 45.4 / **55.4** (50.0–60.7) |
| PIR <1.3 / ≥3.5 | 49.7 / 32.5 |

Calibration-in-the-large is about zero in every subgroup (−0.003 to +0.008), and calibration slopes range from 0.56 to 0.81.

**Text changes:** "equitable screening performance" has been removed. The Discussion now opens the equity paragraph with "Equal AUROC across groups is not equal performance" and advises agencies to check sensitivity and the proportion flagged in each population they serve. The Abstract and Conclusions report the threshold disparities.

**Draft reply:**
> We agree on both points and thank the reviewer. The sex difference is 0.07 (0.81 vs 0.74, non-overlapping CIs), and both passages have been corrected. The count of race/ethnicity categories (six) has been corrected, and we now note that the maximum subgroup AUROC comes from the smallest group (n=845).
>
> We have also added the analysis the reviewer requested (Table S6): sensitivity, specificity, PPV, NPV, proportion flagged, and subgroup calibration at the deployed threshold, with design-based CIs. Calibration-in-the-large was close to zero in all groups, but sensitivity differed substantially: 11.8% in adults younger than 50 vs 68.1% at 65 or older, and 27.6% among Mexican American vs 55.4% among non-Hispanic Black adults.
>
> We have removed the claim of equitable screening performance. The Abstract, Discussion, and Conclusions now state that similar AUROC does not imply similar performance at a fixed threshold, and that thresholds should be set and checked locally for each population served.

---

## Comment 7: XGBoost vs LR comparison invalid (DeLong assumptions; different imputation)

**Verified:** Yes, on both points. DeLong's test assumes independent observations and fixed predictions, and the v5 comparison mixed model class with missing-data strategy. The v5 numbers (Δ 0.017, z = 2.91, P=.004) were also not produced by any code. v6 had already replaced them; this revision implements exactly the analysis the reviewer proposed.

**New analysis** (`src/stage2_model_comparison.py`, output `outputs/stage2_comparator_lr.json`):

- **Models.** Three models on identical predictors and folds: XGBoost with native missing handling (primary), XGBoost with median imputation, and LR with **the same** median imputation.
- **Uncertainty.** The **full 5-fold CV is re-run inside each of 1,000 Rao–Wu PSU-within-strata bootstrap replicates**, using replicate weights.
- **Reporting.** Differences with 95% percentile CIs; **no P values, and DeLong removed.**

| Comparison | ΔAUROC (95% CI) |
|---|---|
| XGBoost (median) − LR (median): same imputation | **−0.004** (−0.026 to 0.003) |
| XGBoost (native) − LR (median) | −0.006 (−0.027 to 0.002) |
| XGBoost (native) − XGBoost (median): imputation effect | −0.002 (−0.006 to 0.005) |

**Caveat, stated in the paper:** each Rao–Wu replicate refits on about half of the PSUs (n_h − 1 = 1 of 2 per stratum). The interval therefore also reflects reduced training data, which may penalize the more flexible model, and this is why the CIs are left-skewed. The conclusion does not depend on this: the point estimates show no advantage for XGBoost.

**Draft reply:**
> We agree with both points and have replaced the comparison. DeLong's test has been removed, and no P values are reported. XGBoost and logistic regression are now compared under the same median imputation fitted within each training fold, alongside the primary XGBoost model with native missing-value handling. Uncertainty is estimated as the reviewer suggested, by re-running the full 5-fold cross-validation inside each of 1,000 bootstrap replicates that resample NHANES primary sampling units within strata.
>
> Under identical imputation, the AUROC difference (XGBoost minus logistic regression) was −0.004 (95% CI −0.026 to 0.003). For the primary XGBoost model it was −0.006 (−0.027 to 0.002), and the imputation strategy itself changed XGBoost's AUROC by −0.002. We note in the text that because each replicate refits on roughly half of the primary sampling units, the intervals also reflect reduced training data.
>
> We conclude that gradient boosting offers no improvement over logistic regression for this task, and the manuscript recommends a transparent regression score accordingly.

---

## Comment 8: The outcome is not a KDIGO diagnosis; one-component inclusion causes differential misclassification

**(a) Renaming.** The outcome is now called "single-visit laboratory markers of CKD", or "CKD markers", in the Abstract, Methods, and Discussion. The Methods state that it is not a KDIGO diagnosis because chronicity cannot be established, and note that "CKD" in the Stage 2 results is shorthand for these markers. The Limitations explain that transient abnormalities inflate prevalence and probably lower measured discrimination.

**(b) Components** (new; output in `outputs/stage2_outcome_components.json`):

| Group | n | Weighted prevalence of CKD markers |
|---|---|---|
| Both creatinine and UACR | 13,666 | 13.8% |
| Creatinine only | 249 | 20.6% |
| UACR only | 1,235 | 14.0% |

- Restricted to participants with both components: AUROC 0.775 (0.760–0.791) using the out-of-fold predictions, and **0.769** after refitting on that subset alone.
- Direction: missing components can only produce false negatives, which biases prevalence downward. The Limitations say this, and note that the restricted analysis changes little.

**Draft reply:**
> We agree. The outcome is now described as single-visit laboratory markers of CKD, and the Methods state that it is not a KDIGO diagnosis because the 3-month chronicity criterion cannot be applied. The Limitations note that transient abnormalities inflate prevalence and probably lower measured discrimination.
>
> Of 15,150 participants, 13,666 had both components, 249 had creatinine only, and 1,235 had urine measures only. Because the outcome is an OR of the two criteria, missing components can only produce false negatives, biasing prevalence downward. Restricted to participants with both components, prevalence was 13.8%, and AUROC was 0.775 (95% CI 0.760–0.791), or 0.769 when the model was refit on that subset. We report these results and discuss the direction of the bias in the Limitations.

---

# Minor comments

Figure and table numbers below refer to the revised manuscript. Removing Figures 6, 7, and 13 and adding 2 tables changed the numbering. Figures and appendix tables are numbered in order of first mention.

| # | Comment | Status | Change in v6 |
|---|---|---|---|
| m1 | "Prospective evaluation … in progress" in the Conclusions | Fixed | Removed from the Abstract and the paper. No such protocol exists in our materials. |
| m2 | Subgroup minimum 0.637 vs 0.638 | Fixed | All values now come from one output file. The minimum is 0.641 (adults <50 years) in both the text and Figure 10. |
| m3 | Capacity sweep: "<0.005" wrong, and the ladder holds capacity constant | Fixed + new analysis | Text gives the actual range (0.440–0.445) and describes the ladder as a robustness check over plausible configurations, explaining why. **New one-factor-at-a-time sweep** (trees 200/600/1000, depth 3/5/7, learning rate 0.01/0.05/0.10): R² 0.440–0.445 (Table S1). Code in `train_ecological_model.py` (`OFAT_SETTINGS`). |
| m4 | Feature-importance ranking between collinear features | Fixed | Ranking removed and Figure 6 deleted. Methods and Results state that the 3 features are collinear by construction (quintile is a coarsening of national rank) and that split-based importance is not interpretable. |
| m5 | Quintile predicted = observed: out-of-fold? Report to 3 decimals with n | Confirmed + fixed | Confirmed out-of-fold (`predictions_by_quintile` uses `oof_pred`). New Table 2 gives both series to 3 decimals with tract counts. Results explain why: the quintile is a model input, so out-of-fold predictions reproduce quintile means (between-quintile variance), while R² is driven by within-quintile variation between tracts. |
| m6 | Figures 7 and 13 are tables as images | Fixed | Both removed. Figure 7 is now typeset as Table 1 (all regions, R², MAE, calibration slope and intercept, Spearman). Figure 13 duplicated Table 4. The paper now has 10 figures. |
| m7 | "calibrated R²", "ground truth", "authoritative" | Fixed | None of these terms appear in v6. PLACES is described throughout as a model-based estimate of self-reported diagnosed CKD. |
| m8 | USRDS "used as priors" | Fixed | Removed. USRDS is cited only for dialysis costs in the Introduction. |
| m9 | ACS vintage of ADI vs Section 4.4 | Fixed | Verified: the 2020 ADI uses the **2016–2020** ACS 5-year estimates on 2020 block groups (Neighborhood Atlas changelog; v4 refined only the shrinkage). "ACS 2015–2019" in v5 was the vintage of the **PLACES model covariates** (PLACES 2022 dataset description). Methods state both, and the Limitations note that the 2 products share ACS inputs (2016–2019 overlap), which could inflate the association. |
| m10 | BRFSS year of the PLACES CKD measure, with citation | Fixed | Verified in the PLACES 2022 dataset description: the release uses BRFSS 2020 for 25 measures, CKD included, and BRFSS 2019 only for 4 blood pressure and cholesterol measures. Stated in Methods with the citation. |
| m11 | "Ninth leading cause of death" uncited | Fixed | Sentence removed. The Introduction now cites CDC 2023 for prevalence and awareness. |
| m12 | "Regenerated on 2026-05-09" predates the revision | Fixed | Replaced by a dated statement: all results were generated on October 17, 2026 from archived version 6.0.0 of the code. All Stage 1 and Stage 2 outputs were regenerated in this revision. |
| m13 | Northeast/West slopes <1 misinterpreted as under-prediction | Fixed | Results state that a slope <1 means the regional gradient is flatter than the national model assumes, so predictions are too extreme: over-predicting in the most-deprived tracts and under-predicting in the least-deprived. |

**Draft reply (minor comments):**
> We thank the reviewer for these detailed comments, all of which we have addressed.
>
> **(1)** The statement about a prospective evaluation has been removed.
>
> **(2)** All subgroup values are now taken from a single output file, and the minimum (0.641) is consistent throughout.
>
> **(3)** We now report the actual range (0.440–0.445) and describe the original sweep as a robustness check over a small set of configurations, explaining that it roughly holds effective capacity constant. We also added a one-factor-at-a-time sweep varying trees (200–1000), depth (3–7), and learning rate (0.01–0.10) around the main configuration; R² ranged from 0.440 to 0.445 (Table S1).
>
> **(4)** The importance ranking and the importance figure have been removed. The Methods and Results state that the 3 features are collinear by construction and that split-based importance is not interpretable.
>
> **(5)** We confirm that the predicted series is out-of-fold. Table 2 now reports both series to 3 decimals with tract counts, and the Results explain why quintile means agree closely despite an R² of 0.445: the quintile is itself a model input, so out-of-fold predictions reproduce between-quintile differences, whereas R² mainly reflects within-quintile variation between tracts.
>
> **(6)** Former Figures 7 and 13 have been removed. The Stage 1 summary is now typeset as Table 1, and the Stage 2 summary was already in Table 4.
>
> **(7)** "Calibrated R²", "ground truth", and "authoritative" no longer appear. PLACES is consistently described as a model-based estimate of self-reported diagnosed CKD.
>
> **(8)** The reference to priors has been removed.
>
> **(9)** We verified that the 2020 ADI is built from the 2016–2020 ACS 5-year estimates. The 2015–2019 vintage cited previously belongs to the covariates of the PLACES model. Both are now stated, and the Limitations note the resulting shared ACS inputs.
>
> **(10)** The PLACES 2022 release uses 2020 BRFSS data for the CKD measure. This is now stated with a citation.
>
> **(11)** The uncited sentence has been removed.
>
> **(12)** All outputs were regenerated for this revision, and the Reproducibility section states the date and code version.
>
> **(13)** Corrected as the reviewer describes.
