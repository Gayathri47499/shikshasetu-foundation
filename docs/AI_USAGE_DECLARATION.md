# AI Usage Declaration (One-Page Statement)

**Project:** ShikshaSetu Foundation — Student Success & Intervention Intelligence Platform  
**Assessment:** Veltris Vertical AI Academy — Challenge A (Improving Education Access)

## 1. Disclosure of AI-Assisted Work
- AI coding and drafting assistants were used to accelerate full-stack scaffolding (FastAPI endpoints, React/Tailwind components, SQLAlchemy schema definitions, and documentation formatting).
- Google Gemini (`gemini-2.5-flash`) is integrated into the runtime **Teacher AI Assistant** solely behind a backend Python adapter (`backend/app/ai/assistant_service.py`) to summarize authorized database facts and draft non-stigmatizing support checklists.

## 2. Personal Verification & Ownership
I personally reviewed, verified, and tested:
1. Exact transcription of all Veltris Challenge A datasets (`Dataset A1`, `Dataset A2`, `Dataset A3`) without alteration.
2. All deterministic calculations: weighted attendance (`71.03%` across `900` students), explainable scoring weights, and capacity/budget constraints (`5` workers × `4` visits/day × `5` days = `100` visits/week; `INR 25,000` weekly budget).
3. Ethical & Responsible AI boundaries: no supervised dropout classifier is trained or claimed on the 12 synthetic student records; distance is framed as an access barrier; prior visits prompt outcome review rather than increasing risk; and all automated proposals require human Teacher/Admin approval.
4. Automated `pytest` suite and production frontend build verification.
