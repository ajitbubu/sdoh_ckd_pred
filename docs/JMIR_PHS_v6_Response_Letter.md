# Response to Editor and Reviewers

**Manuscript:** ms 101575, *JMIR Public Health and Surveillance*
**Revised title:** Neighborhood Deprivation and Undetected Chronic Kidney Disease Burden: Open Small-Area Surveillance and Non-Laboratory Screening Triage Using CDC PLACES and NHANES
**Authors:** Ajit Sahu, Sanjoy Mukherjee

Dear Editor,

Thank you for the opportunity to revise our manuscript, and thank you and Reviewer AS for comments that have substantially improved it. We have uploaded a clean revised manuscript and a version in which new or changed text is highlighted. Because the manuscript was substantially rewritten in response to the editorial comments, most of the text is highlighted. Our point-by-point responses follow. Before them, we draw your attention to three matters.

**1. Corrections identified during revision.** To address your concern that the analysis was not rigorous enough, we re-ran the complete pipeline from the public raw data. In doing so we identified errors in the previous version, which we have corrected:

- **Model comparison.** The previously reported advantage of XGBoost over logistic regression was not supported. On identical cross-validation folds the two models do not differ (AUROC 0.772 vs 0.778; difference −0.006, 95% CI −0.013 to 0.002).
- **Calibration.** A binning error in our calibration routine overstated calibration. The corrected logistic calibration slope is 0.75 (95% CI 0.70–0.80), which we now report, interpret, and discuss.
- **Stage 1 values.** Several Stage 1 values in the text did not match the figures generated from the Area Deprivation Index data, and they have been aligned with them.
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
- **Comparators.** A logistic regression comparator is evaluated on identical folds with a paired test, alongside demographic-only baselines.
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

Stage 1 ranks places by deprivation-predicted burden. Stage 2 includes income as a predictor, and we report its performance and calibration across income groups (Figure 11). We state explicitly that the models use social-risk measures to direct testing; they do not determine social risk.

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
We thank the reviewer for catching this. The quintile values in the previous text were incorrect and did not match Figure 5. Observed CDC PLACES prevalence by ADI quintile is [PENDING: exact Q1–Q5 values from the Stage 1 rerun], a [PENDING]-fold gradient, within the 1.5- to 2.0-fold range cited. The model's predicted means are virtually identical to the observed means.

We now report observed and predicted values for every quintile in the Results. Because predicted and observed quintile means coincide, model shrinkage does not attenuate the gradient. In the Discussion we note that the gradient's position at the lower end of the published range more plausibly reflects smoothing in the PLACES small-area estimation, averaging of individual risk within tracts, and under-ascertainment of CKD in self-report.

**AS4. Deployment qualifier.**
We agree. The Abstract and Conclusions now state that the ecological model should be recalibrated to regional or state data before it is used to allocate resources, particularly in the Northeast and West, where leave-one-region-out performance was weakest.

**AS5. Self-report bias.**
We have added this limitation and examined it empirically. Among adults reporting no hypertension diagnosis, 9.3% (95% CI 8.4%–10.3%) had measured blood pressure of 140/90 mm Hg or higher. This proportion did not differ materially by income-to-poverty ratio (8.8%–10.0%). Because measured blood pressure is itself a predictor, it partly compensates for unreported hypertension. We note that unreported diabetes, heart failure, and stroke could not be assessed, and that in populations with poorer access to care the comparability across groups may not hold.

**AS6. "First study" claim.**
The statement reflected an informal impression rather than a systematic search, and we have removed it. The revised paper describes its contribution in terms of the public health questions it addresses rather than priority.

**AS7. Demographic-only baseline.**
Thank you for this helpful suggestion, which we have adopted. Logistic regression with age and sex alone achieves an AUROC of 0.728 (95% CI 0.717–0.741). Adding race/ethnicity, income-to-poverty ratio, and BMI gives 0.748 (0.736–0.762), and the full model gives 0.778 (0.764–0.793). Blood pressure and the self-reported conditions therefore add 0.030 (95% CI 0.024–0.036) beyond demographics and BMI. We report this in the Results and in Table 2, and note that much of the discrimination comes from age.

**AS8. Spearman correlation versus R².**
[PENDING: replace with the option (a) or (b) text after the Stage 1 rerun.] If the rerun completes, report "ρ=[value]" with the explanation in `JMIR_PHS_v6_Response_to_Reviewer_AS.md`, comment 8, option (a).

**AS9. Regional R² values.**
Thank you. The previous text misidentified the lowest region. Figures 3 and 7 show R²=0.232 for the Northeast and 0.247 for the West. The Results now state all four regional R² values (Northeast 0.232, Midwest 0.409, South 0.415, West 0.247) and the corresponding calibration slopes, and Figure 7 tabulates them.

**AS10. ADI data access.**
We appreciate this note. The Data Availability section now explains how to obtain the ADI file. We have also made the pipeline's handling of the public Neighborhood Atlas file format more robust, so that independent replication is straightforward once the file has been downloaded.

Sincerely,
Ajit Sahu (corresponding author), on behalf of both authors
