# Response to Reviewer AS: JMIR Public Health & Surveillance (ms 101575)

This file contains the reviewer's 10 minor comments, what was changed in v6 (`CKD_Paper_JMIR_PHS_v6_revised.docx`), and a draft reply for each. Fill in or adjust the replies before pasting them into the response letter. The editorial comments are handled separately in `JMIR_PHS_v6_Editorial_Response.md`.

---

## ⚠️ Read first: the reviewer praised analyses that v6 no longer contains

The reviewer's general comments commend several things, and some of them are not in v6:

| Commended item | Status |
|---|---|
| Feature ablations | Removed: no code existed |
| Boundary-misalignment (crosswalk) analysis | Removed: no code existed |
| End-to-end reproducibility via a Makefile | No Makefile exists |
| Logistic-regression comparator "with formal statistical testing" | Kept, but the result is reversed: there is no XGBoost advantage |
| Spearman correlation (comment 8) | Removed: no code existed |

The reviewer will see these changes in the highlighted manuscript. The response letter has to say so openly at the top. A reply that thanks the reviewer for praising analyses which have since been withdrawn, without explaining why, would damage credibility with both the reviewer and the editor.

**Draft opening paragraph for the reply to Reviewer AS:**

> We thank the reviewer for a careful and constructive review. Before responding point by point, we must correct the record on several elements the reviewer commended. While re-running the complete pipeline from the public raw data for this revision, we found that the feature-ablation and Census-crosswalk boundary-misalignment analyses described in the previous version, the Spearman correlation, and the Makefile referenced in the Reproducibility section had not been implemented in the released code. We have removed them rather than report results we cannot reproduce.
>
> We also found that, on identical cross-validation folds, the XGBoost classifier does not outperform logistic regression (AUROC 0.772 vs 0.778; difference −0.006, 95% CI −0.013 to 0.002). The previously reported advantage was incorrect.
>
> In addition, a binning error had overstated calibration. The corrected logistic calibration slope is 0.75, which we now report and discuss.
>
> All results in the revised manuscript are produced by code in the public repository, and all confidence intervals are now design-based. They are estimated with a Rao–Wu bootstrap that resamples NHANES primary sampling units within strata. We apologize for these errors and are grateful that the revision process prompted us to find them.

---

## Point-by-point

### Comment 1: Ethics/IRB statement with the NCHS protocol number

**Change:** We added a *Methods › Ethical Considerations* subsection. It gives the NCHS Research Ethics Review Board protocols: #2011-17 for data collected before October 26, 2017; #2018-01 for October 26, 2017 to March 2020; and #2021-05 for 2021–2023, all verified against the CDC NHANES ERB page. It also covers original informed consent, deidentification and privacy, participant remuneration, and why the secondary analysis of public, deidentified data does not require further IRB review under 45 CFR 46.102(e)(1).

**Draft reply:**
> Thank you. We have added an Ethical Considerations subsection to the Methods. It reports the NCHS Research Ethics Review Board protocol numbers covering the NHANES cycles used (#2011-17, #2018-01, and #2021-05), the original informed consent, the deidentification and privacy safeguards, and the basis for our exemption from further review.

### Comment 2: Single-measurement CKD label as a recognized NHANES convention, with citations

**Change:** The Methods outcome paragraph now states that the KDIGO ≥3-month persistence criterion cannot be applied. It explains that the single-measurement definition is the established convention for national NHANES CKD prevalence estimates, including those of the CDC CKD Surveillance System, and cites:

- CDC, *Chronic Kidney Disease in the United States, 2023*
- Murphy D et al, CDC CKD Surveillance Team, *Ann Intern Med* 2016;165(7):473-481, PMID 27479614. This paper uses a "1-time" UACR and names single measurement as a limitation.
- Coresh J et al, *JAMA* 2007;298(17):2038-2047, PMID 17986697. This paper estimated persistence of albuminuria from NHANES III repeat visits.

The paragraph also notes that the convention somewhat overestimates persistent CKD, mainly through transient albuminuria.

**Draft reply:**
> We agree and have made this explicit in the Methods. The single-measurement eGFR/UACR definition is the convention used for national CKD prevalence estimates from NHANES, including by the CDC CKD Surveillance System (Murphy et al, Ann Intern Med 2016; Coresh et al, JAMA 2007; CDC 2023). We now cite these papers and note that the convention somewhat overestimates persistent CKD because albuminuria measured once can be transient.

### Comment 3: Quintile gradient (~1.3×) smaller than the cited 1.5–2.0×; report observed by quintile and explain

**Important correction:** The "~2.6% to ~3.4%" values in the previous text were wrong. They did not match the previous version's own Figure 5. The figure, generated from the real ADI data, shows observed PLACES prevalence of about 2.45%, 2.60%, 2.83%, 3.20%, and 3.90% for Q1 to Q5. That is a **1.6-fold** gradient, within the cited range, at its lower end. Predicted values are virtually identical to observed in every quintile.

**Change:**

- **Results:** report the observed prevalence for all 5 quintiles alongside the predicted values. They state that the model did not attenuate the gradient at the quintile level, although it compresses extremes at the level of individual tracts (predicted range about 2%–5% vs observed 0.5%–14.4%).
- **Discussion:** the gradient sits at the lower end of the published range, and model shrinkage is ruled out as the cause because predicted and observed quintile means coincide. The more plausible contributors are:
  - smoothing inherent in PLACES multilevel small-area estimation, which pulls tract estimates toward values expected from their demographic composition;
  - within-tract averaging of individual risk;
  - under-ascertainment of CKD in self-report, which may vary with deprivation.

**Draft reply:**
> We thank the reviewer for catching this. The quintile values in the previous text were incorrect and did not match Figure 5. The observed PLACES prevalence by ADI quintile is approximately 2.45%, 2.60%, 2.83%, 3.20%, and 3.90%, a 1.6-fold gradient, within the 1.5- to 2.0-fold range cited, and the model's predicted means are virtually identical. We now report observed and predicted values for every quintile in the Results. Because predicted and observed quintile means coincide, model shrinkage does not attenuate the gradient. In the Discussion we note that its position at the lower end of the published range more plausibly reflects smoothing in the PLACES small-area estimation, within-tract averaging, and under-ascertainment of CKD in self-report.

**Author check:** The quintile values were read from the bar heights in Figure 5, so the text says "approximately". After re-running Stage 1 with the real ADI file, take the exact values from `ckd_pipeline/outputs/stage1_predictions_by_quintile.csv`.

### Comment 4: Qualify "suitable for population-health deployment" in the Abstract and Conclusions with region-stratified recalibration

**Change:** v6 no longer uses the phrase "suitable for population-health deployment".

- **Abstract Conclusions:** now say the deprivation model supports prioritizing neighborhoods "provided it is recalibrated by region before deployment". The Stage 2 sentence already requires local recalibration.
- **Conclusions section:** adds that "the model should be recalibrated to regional or state data before it is used to allocate resources, particularly in the Northeast and West."
- **Results:** report all four leave-one-region-out R² values and calibration slopes, with the correct interpretation of a slope below 1.

**Draft reply:**
> We agree. The Abstract and Conclusions now state that the ecological model should be recalibrated to regional or state data before it is used to allocate resources, particularly in the Northeast and West, where leave-one-region-out performance was weakest.

### Comment 5: Self-report recall/reporting bias as a limitation, relevant to the equity claims

**Change:**

- **Limitations:** a new paragraph on recall and reporting bias in the 4 self-reported diagnoses, and on how awareness of a diagnosis depends on access to care.
- **New analysis:** among adults reporting no hypertension diagnosis, **9.3% (95% CI 8.4%–10.3%)** had measured blood pressure ≥140/90 mm Hg. This proportion was similar across income groups: 9.7%, 10.0%, and 8.8% for PIR <1.3, 1.3–3.49, and ≥3.5. Measured blood pressure is itself a predictor and partly offsets missed diagnoses.
- **Stated limits of the check:** we could not assess unreported diabetes, heart failure, or stroke, or differences by insurance status, and comparability across groups may not hold where access is worse than the national average.

**Draft reply:**
> We have added this limitation and examined it empirically. Among adults reporting no hypertension diagnosis, 9.3% had measured blood pressure of 140/90 mm Hg or higher, and this did not differ materially by income-to-poverty ratio (8.8%–10.0%). Because measured blood pressure is itself a predictor, it partly compensates for unreported hypertension. We note that unreported diabetes, heart failure, and stroke could not be assessed and that in populations with poorer access to care, comparability across groups may not hold.

### Comment 6: Basis for "the first study … to chain a tract-level ecological model into a patient-level classifier"

**Change:** No systematic literature search was performed, so the claim has been **removed**, together with the methodological contribution list (the editor asked for this too). v6 frames the contribution around public health questions, and the Discussion says explicitly that the deprivation gradient itself is not new.

**Draft reply:**
> The statement reflected an informal impression, not a systematic search, and we have removed it. The revised Introduction and Discussion describe the contribution in terms of the public health questions addressed, not priority.

### Comment 7 (optional): Demographic-only baseline

**Change:** We added nested logistic regression baselines on the same folds, with design-based CIs.

| Predictors | AUROC (95% CI) |
|---|---|
| Age + sex | 0.728 (0.717–0.741) |
| + race/ethnicity, PIR, BMI | 0.748 (0.736–0.762) |
| Full model (adds blood pressure + self-reported conditions) | 0.778 (0.764–0.793) |

- **Gain of the full model over age + sex:** +0.050 (0.043–0.057).
- **Gain from blood pressure and self-reported conditions alone:** +0.030 (0.024–0.036).

The new values appear in the Methods, in the Results, and in two new rows of Table 2.

**Draft reply:**
> Thank you for this helpful suggestion, which we have adopted. Age and sex alone achieve an AUROC of 0.728, adding race/ethnicity, income-to-poverty ratio, and BMI gives 0.748, and the full model gives 0.778. Blood pressure and self-reported conditions therefore add 0.030 (95% CI 0.024–0.036) beyond demographics and BMI. We report this in the Results and Table 2 and note that much of the discrimination comes from age.

### Comment 8: Why Spearman (0.71) exceeds R² (0.45)

**Change:** The Spearman value in the previous version was not produced by the archived code and has been removed (see the opening paragraph). `src/train_ecological_model.py` now computes `spearman_rho_oof` on the out-of-fold predictions and writes it to `outputs/stage1_metrics.json`, so the value will be available when Stage 1 is re-run with the real ADI file.

**Two options for the authors:**

- **(a) Recommended, if you re-run Stage 1 before resubmission.** Add the value back to Results › Stage 1 with this explanation (fill in ρ):
  > *The Spearman rank correlation between out-of-fold predicted and observed tract prevalence was ρ=[value]. Rank correlation exceeds R² because it measures only whether tracts are ordered correctly, whereas R² also penalizes the distance between predicted and observed values; the model compresses extreme tracts toward the mean (Figure 1), which lowers R² more than it lowers rank agreement. For prioritizing tracts, rank agreement is the more relevant measure.*
- **(b) If you do not re-run.** Use the reply below.

**Draft reply (option b):**
> We thank the reviewer for this point. On re-auditing the code for this revision we found that the Spearman correlation reported previously was not produced by the released pipeline, so we have removed it. The Stage 1 script now computes rank correlation on out-of-fold predictions. Conceptually, rank correlation exceeds R² because it measures only whether tracts are correctly ordered, whereas R² also penalizes the distance between predicted and observed values, and the model compresses extreme tracts toward the mean.

### Comment 9: Leave-one-region-out values and the Figure 3 caption

**Change:** The previous text and caption were inconsistent with each other and with the figure. Figure 3 and Figure 7 show the Northeast as the minimum (0.232), not the West (0.247). The v6 Results now state all four values, Northeast 0.232, Midwest 0.409, South 0.415, and West 0.247, with the four calibration slopes (0.69, 0.91, 1.14, 0.81). The Figure 3 caption no longer repeats rounded values. Figure 7 lists all four regional R² values.

**Draft reply:**
> Thank you. The previous text misidentified the lowest region. Figures 3 and 7 show R²=0.232 for the Northeast and 0.247 for the West. The Results now state all four regional R² values (Northeast 0.232, Midwest 0.409, South 0.415, West 0.247) and calibration slopes, and Figure 7 tabulates them.

### Comment 10 (note): Registration-gated ADI file

**Change:** No change is required. The Data Availability section explains the Neighborhood Atlas registration and data use agreement and why the file cannot be redistributed. We also fixed the real-file loader in `src/train_ecological_model.py`: it now coerces Neighborhood Atlas suppression codes to missing and derives the quintile from the national rank. We added `src/fetch_places.py` so PLACES is downloaded automatically.

**Draft reply:**
> We appreciate this note. The Data Availability section now explains how to obtain the ADI file, and we have made the pipeline's handling of the public Neighborhood Atlas file format more robust so that independent replication is straightforward once the file is downloaded.

---

## New outputs for this reviewer

| File | Content |
|---|---|
| `ckd_pipeline/outputs/stage2_demographic_baselines.json` | Comment 7: nested LR baselines with design-based CIs |
| `ckd_pipeline/outputs/stage2_unreported_hypertension.json` | Comment 5: measured hypertension among adults reporting no diagnosis, by PIR |
| `stage1_metrics.json → spearman_rho_oof` | Comment 8: produced on the next Stage 1 run with the real ADI file |

New references added to the manuscript: Murphy et al 2016 (PMID 27479614) and Coresh et al 2007 (PMID 17986697), both verified in PubMed.
