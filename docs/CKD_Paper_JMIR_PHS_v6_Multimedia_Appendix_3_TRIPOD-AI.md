# Multimedia Appendix 3. TRIPOD+AI checklist for the Stage 2 prediction model

Checklist items from Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ 2024;385:e078378. The study develops and internally evaluates (by cross-validation) a diagnostic prediction model, so items marked D, E, and D;E apply. Locations refer to sections of the revised manuscript; "Appendix 1" is Multimedia Appendix 1. Stage 1 is an ecological analysis of area-level prevalence, not an individual prediction model, and is not covered by this checklist.

| Section | Item | Reported in |
|---|---|---|
| Title | 1 | Title |
| Abstract | 2 | Abstract |
| Background | 3a | Introduction, paragraphs 1 and 3 (healthcare context, diagnostic purpose, existing models: SCORED, Kshirsagar score, Kidney Failure Risk Equation) |
| | 3b | Introduction, paragraph 3; Discussion, "Public Health Implications" (target population: US adults without recent kidney testing; intended users: health departments and community screening programs) |
| | 3c | Introduction, paragraph 2 (socioeconomic inequalities in CKD) |
| Objectives | 4 | Introduction, final paragraph; Abstract, Objective |
| Data | 5a | Methods, "Study Design and Data Sources" and "Stage 2" (NHANES, nationally representative survey) |
| | 5b | Methods, "Stage 2" (January 2017–March 2020 and August 2021–August 2023) |
| Participants | 6a | Methods, "Stage 2" (general US civilian noninstitutionalized population; NHANES mobile examination centers) |
| | 6b | Methods, "Stage 2" (adults ≥18 years with serum creatinine or urine albumin and creatinine) |
| | 6c | Not applicable: treatments are not model inputs; self-reported diagnoses are predictors (Methods, "Stage 2") |
| Data preparation | 7 | Methods, "Stage 2" (blood pressure averaging, coding of refused or unknown responses, UACR calculation); preparation was identical across groups |
| Outcome | 8a | Methods, "Stage 2" outcome paragraph (single-visit eGFR <60 mL/min/1.73 m² by race-free CKD-EPI 2021 or UACR ≥30 mg/g; assessed at the examination; same method in all groups) |
| | 8b | Not applicable: laboratory measurement, no subjective interpretation |
| | 8c | Not applicable: laboratory outcome measured independently of the predictors |
| Predictors | 9a | Methods, "Stage 2" (predictors limited to information available without laboratory testing; fixed in advance) |
| | 9b | Methods, "Stage 2" (definitions of all 11 predictors) |
| | 9c | Not applicable: no subjective interpretation |
| Sample size | 10 | Methods, "Stage 2" (fixed by available data; about 180 outcome events per parameter) |
| Missing data | 11 | Methods, "Stage 2" (median imputation within training folds; multiple-imputation sensitivity analysis); Appendix 1, Table S2 |
| Analytical methods | 12a | Methods, "Stage 2" (stratified 5-fold cross-validation; no separate test set) |
| | 12b | Methods, "Stage 2" (standardization, one-hot encoding of race/ethnicity; linear terms) |
| | 12c | Methods, "Stage 2" (L2 logistic regression, C=1.0, fixed in advance; XGBoost comparator; internal validation by cross-validation) |
| | 12d | Not applicable: no clusters such as hospitals; survey design handled with design-based CIs (Methods, "Stage 2") |
| | 12e | Methods, "Stage 2" (discrimination, calibration measures, decision curves, operating points; model comparison with refit bootstrap) |
| | 12f | Not applicable: no model updating was performed; the need for local recalibration is discussed |
| | 12g | Appendix 1, Table S7 (formula with coefficients); code in the public repository |
| Class imbalance | 13 | Methods, "Stage 2" (no class-imbalance methods; the previous version's balanced class weights were removed) |
| Fairness | 14 | Methods, "Stage 2" (performance and calibration by age, sex, race/ethnicity, and income; race-free sensitivity model) |
| Model output | 15 | Methods, "Stage 2" (predicted probabilities; operating points at prespecified specificity targets of 95%, 90%, 80%, 70%, and 60%) |
| Training versus evaluation | 16 | Not applicable: development and evaluation use the same data through cross-validation |
| Ethical approval | 17 | Methods, "Ethical Considerations" |
| Funding | 18a | Funding |
| Conflicts of interest | 18b | Conflicts of Interest |
| Protocol | 18c | [AUTHORS: confirm, then state in the manuscript, e.g., "No study protocol was prepared."] |
| Registration | 18d | [AUTHORS: confirm, then state in the manuscript, e.g., "The study was not registered."] |
| Data sharing | 18e | Data Availability |
| Code sharing | 18f | Methods, "Reproducibility"; Data Availability |
| Patient and public involvement | 19 | [AUTHORS: confirm, then state in the manuscript, e.g., "Patients and the public were not involved in the design, conduct, or reporting of this study."] |
| Participants | 20a | Methods, "Stage 2" (17,846 adults; 15,150 analyzed); Results, "Stage 2" (2,706 with the outcome) |
| | 20b | Results, "Stage 2"; Table 3; Appendix 1, Table S2 |
| | 20c | Not applicable: no separate evaluation dataset |
| Model development | 21 | Results, "Stage 2"; Table 3 (15,150 participants, 2,706 events; 5 cross-validation folds) |
| Model specification | 22 | Appendix 1, Table S7; public repository (freely available) |
| Model performance | 23a | Results, "Stage 2"; Table 4; Figures 6–10; Appendix 1, Tables S3–S6 |
| | 23b | Not applicable: no clusters |
| Model updating | 24 | Not applicable: no model updating |
| Interpretation | 25 | Discussion, "Principal Findings", "Comparison With Prior Work", and "Public Health Implications" (including fairness) |
| Limitations | 26 | Discussion, "Limitations" |
| Usability | 27a | Appendix 1, Table S7 (values used for missing predictors); Discussion, "Public Health Implications" |
| | 27b | Discussion, "Public Health Implications" (applied by program staff at intake, in pharmacies, or at community events) |
| | 27c | Discussion, "Future Directions" |
