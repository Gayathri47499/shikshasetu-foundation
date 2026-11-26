# ShikshaSetu Foundation — 8-Slide Presentation Outline

1. **Title & Mission**: ShikshaSetu Foundation — Student Success & Intervention Intelligence Platform (*Every Student Matters. Every Opportunity Counts.*).
2. **Problem & Operational Constraints**: 10 schools, 900 students, manual triage, inconsistent outcome tracking; 5 workers × 4 visits/day × 5 days = 100 visits/wk & INR 25,000 budget.
3. **Data Analysis (Datasets A1–A3)**: Weighted avg attendance `71.03%`; lowest schools: School 7 (`61%`), School 10 (`62%`), School 5 (`65%`); 5-student initial investigation shortlist (`ST009`, `ST004`, `ST012`, `ST007`, `ST002`); synthetic data limitations & correlation vs. causation.
4. **Solution Workflow**: Import & validate CSV → Analyze attendance → Explainable triage → Teacher review/override → Capacity-constrained weekly plan → Approved visits → Outcome tracking.
5. **Explainable Risk & AI Responsibility Matrix**: Deterministic rules + traditional analytics + transparent scoring (40/30/20/10 weights) + PII-stripped Gemini explanations + deferred supervised ML.
6. **Technical Architecture & Security**: React + Vite + Tailwind (Vercel) → FastAPI + SQLAlchemy (Render) → PostgreSQL (Supabase) + Gemini API backend adapter; RBAC & audit logging.
7. **Live Prototype & Impact KPIs**: Screenshots/demo of Dashboard, Explainability Panel, Weekly Planner, Grounded AI Assistant, and 8 Social Impact KPIs.
8. **90-Day Roadmap, Limitations & Conclusion**: Days 1–30 pilot, Days 31–60 rollout, Days 61–90 controlled impact evaluation; safeguarding & governance next steps.
