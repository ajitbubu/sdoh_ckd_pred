# Response to Editor and Reviewers

**Manuscript:** ms 101575, *JMIR Public Health and Surveillance*
**Revised title:** Neighborhood Deprivation and Undetected Chronic Kidney Disease Burden: Open Small-Area Surveillance and Non-Laboratory Screening Triage Using CDC PLACES and NHANES
**Authors:** Ajit Sahu, Sanjoy Mukherjee

Dear Editor,

Thank you for the opportunity to revise our manuscript, and thank you and Reviewer AS for comments that have substantially improved it. We have uploaded a clean revised manuscript and a version in which new or changed text is highlighted. Because the manuscript was substantially rewritten in response to the editorial comments, most of the text is highlighted. Our point-by-point responses follow. Before them, we draw your attention to three matters.

**1. Corrections identified during revision.** To address your concern that the analysis was not rigorous enough, we re-ran the complete pipeline from the public raw data. In doing so we identified errors in the previous version, which we have corrected:

- **Model comparison.** The previously reported advantage of XGBoost over logistic regression was not supported. On identical cross-validation folds the two models do not differ (with identical imputation, AUROC difference −0.004, 95% CI −0.026 to 0.003).
- **Calibration.** A binning error in our calibration routine overstated calibration. The corrected logistic calibration slope is 0.75 (95% CI 0.70–0.80), which we now report, interpret, and discuss.
- **Stage 1 values.** Several Stage 1 values in the text did not match the figures generated from the Area Deprivation Index data. We re-ran Stage 1 from the released code with the Neighborhood Atlas file, regenerated the Stage 1 figures, and report the resulting values throughout.
- **Withdrawn analyses.** Supplementary analyses we described but had not completed (the Census-crosswalk sensitivity analysis, the feature ablations, and a Spearman correlation), references to a prospective evaluation protocol and an archived data snapshot, and the statement that race/ethnicity was not a model predictor (it is) have been removed or corrected.
- **Confidence intervals.** All confidence intervals are now design-based. They are estimated with a Rao–Wu bootstrap that resamples NHANES primary sampling units within strata.

Every number in the revised manuscript is produced by code in the public project repository. We regret these errors.

**2. Correction regarding generative AI.** A previous version of our manuscript stated that no generative AI tools were used in its preparation. That statement was incorrect, and we apologize for it. The revised manuscript includes a "Use of Generative AI" section disclosing that Claude (Anthropic) was used to help write and debug analysis code, to draft and edit manuscript text, and to check reported values against analysis outputs. The authors reviewed, edited, and verified all AI-assisted content, re-ran all analyses, and take full responsibility for the content of the article.

**3. Journal transfer preferences.** Should the manuscript ultimately not be accepted by *JMIR Public Health and Surveillance*, our transfer preferences, in order, are: (1) *Interactive Journal of Medical Research*, (2) *JMIR AI*.

---

## Response to the Editor

**E1. "The analysis is not rigorous enough for this journal", "methodological weaknesses/limitations", and "major reporting issues."**
We have substantially strengthened the analysis.

- **Uncertainty.** All Stage 2 confidence intervals are now design-based: a Rao–Wu rescaled bootstrap over NHANES primary sampling units within strata, with 1,000 replicates.
- **Calibration.** Calibration is assessed with the logistic calibration slope and calibration-in-the-large.
- **Comparators.** A logistic regression comparator is evaluated against XGBoost under identical imputation, with the cross-validation re-run inside each design-based bootstrap replicate, alongside demographic-only baselines.
- **Equity.** Performance is reported across age, sex, race/ethnicity, and income groups, with a race-free sensitivity model.
- **Reporting.** Tables now report estimates with 95% CIs, table and figure labelling errors have been corrected, and all results were regenerated from the public raw data with released code.

The corrections this process identified are listed above.

**E2. The Introduction has too much methods and not enough public health importance; the contribution list is mostly methodological.**
We rewrote the Introduction to lead with the public health problem. Up to 9 in 10 US adults with CKD are unaware of it. Testing is inexpensive, so the constraint is deciding where and in whom to offer it, and that decision became harder when CDC PLACES discontinued its tract-level CKD measure in 2024. The methodological contribution list has been replaced by two public health research questions, and methodological material has been moved to the Methods.

**E3. If the paper mainly applies new methods to questions answered by prior research, its impact may be minimal.**
We agree that the earlier framing over-emphasized methods. The revised paper addresses two applied questions that existing work does not answer:

- how agencies can continue to prioritize neighborhoods for CKD outreach now that federal tract-level CKD estimates have been discontinued;
- how well a contemporary, laboratory-free triage score performs against the current KDIGO definition of CKD, including its calibration and its performance across social-risk groups.

Comparison with existing questionnaire-based scores (SCORED and the Kshirsagar score) is now explicit in the Introduction and Discussion.

**E4. Ethical research statements are missing.**
We added an Ethical Considerations subsection to the Methods. It reports:

- the NCHS Research Ethics Review Board protocols under which NHANES data were collected (#2011-17, #2018-01, and #2021-05);
- the original informed consent;
- the deidentification and privacy safeguards;
- participant remuneration;
- the basis, under 45 CFR 46.102(e)(1), on which this secondary analysis of public, deidentified data did not require further institutional review.

**E5. It is unclear how the results align with prior evidence or constitute new information about risk assessment.**
We added a "Comparison With Prior Work" subsection that separates confirmation of prior evidence from new information.

- **Agreement with prior evidence.** The ecological deprivation gradient (1.6-fold between the least- and most-deprived quintiles) and the individual income gradient in CKD prevalence agree with prior meta-analytic evidence, which supports their validity.
- **New information about risk assessment.** We quantify how much of the national small-area CKD distribution deprivation recovers (44%) and how this varies by region. We also provide a contemporary non-laboratory triage score, benchmarked against SCORED and reported with calibration and equity measures.

**E6. List-based limitations and future directions are not appropriate.**
Both sections have been rewritten as narrative paragraphs.

**E7. Define "social risk" and how the models use it.**
In the Introduction we define social risk following Alderwick and Gottlieb (Milbank Q 2019): adverse social conditions associated with poor health, as distinct from social needs. Social risk is operationalized at the area level by the Area Deprivation Index (Stage 1) and at the individual level by the family income-to-poverty ratio (Stage 2).

Stage 1 ranks places by deprivation-predicted burden. Stage 2 includes income as a predictor, and we report its performance and calibration across income groups (Figure 10). We state explicitly that the models use social-risk measures to direct testing; they do not determine social risk.

**E8. No Conclusions section.**
A Conclusions section has been added.

**E9. Minimize bullet points.**
The revised manuscript contains no bulleted or numbered lists.

**E10. Ethical Considerations subheading with the 4 required points.**
See E4. All 4 points are addressed.

**E11. Data Availability.**
A Data Availability section has been added. It gives access URLs for NHANES and CDC PLACES. It explains that the Neighborhood Atlas Area Deprivation Index requires registration and a data use agreement, so we cannot redistribute it. It also gives the location of all code, download scripts, and derived tables in the public repository, with a Zenodo snapshot to follow on acceptance.

**E12. Conflict of Interest.**
Added: AS is employed by DataSafeguard.ai, which did not fund this work and has no commercial product based on it. SM declares no conflicts of interest.

**E13. Author Contributions (CRediT).**
Added: Conceptualization, Methodology, Formal analysis, Visualization, and Writing – original draft (AS); Software and Writing – review & editing (AS, SM); Data curation and Validation (SM).

**E14. Funding statement.**
Added: "The authors declared no financial support was received for this work."

**E15. Generative AI disclosure.**
Added. See matter 2 above, including our correction of the previous statement.

**E16. Tracked or highlighted version and JMIR style.**
A highlighted version is supplied. The manuscript follows JMIR section structure and Vancouver referencing, includes an Abbreviations section, and places supplementary tables in Multimedia Appendix 1.

---

## Response to Reviewer AS

We thank the reviewer for a careful and constructive review. Before responding point by point, we must correct the record on several elements the reviewer commended.

While re-running the complete pipeline from the public raw data for this revision, we found that the following had not been implemented in the released code:

- the feature-ablation analyses;
- the Census-crosswalk boundary-misalignment analysis;
- the Spearman correlation;
- the Makefile referenced in the Reproducibility section.

We have removed them rather than report results we cannot reproduce. We also found that, on identical cross-validation folds, the XGBoost classifier does not outperform logistic regression (AUROC 0.772 vs 0.778), and that a binning error had overstated calibration (corrected logistic calibration slope 0.75). Both are now reported accurately. All confidence intervals are now design-based. We apologize for these errors and are grateful that the review process prompted us to find them.

**AS1. Ethics/IRB statement.**
We have added an Ethical Considerations subsection. It reports the NCHS Research Ethics Review Board protocol numbers for the NHANES cycles used (#2011-17, #2018-01, and #2021-05), the original informed consent, the privacy safeguards, and the basis for exemption from further review.

**AS2. Single-measurement CKD label.**
We agree and have made this explicit in the Methods. The single-measurement eGFR/UACR definition is the convention used for national CKD prevalence estimates from NHANES, including by the CDC CKD Surveillance System (Murphy et al, Ann Intern Med 2016; Coresh et al, JAMA 2007; CDC 2023). We cite these papers and note that the convention somewhat overestimates persistent CKD, because albuminuria measured once can be transient.

**AS3. ADI quintile gradient.**
We thank the reviewer for catching this. The quintile values in the previous text were incorrect and did not match the previous version's Figure 5 (now Table 2 and Figure 4). Observed CDC PLACES prevalence by ADI quintile is 2.45%, 2.60%, 2.83%, 3.20%, and 3.90%, a 1.6-fold gradient, within the 1.5- to 2.0-fold range cited. The model's predicted means are within 0.002 percentage points of the observed means in every quintile.

We now report observed and predicted values for every quintile in the Results. Because predicted and observed quintile means coincide, model shrinkage does not attenuate the gradient. In the Discussion we note that the gradient's position at the lower end of the published range more plausibly reflects smoothing in the PLACES small-area estimation, averaging of individual risk within tracts, and under-ascertainment of CKD in self-report.

**AS4. Deployment qualifier.**
We agree. The Abstract and Conclusions now state that the ecological model should be recalibrated to regional or state data before it is used to allocate resources, particularly in the Northeast and West, where leave-one-region-out performance was weakest.

**AS5. Self-report bias.**
We have added this limitation and examined it empirically. Among adults reporting no hypertension diagnosis, 9.3% (95% CI 8.4%–10.3%) had measured blood pressure of 140/90 mm Hg or higher. This proportion did not differ materially by income-to-poverty ratio (8.8%–10.0%). Because measured blood pressure is itself a predictor, it partly compensates for unreported hypertension. We note that unreported diabetes, heart failure, and stroke could not be assessed, and that in populations with poorer access to care the comparability across groups may not hold.

**AS6. "First study" claim.**
The statement reflected an informal impression rather than a systematic search, and we have removed it. The revised paper describes its contribution in terms of the public health questions it addresses rather than priority.

**AS7. Demographic-only baseline.**
Thank you for this helpful suggestion, which we have adopted. Logistic regression with age and sex alone achieves an AUROC of 0.728 (95% CI 0.717–0.741). Adding race/ethnicity, income-to-poverty ratio, and BMI gives 0.748 (0.736–0.762), and the full model gives 0.778 (0.764–0.793). Blood pressure and the self-reported conditions therefore add 0.030 (95% CI 0.024–0.036) beyond demographics and BMI. We report this in the Results and in Table 4, and note that much of the discrimination comes from age.

**AS8. Spearman correlation versus R².**
We thank the reviewer for this question, and we must first correct the value. The Spearman correlation of 0.71 reported previously was not produced by the released code. Re-running Stage 1 from the released code, the Spearman correlation between out-of-fold predicted and observed tract prevalence is 0.67, and we now report this value in the Results. The two statistics are not contradictory. R² is on a squared scale, and the square root of the cross-validated R² (0.445) is 0.67, close to the rank correlation. Rank correlation is the more directly relevant measure when the model is used to order tracts for prioritization, and we now say so in the Results.

**AS9. Regional R² values.**
Thank you. The previous text misidentified the lowest region. Re-running Stage 1 from the released code gives R²=0.232 for the Northeast and 0.251 for the West. The Results now state all four regional R² values (Northeast 0.232, Midwest 0.409, South 0.416, West 0.251) and the corresponding calibration slopes, and Table 1, generated from the same run, tabulates them.

**AS10. ADI data access.**
We appreciate this note. The Data Availability section now explains how to obtain the ADI file. We have also made the pipeline's handling of the public Neighborhood Atlas file format more robust, so that independent replication is straightforward once the file has been downloaded.

---

## Response to Reviewer FE

We thank the reviewer for a rigorous and constructive review that has substantially improved the manuscript. Several of the problems identified (the repository, the boundary-misalignment analysis, the calibration bin, the sex gap, and the model comparison) are errors that we had also found while re-running the pipeline for this revision, and we have corrected them as described below.

**FE1. Cited repository does not contain the pipeline; reproducibility cannot be verified**
We thank the reviewer for checking the repository, and we apologize: reference [23] pointed to an earlier repository from a previous synthetic-cohort version of the project, and the described pipeline was not in it. The revised manuscript cites the correct repository (github.com/ajitbubu/sdoh_ckd_pred) and a Zenodo archive of the exact version that produced the reported results (DOI [ZENODO DOI]), deposited at submission so that it can be inspected during review. The pipeline's metric files (stage1_metrics.json, stage2_metrics.json, and the supplementary analysis outputs) are supplied as Multimedia Appendix 2. We have corrected the sentinel value in the text (the pipeline records adi_source: real_neighborhood_atlas). We agree that silent substitution was poor design: the Stage 1 script now stops with an error if the Neighborhood Atlas file is absent, and synthetic data can be used only with an explicit testing flag. We also thank the reviewer for flagging the credentials file; it has been removed and the affected credentials are being rotated.

**FE2. Boundary-misalignment analysis is arithmetically impossible**
The reviewer is correct, and we are grateful for the careful check. On re-auditing the pipeline we found that the boundary-misalignment analysis described in Section 3.1.6 and Supplementary Table S1 had not been implemented, and the figures reported for it were not produced by our code. We have removed the analysis and the table. The revised manuscript reports only what the code produces: 60,945 of 72,337 PLACES tracts (84.3%) linked to ADI tracts, and 24,450 of 85,395 ADI tracts (28.6%) had no PLACES match. We identify a crosswalk-based reallocation as a limitation and future step, not as a completed analysis.

**FE3. The "chaining" of the two stages is not implemented**
We agree, and we have taken the reviewer's second option. The novelty claim has been removed. The Abstract and Methods now describe two separate analyses that share a design but are not linked: Stage 1 predictions are not used as inputs, priors, or offsets in Stage 2, and the stages share no records. We state that linking them would require participants' census tracts, which are available only as restricted data through the NCHS Research Data Center, and the Limitations note that we therefore could not test whether combining tract prioritization with individual triage improves detection.

**FE4. PLACES measures self-reported diagnosed CKD, a different construct, with socially patterned under-ascertainment**
We thank the reviewer for this important point, which we have adopted throughout. The Abstract, Methods, Discussion, Limitations, and Conclusions now state that the Stage 1 outcome is the prevalence of self-reported diagnosed CKD, a different construct from the laboratory markers used in Stage 2.

To quantify the gap and test the hypothesized direction of bias, we used the NHANES item corresponding to the BRFSS question behind PLACES. Self-reported kidney disease was 3.0%, close to the 2.96% PLACES mean, against 14.1% with laboratory markers. Only 13.1% of adults with CKD markers were aware of it, confirming the magnitude the reviewer describes.

However, awareness was not lower at lower income (16.2% at income-to-poverty ratio <1.3 vs 12.9% at ≥3.5), and the income gradient in self-reported disease (ratio 1.91) was steeper than that in CKD markers (1.58). In these data, then, under-ascertainment did not bias the socioeconomic gradient toward the null.

Because individual income is not area deprivation, and self-report may preferentially capture advanced disease, we do not claim this settles the direction of bias at the tract level. The revised Limitations state that the direction and size of the bias are uncertain and that the Stage 1 gradient should be read as a gradient in diagnosed CKD.

**FE5. Calibration slope is an artifact of a degenerate bin**
The reviewer is right. A binning error created an eleventh bin containing a single participant, which inflated the reported slope; this has been corrected. We now report the logistic calibration slope (0.75, 95% CI 0.70–0.80) and intercept (+0.05, −0.02 to 0.12) from the regression of the outcome on the logit of predicted risk, and calibration-in-the-large. We also report a flexible spline-based calibration curve with design-based pointwise 95% CIs (Figure 8), ICI (0.022), E50 (0.019), and E90 (0.030), and the Brier skill score against the prevalence-only model (0.147, 95% CI 0.123–0.172). Figure 8 now has exactly 10 deciles, with bin sizes in Table S3. As the reviewer notes, the curve departs from the diagonal above a predicted risk of about 0.3, close to the deployed threshold, and we discuss the need for recalibration before deployment.

**FE6. Sex disparity understated; AUROC parity ≠ equitable performance**
We agree on both points and thank the reviewer. The sex difference is 0.07 (0.81 vs 0.74, non-overlapping CIs), and both passages have been corrected. The count of race/ethnicity categories (six) has been corrected, and we now note that the maximum subgroup AUROC comes from the smallest group (n=845).

We have also added the analysis the reviewer requested (Table S6): sensitivity, specificity, PPV, NPV, proportion flagged, and subgroup calibration at the deployed threshold, with design-based CIs. Calibration-in-the-large was close to zero in all groups, but sensitivity differed substantially: 11.8% in adults younger than 50 vs 68.1% at 65 or older, and 27.6% among Mexican American vs 55.4% among non-Hispanic Black adults.

We have removed the claim of equitable screening performance. The Abstract, Discussion, and Conclusions now state that similar AUROC does not imply similar performance at a fixed threshold, and that thresholds should be set and checked locally for each population served.

**FE7. XGBoost vs LR comparison invalid (DeLong assumptions; different imputation)**
We agree with both points and have replaced the comparison. DeLong's test has been removed, and no P values are reported. XGBoost and logistic regression are now compared under the same median imputation fitted within each training fold, alongside the primary XGBoost model with native missing-value handling. Uncertainty is estimated as the reviewer suggested, by re-running the full 5-fold cross-validation inside each of 1,000 bootstrap replicates that resample NHANES primary sampling units within strata.

Under identical imputation, the AUROC difference (XGBoost minus logistic regression) was −0.004 (95% CI −0.026 to 0.003). For the primary XGBoost model it was −0.006 (−0.027 to 0.002), and the imputation strategy itself changed XGBoost's AUROC by −0.002. We note in the text that because each replicate refits on roughly half of the primary sampling units, the intervals also reflect reduced training data.

We conclude that gradient boosting offers no improvement over logistic regression for this task, and the manuscript recommends a transparent regression score accordingly.

**FE8. The outcome is not a KDIGO diagnosis; one-component inclusion causes differential misclassification**
We agree. The outcome is now described as single-visit laboratory markers of CKD, and the Methods state that it is not a KDIGO diagnosis because the 3-month chronicity criterion cannot be applied. The Limitations note that transient abnormalities inflate prevalence and probably lower measured discrimination.

Of 15,150 participants, 13,666 had both components, 249 had creatinine only, and 1,235 had urine measures only. Because the outcome is an OR of the two criteria, missing components can only produce false negatives, biasing prevalence downward. Restricted to participants with both components, prevalence was 13.8%, and AUROC was 0.775 (95% CI 0.760–0.791), or 0.769 when the model was refit on that subset. We report these results and discuss the direction of the bias in the Limitations.

**Minor comments.**
We thank the reviewer for these detailed comments, all of which we have addressed.

**(1)** The statement about a prospective evaluation has been removed.

**(2)** All subgroup values are now taken from a single output file, and the minimum (0.641) is consistent throughout.

**(3)** We now report the actual range (0.440–0.445) and describe the original sweep as a robustness check over a small set of configurations, explaining that it roughly holds effective capacity constant. We also added a one-factor-at-a-time sweep varying trees (200–1000), depth (3–7), and learning rate (0.01–0.10) around the main configuration; R² ranged from 0.440 to 0.445 (Table S1).

**(4)** The importance ranking and the importance figure have been removed. The Methods and Results state that the 3 features are collinear by construction and that split-based importance is not interpretable.

**(5)** We confirm that the predicted series is out-of-fold. Table 2 now reports both series to 3 decimals with tract counts, and the Results explain why quintile means agree closely despite an R² of 0.445: the quintile is itself a model input, so out-of-fold predictions reproduce between-quintile differences, whereas R² mainly reflects within-quintile variation between tracts.

**(6)** Former Figures 7 and 13 have been removed. The Stage 1 summary is now typeset as Table 1, and the Stage 2 summary was already in Table 4.

**(7)** "Calibrated R²", "ground truth", and "authoritative" no longer appear. PLACES is consistently described as a model-based estimate of self-reported diagnosed CKD.

**(8)** The reference to priors has been removed.

**(9)** We verified that the 2020 ADI is built from the 2016–2020 ACS 5-year estimates. The 2015–2019 vintage cited previously belongs to the covariates of the PLACES model. Both are now stated, and the Limitations note the resulting shared ACS inputs.

**(10)** The PLACES 2022 release uses 2020 BRFSS data for the CKD measure. This is now stated with a citation.

**(11)** The uncited sentence has been removed.

**(12)** All outputs were regenerated for this revision, and the Reproducibility section states the date and code version.

**(13)** Corrected as the reviewer describes.

Sincerely,
Ajit Sahu (corresponding author), on behalf of both authors
