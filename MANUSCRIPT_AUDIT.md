# Manuscript Audit — Changes Required for NHANES + Linked Mortality Rebuild

Audit of `_ms_plain.md` for every claim, number, or framing element that must
change once we move from the synthetic simulator to NHANES (cycles 2003-2018)
linked to the NCHS Public-use Linked Mortality File. Line numbers reference
`_ms_plain.md`.

**Major paper-identity changes from this pivot:**
- Outcome: CKD progression (Stage 2-3 → Stage 4-5 in 24 months) → **all-cause mortality** at 5-year horizon among adults with baseline Stage 2-3 CKD.
- Setting: rural underserved → **nationally representative US adult population** (NHANES).
- Cohort: synthetic N=47,832 → **NHANES analytic cohort, expected ~2,500-5,000 adults with Stage 2-3 CKD across 8 cycles**.
- SDOH layer: ZCTA-level aggregates → **individual-level questionnaire-based SDOH** (poverty income ratio, education, food security score, insurance, employment, housing). This *resolves* the ecological-bias concern.
- Pilot deployment + cost-effectiveness: dropped or reframed as Discussion-only illustration.
- Native American framing: dropped (NHANES race/ethnicity uses RIDRETH3: Mexican American, Other Hispanic, Non-Hispanic White, Non-Hispanic Black, Non-Hispanic Asian, Other/Multi-racial — no separate Native American category in standard NHANES).
- Race-free eGFR: switch to CKD-EPI 2021 (per Eneanya 2019 ref [15], already in your bibliography).

Categories:
- **FRAMING** — wording that conflicts with CRIC's multi-site academic-center origin
- **N** — cohort size numbers that will drop from 47,832/12,441/18,347 to ~CRIC scale (~5,500 total, partitioned)
- **AUROC** — performance numbers that will be regenerated from CRIC results
- **SHAP** — feature importance percentages that were hand-coded into the simulator
- **PILOT** — projected pilot deployment numbers that need reframing or removal
- **COST** — cost-effectiveness numbers downstream of pilot
- **SDOH** — neighborhood-level SDOH claims (ZCTA, food desert, walkability) that PUF doesn't support
- **METHODS** — methodological claims about the synthetic generator
- **FACT-FIX** — a claim that was already false vs. the synthetic code (8.3% exclusion)

---

## Title and Abstract

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 1 | "AI-Enabled Early Detection of Chronic Kidney Disease in **Underserved** Communities" | FRAMING | Change to "...in a Diverse Multi-Site CKD Cohort" or similar. Drop "Underserved" since CRIC is academic-center. |
| 9-10 | "Underserved populations, including African American, Hispanic, and **Native American** communities" | FRAMING | Drop "Native American" — CRIC has minimal NA representation. Keep AA/Hispanic. |
| 22 | "underserved rural communities" | FRAMING | Replace with "racial/ethnic minority and lower-SES subgroups within a multi-site CKD cohort" |
| 24 | "synthetic patient cohort (N=47,832)" | N + METHODS | Replace with CRIC PUF cohort size and selection criteria |
| 27 | "USRDS 2023 Annual Data Report, CDC PLACES 2024" | METHODS | Drop these as data sources. Replace with "CRIC public-use file (NIDDK Central Repository)". |
| 31 | "external validation cohort (N=12,441)" | N | Replace with held-out CRIC partition |
| 32 | "synthetic rural cohort (N=18,347 Stage 1-3 CKD patients)" | PILOT + FRAMING + N | Reframe pilot as illustrative simulation OR drop. Cannot be done on CRIC same way. |
| 36 | "AUROC of 0.87 (95% CI 0.85-0.89)" | AUROC | Regenerate from CRIC. Likely 0.72-0.80 range. |
| 38 | "outperforming a clinical-feature-only baseline by 8.3 percentage points (AUROC 0.80; P\<.001)" | AUROC | Regenerate. Gap will likely shrink. |
| 39-40 | "eGFR slope (18.4%), baseline eGFR (15.2%), and baseline albuminuria (12.8%)" | SHAP | Regenerate from real SHAP output |
| 40 | "SDOH features contributing 23% of model explanatory power" | SHAP | Regenerate. With PUF-limited SDOH (education, income, insurance only), this percentage will fall. |
| 42-43 | "32 percentage-point improvement in early detection rates, a 28 percentage-point increase in nephrology referrals" | PILOT | Reframe or drop |
| 43 | "31.9% relative reduction in Stage 5 progression rates" | PILOT | Reframe or drop |
| 45 | "BCR was 3.75:1" | COST | Reframe or drop with pilot |
| 50 | "underserved rural communities" | FRAMING | Same as line 22 |

---

## Introduction

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 72 | "African American, Hispanic, and Native American populations" | FRAMING | Drop "Native American" |
| 75 | "In rural regions, geographic isolation further limits nephrology access, with some counties lacking kidney specialist services within 100 miles" | FRAMING | Either drop entirely or rewrite as motivating context, not as the study setting |
| 88 | "early-stage CKD screening in underserved populations" | FRAMING | Soften to "early-stage CKD screening with attention to socioeconomic risk factors" |

---

## Methods → Study Design / Synthetic Cohort Generation

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 140-148 | Entire "Study Design" paragraph describing synthetic data generation | METHODS | **Rewrite.** Replace with: "We used the Chronic Renal Insufficiency Cohort (CRIC) public-use file from the NIDDK Central Repository [cite]. CRIC is a multi-center prospective observational cohort..." |
| 144 | "USRDS 2023, CDC PLACES 2024, published CKD progression literature" | METHODS | Drop as data sources |
| 157 | "synthetic cohort N=47,832" (Figure 1 caption) | N + METHODS | Update caption to CRIC cohort size |
| 165-180 | Entire "Synthetic Cohort Generation" section | METHODS | **Replace** with new "Cohort Definition" section describing CRIC inclusion/exclusion: Stage 2-3 at baseline (eGFR 30-89), at least one follow-up visit within 24 months, etc. |
| 170 | "Racial/ethnic composition (African American 23.1%, Hispanic/Latino 13.8%, White 59.2%, other 3.9%)" | FRAMING | Replace with CRIC actual demographics (roughly 42% Black, 13% Hispanic, 42% White per CRIC public reports) |
| 173 | "ADI quintile distributions from the 2020 national dataset" | SDOH | Drop unless we escalate to LAF for ZIP-level linkage |
| 175-176 | "An independent synthetic external validation cohort (N=12,441) was generated using the same parameterization" | METHODS | Replace with CRIC partition (e.g., chronological hold-out by enrollment date, or site-stratified hold-out) |
| 177-180 | Pilot cohort description | PILOT + N | Decide: reframe pilot as illustrative or drop |

---

## Methods → Data Integration Framework (lines 182-198)

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 192-198 | "Channel 3 comprises ZCTA-level SDOH features from CDC PLACES, the US Census Bureau American Community Survey, the ADI, and the USDA Food Access Research Atlas, including food desert status, housing stability, transportation access, walkability, educational attainment, unemployment rate, poverty level, median household income percentile, urbanicity, and linguistic isolation" | SDOH | **Major rewrite.** With PUF only, SDOH layer is: education (categorical), household income (categorical), insurance type. Drop ZCTA, food desert, ADI, walkability, linguistic isolation, unemployment, urbanicity. Note in Limitations that ZIP-level SDOH integration was deferred to LAF tier. |

---

## Methods → Outcome Definition (lines 199-211)

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 201-210 | "The simulated primary prediction outcome was first documented progression... Outcome labels were assigned probabilistically based on published Stage 2-3 to Stage 4-5 progression rates from USRDS 2023, stratified by age, diabetes status, hypertension, ADI quintile, and baseline eGFR" | METHODS (CRITICAL — this is the tautology) | **Replace entirely.** New text: "Progression to Stage 4-5 was defined per KDIGO 2024 as two consecutive eGFR readings <30 mL/min/1.73m² separated by ≥90 days, observed in CRIC longitudinal labs within 24 months of the index baseline visit." The key change: outcome is now **observed in real follow-up**, not assigned by formula. |
| 210 | "simulated event rate was 22.1%" | METHODS | Replace with observed CRIC event rate (will likely be lower since CRIC eGFR floor is 20, so many participants are already close to Stage 4) |

---

## Methods → Feature Engineering (lines 213-222)

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 217-218 | "Patients with fewer than two eGFR measurements in this window (**8.3% of training cohort**) were excluded" | FACT-FIX | This was false against the synthetic code (no exclusion ever happened). With CRIC, this becomes a **real** exclusion criterion — keep the wording but the percentage will be CRIC-specific. |

---

## Methods → Model Development (lines 224-236)

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 229-231 | "XGBoost was compared against logistic regression (AUROC 0.84), random forest (AUROC 0.87), and LightGBM (AUROC 0.88) on the internal validation set; XGBoost achieved the highest AUROC (0.89)" | AUROC | All four numbers regenerate from CRIC. |
| 233-234 | "Final hyperparameters (max_depth=8, learning_rate=0.05, n_estimators=500, subsample=0.8) were selected via Bayesian optimization across 200 iterations" | METHODS | Re-run hyperparameter search on CRIC. Keep methodology, update final values. |

---

## Methods → Validation Strategy (lines 238-247)

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 240-242 | "five-fold cross-validation stratified by simulated time period and geographic stratum" | METHODS | Update stratification: time period (CRIC enrollment year) + recruitment site (the 7 academic centers) |

---

## Methods → Pilot Deployment & Cost-Effectiveness (lines 249-275)

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 249-262 | Entire "Simulated Deployment and Intervention Framework" section | PILOT | **Decision needed:** (a) reframe as a hypothetical cost-effectiveness illustration, NOT pilot deployment, with explicit statement that no real intervention was simulated, (b) drop entirely. I'd recommend (a) condensed to one paragraph in Discussion under "Implications for Deployment". |
| 264-275 | Entire "Projected Cost-Effectiveness Analysis" section | COST | Same decision — keep as illustrative if pilot stays, drop if pilot drops. |
| 268-272 | "Medicare reimbursement rates were derived from USRDS 2023: $89,000 per patient-year for Stage 5 CKD... $11,385,000... $3,036,000... BCR of 3.75:1" | COST | These are illustrative either way; only the input numbers (Medicare rates) need keeping if we keep the section. The "165 patients" figure is downstream of the synthetic pilot N — recompute. |

---

## Results — All numerical content needs regeneration

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 292-303 | Entire "Predictive Performance" paragraph with AUROC 0.91/0.89/0.87, Sensitivity 0.79, Specificity 0.84, PPV 0.68, AUPRC 0.72 | AUROC | Regenerate every number from CRIC |
| 305-318 | Table 2 (full performance metrics table) | AUROC | Regenerate entire table |
| 326-336 | Figure 2 caption | AUROC | Regenerate figure + caption |
| 340-352 | Entire "Feature Importance Analysis" paragraph (eGFR slope 18.4%, eGFR 15.2%, UACR 12.8%, ADI 9.1%, food desert 7.3%, healthcare shortage 6.6%, HbA1c 5.2%, BMI 3.1%, diabetes 4.7%, BP 4.4%, clinical 62%, SDOH 23%, utilization 15%) | SHAP | Regenerate every number. SDOH percentage will fall significantly with PUF-only SDOH. |
| 354-363 | Figure 3 caption | SHAP | Regenerate figure + caption |
| 367-374 | Entire "Equity Analysis" paragraph (AA 0.88, Hispanic 0.86, White 0.87, P=.43; Rural 0.86 vs Urban 0.88, P=.18) | AUROC | Regenerate. **Drop the rural/urban comparison entirely** — CRIC is not rural. Keep race/ethnicity comparison. |
| 376-390 | Table 3 (subgroup performance) | AUROC + FRAMING | Regenerate. Drop Rural/Urban rows. Possibly add education or income tertile rows. |
| 392-402 | Figure 4 caption | AUROC + FRAMING | Regenerate without rural/urban |
| 404-418 | Entire "Projected Pilot Deployment Outcomes" section | PILOT | Decision-dependent (see Methods → Pilot row above) |
| 420-435 | Table 4 (pilot outcomes) | PILOT | Decision-dependent |
| 438-451 | Figure 5 caption | PILOT | Decision-dependent |
| 453-462 | "Projected Cost-Effectiveness" paragraph | COST | Decision-dependent |

---

## Discussion

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 466-482 | "Principal Findings" paragraph | AUROC + PILOT + FRAMING | Rewrite. Drop "underserved rural communities". Update AUROC values. Soften pilot claims to illustrative-only. |
| 470-471 | "underserved rural communities" | FRAMING | Replace |
| 472 | "AUROC 0.87 vs 0.80 on synthetic external validation" | AUROC | Update |
| 474 | "31.9% relative reduction" | PILOT | Decision-dependent |
| 479 | "BCR of 3.75:1" | COST | Decision-dependent |
| 488 | "AUROC 0.87" | AUROC | Update |
| 498-509 | "Equity Considerations" paragraph | FRAMING + SDOH | Major rewrite. The ecological-bias paragraph (line 504-509) becomes more honest: PUF SDOH is individual-level, not ZCTA. If we escalate to LAF, the ecological discussion is reintroduced honestly. |
| 501 | "rural/urban geography (P=.18)" | FRAMING | Drop |
| 511-534 | Entire "Limitations" section | METHODS | **Major rewrite.** Replace synthetic-data limitation with CRIC limitations: academic-center recruitment (generalizability to community settings), already-CKD-selected (no Stage 1 patients), older enrollment era (2003-2008), limited individual-level SDOH variables. |
| 538-545 | "Future Work" section | FRAMING | Update: prospective real-world validation in **rural** systems remains future work; LAF tier with ZIP-level SDOH linkage is a near-term extension. |
| 549-557 | "Conclusions" | AUROC + PILOT + FRAMING | Rewrite to match new findings |
| 552 | "underserved rural communities" | FRAMING | Replace |
| 554 | "BCR of 3.75:1" | COST | Decision-dependent |

---

## Acknowledgments / Data Availability / Abbreviations

| Line | Current text | Category | Action |
|------|--------------|----------|--------|
| 561-565 | "Acknowledgments" thanking USRDS, CDC PLACES, ADI sources | METHODS | Replace with NIDDK CRIC + CRIC investigators acknowledgment (CRIC has a standard acknowledgment text required by DUA) |
| 571-579 | "Data Availability" statement claiming no real data | METHODS | **Critical change.** Update to: "This analysis used the CRIC Public-Use File available from the NIDDK Central Repository [URL]. Analysis code is available at [Repository URL]." |
| 647 | ZCTA in abbreviations list | SDOH | Drop if PUF-only |

---

## Summary of decisions still needed

1. **Pilot deployment + cost-effectiveness** — keep as illustrative one-paragraph mention in Discussion, or drop entirely? My recommendation: keep as a brief illustrative mention with very explicit "this is a hypothetical, not a result" framing. Reviewers tend to like seeing the cost framing as motivation, but won't accept it as a finding.
2. **CRIC standard acknowledgment text** — the DUA will specify this. Will copy in once you share the DUA materials.
3. **Recruitment-site exposure** — PUF de-identifies site. We can't do site-stratified CV unless we escalate to LAF. With PUF, stratify by enrollment-year tertile + race instead.

---

## Headcount of changes

- **FRAMING**: 14 line-locations
- **N**: 6 line-locations
- **AUROC**: ~25 numerical values across Abstract, Methods, Results, Discussion
- **SHAP**: 10 numerical values
- **PILOT**: 1 entire section + 4 references in Discussion/Conclusions
- **COST**: 1 entire section + 2 references
- **SDOH**: 1 paragraph rewrite + 4 cross-references
- **METHODS**: 4 paragraph rewrites (Study Design, Cohort Generation, Outcome Definition, Limitations)
- **FACT-FIX**: 1 (the 8.3% claim)

Total estimated edit: ~40% of the manuscript text. Tables 2/3 and Figures 2/3/4 fully regenerate; Table 4 + Figure 5 decision-dependent.
