# ShikshaSetu Foundation

**Student Success & Intervention Intelligence Platform**  
*Every Student Matters. Every Opportunity Counts.*

Built for the **Veltris Vertical AI Academy — Challenge A: AI for Social Impact (Improving Education Access)**.

---

## Overview

ShikshaSetu Foundation turns fragmented school attendance registers, academic indicators, and outreach constraints into **explainable student review priorities**, **capacity- and budget-validated weekly visit plans**, **standardized outcome tracking**, and **PII-safe grounded AI teacher assistance**.

> **Important Assessment Boundary:** The supplied 12 student records (`ST001`–`ST012`) are synthetic illustrative data with no verified dropout outcome labels. This platform uses a transparent, teacher-overridable rule-based prioritization engine and clearly labels all synthetic/illustrative data.

---

## Core Modules Implemented

1. **Landing & Role-Based Authentication**: Email/password JWT login, Forgot Password reset flow, and server-enforced RBAC for **Foundation Administrator**, **Teacher Coordinator** (school-scoped), and **Community Outreach Worker** (visit-scoped).
2. **Foundation Dashboard**: Live backend KPIs (900 enrolled students, 10 schools, 71.03% weighted attendance, capacity & INR 25,000 budget utilization), animated charts, date/school filters, and audit feed.
3. **School Analytics**: All 10 schools from Dataset A1, attendance rankings, schools requiring attention (<70%), and interactive school detail profiles.
4. **Student Profiles**: Searchable, filterable, paginated student directory with CSV export, attendance/academic history, intervention timeline, and teacher observations.
5. **Explainable Student Risk Intelligence**: Transparent weighted triage (`Attendance 40% + Academic 30% + Distance/Access 20% + Pending Outcome Follow-up 10%`), missing-data flags, and educator review/override workflow.
6. **Intelligent Intervention Planner**: Deterministic constraint solver enforcing **5 workers × 4 visits/worker/day × 5 days = 100 max weekly visits** and **INR 25,000 weekly budget (INR 250/visit)**, with mandatory Teacher/Admin approval before scheduling.
7. **Grounded AI Teacher Assistant**: Provider-abstracted Google Gemini integration (`backend/app/ai/assistant_service.py`) where Python computes all statistics from authorized database rows, strips PII, and falls back gracefully if no API key is configured.
8. **Intervention Lifecycle & Outcome Analytics**: Create visits, update status, record standardized outcomes, follow-up dates, and descriptive before/after attendance charts (with non-causation safeguards).
9. **Foundation Impact Reports (Task F)**: All 8 measurable social impact KPIs, 90-day pilot plan, CSV export, and downloadable PDF reports.
10. **CSV Data Upload & Validation**: Two-step preview & confirm workflow catching missing columns, invalid ranges, duplicate IDs, and unknown school/student references without silently discarding rows.
11. **Offline-Friendly Field Support**: Online/offline indicator, downloadable CSV task lists, and local field-note draft capture with one-click sync when connectivity returns.

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts, Lucide Icons, Axios
- **Backend**: Python, FastAPI, SQLAlchemy 2.0, Pydantic, Pandas, NumPy, Scikit-learn, FPDF2, PyJWT
- **Database**: PostgreSQL (Supabase) in production / SQLite zero-config default locally
- **AI**: Google Gemini API (`gemini-3.5-flash`) behind an abstract backend provider

---

## Local Development Setup

### 1. Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and add your Gemini API key (optional — works with grounded deterministic fallback if empty):
```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_random_secret_key
```

Run the backend server (auto-creates database & seeds exact Veltris Challenge A data on startup):
```bash
uvicorn app.main:app --reload --port 8000
```
API Swagger Docs: `http://localhost:8000/docs`

### 2. Frontend Setup (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Open `http://localhost:5173`.

### Demo Credentials
- **Foundation Administrator**: `admin@shikshasetu.org` / `Admin@123`
- **Teacher Coordinator (School 7)**: `teacher.school7@shikshasetu.org` / `Teacher@123`
- **Community Outreach Worker (OW04)**: `outreach.ow04@shikshasetu.org` / `Outreach@123`

---

## Running Tests

```bash
cd backend
pytest -v
```

---

## Deployment Guide (Vercel + Render + Supabase)

1. **Supabase (PostgreSQL)**:
   - Create a Supabase project and copy the Postgres connection string (`postgresql+psycopg://...`).
2. **Render (FastAPI Backend)**:
   - Connect your GitHub repo using `render.yaml` (`rootDir: backend`).
   - Set environment variables: `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`, `CORS_ORIGINS=https://your-app.vercel.app`.
3. **Vercel (React Frontend)**:
   - Import the repo in Vercel with **Root Directory** set to `frontend`.
   - Set environment variable: `VITE_API_BASE_URL=https://your-render-api.onrender.com`.
   - Deploy (`vercel.json` handles SPA routing automatically).

---

## Responsible AI & Known Limitations
- **Small Synthetic Dataset**: Dataset A2 contains 12 illustrative records with no verified dropout labels; supervised ML is intentionally deferred until consented longitudinal outcomes are collected.
- **Correlation vs. Causation**: Before/after attendance changes are descriptive monitoring indicators and do not prove causation.
- **Privacy**: Only Student IDs and aggregated metrics are sent to the Gemini API—never student names or family contacts.
