# ShikshaSetu Foundation — Technical Case-Study Report
**Veltris Vertical AI Academy | Challenge A: AI for Social Impact – Improving Education Access**

---

## 1. Executive Summary
ShikshaSetu Foundation supports **900 students across 10 schools** (`61%–82%` baseline attendance; weighted average **`71.03%`**). Manual risk identification, unstandardized intervention outcomes, and strict outreach capacity (**5 workers × 4 visits/day × 5 days = 100 visits/week**, **`INR 25,000` weekly budget at `INR 250/visit`**) make weekly prioritization difficult.

**ShikshaSetu Foundation (Student Success & Intervention Intelligence Platform)** is an end-to-end full-stack web system that combines:
- Deterministic capacity/budget validation (`4 visits/worker/day`, `100/wk`, `INR 25,000`).
- Transparent, teacher-overridable student review prioritization (no fake ML trained on the 12 synthetic student records).
- Standardized visit outcome tracking & 8 social-impact KPIs over a 90-day pilot framework.
- A PII-safe Google Gemini AI Teacher Assistant grounded strictly in verified backend database statistics.

---

## 2. Task A: Problem Understanding & Prioritization
### Three Most Important Problems
1. **Inconsistent Attendance & School-Level Disparity**: Weighted attendance is `71.03%`, with **School 7 (`61%`)**, **School 10 (`62%`)**, and **School 5 (`65%`)** lagging well behind School 1 (`82%`) and School 6 (`80%`).
2. **Manual, Unconsolidated Student Triage**: Attendance, previous-term academic scores, travel distance, and prior visit counts sit separately without a unified review queue.
3. **Unrecorded Intervention Outcomes & Resource Constraints**: Prior visits are logged for 5 of the 12 sample students (`ST002`, `ST004`, `ST006`, `ST009`, `ST011`), yet outcomes are inconsistently recorded—risking repeat visits without learning what worked within the `100-visit/week` cap.

### First Priority & Why
**Standardizing attendance + outcome tracking and creating an explainable triage queue** is the #1 priority because without reliable weekly data and outcome feedback loops, neither outreach allocation nor future ML models can be trustworthy.

### Additional Information Required & Assumptions
- Weekly longitudinal attendance series (to detect sudden drops vs. chronic absenteeism), school holiday/exam calendars, transport availability, and consented historical outcomes (`retained`, `transferred`, `confirmed dropout`).
- Key assumptions: `71.03%` weighted attendance assumes comparable reporting windows across the 10 schools; `INR 250/visit` is treated as an average planning cost; initial `40/30/20/10` scoring weights are prototype assumptions subject to educator calibration.

---

## 3. Task B: Data Analysis Findings (`analysis/shikshasetu_eda.ipynb`)
- **Dataset A1**: 10 schools, 900 total enrolled students, weighted mean attendance **`71.03%`** (simple mean `71.00%`). Schools `<70%`: School 7 (`61%`), School 10 (`62%`), School 5 (`65%`), School 4 (`68%`).
- **Dataset A2 Initial Investigation Shortlist (5 Priority Students)**:
  1. **ST009** (School 7): `35%` attendance, score `39`, `8 km`, `2 prior visits`
  2. **ST004** (School 3): `41%` attendance, score `45`, `6 km`, `2 prior visits`
  3. **ST012** (School 10): `44%` attendance, score `48`, `6 km`, `0 prior visits`
  4. **ST007** (School 5): `48%` attendance, score `58`, `7 km`, `0 prior visits`
  5. **ST002** (School 1): `54%` attendance, score `62`, `4 km`, `1 prior visit`
  *(ST006 at 59% attendance / score 52 / 5 km and ST011 at 57% remain visible in the Review Soon queue.)*
- **Patterns & Correlation vs. Causation**: In Dataset A2, attendance correlates positively with previous-term score and negatively with distance to school. However, correlation does **not** prove causation—confounders such as family livelihood, illness, seasonal weather, or transit gaps require longitudinal and comparison-group data.

---

## 4. Task C & D: AI Solution & Explainable Prioritization Model
- **Deterministic Rules**: Attendance bounds (`0–100%`), CSV schema checks, `4 visits/worker/day`, `100/wk`, `INR 25,000` budget.
- **Traditional Analytics**: School rankings, weighted averages, missing-data flags, descriptive before/after changes.
- **Explainable Scoring Engine (`backend/app/intelligence/risk_engine.py`)**:
  - Attendance Concern (`0–40 pts`)
  - Academic Indicator (`0–30 pts`)
  - Access / Travel Logistics (`0–20 pts`) — explicitly framed as a travel barrier, never motivation
  - Intervention Follow-up Need (`0–10 pts`) — triggers only when prior visits lack documented outcomes
  - Bands: **High Priority** (`>=60` or attendance `<50%`), **Review Soon** (`>=40` or attendance `<65%`), **Routine Review**.
  - **Fairness & Human Oversight**: Educators can validate, override, or defer any recommendation with an audit-logged reason.
- **Future Supervised ML**: Deferred until consented, representative, outcome-labelled longitudinal records exist (Logistic Regression / tree-based models evaluated via temporal validation, PR-AUC, calibration, and subgroup fairness checks).
- **Generative AI**: Google Gemini (`gemini-3.5-flash`) explains verified backend facts and drafts non-stigmatizing checklists without receiving PII.

---

## 5. Task E: Technical Architecture, Security & Offline Resilience
- **Frontend**: React + TypeScript + Vite + Tailwind CSS + Recharts + Framer Motion (Vercel).
- **Backend**: Python + FastAPI + SQLAlchemy 2.0 + Pandas + FPDF2 (Render).
- **Database**: PostgreSQL (Supabase) in production; SQLite fallback locally.
- **Security**: PBKDF2-SHA256 passwords, HS256 JWT tokens, server-side RBAC (`admin`, `teacher` school-scoped, `outreach` worker-scoped), immutable `audit_events` table, no secrets in frontend code.
- **Limited Connectivity Support**: Online/offline indicator, downloadable CSV visit task lists, and local field-note draft capture with server sync endpoint (`POST /api/interventions/sync-offline-drafts`).

---

## 6. Task F: Social Impact Measurement & 90-Day Plan
Eight tracked KPIs implemented in `backend/app/analytics/kpi_engine.py`:
1. Weighted Average Attendance
2. Prolonged Absenteeism (`<50%`)
3. Intervention Completion Rate
4. Follow-up Completion Rate
5. Cohort Student Retention
6. Outreach Cost per Successful Support Outcome
7. Average Time to First Teacher Review
8. Post-Intervention Attendance Change *(explicitly marked descriptive association, not causation)*

90-Day Plan: **Days 1–30** (Baseline, data quality, threshold calibration) → **Days 31–60** (Teacher-approved outreach & outcome logging) → **Days 61–90** (Comparison-group evaluation & fairness audit).

---

## 7. Task G: Practical Working Artifact
Implemented full-stack application (`shikshasetu-foundation`) + reproducible EDA notebook (`analysis/shikshasetu_eda.ipynb`) + automated test suite (`backend/tests/test_core.py`).
