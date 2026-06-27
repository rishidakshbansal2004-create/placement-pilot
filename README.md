# 🚀 Placement Pilot

> Your AI co-pilot for campus placements — hunting jobs, scoring matches, and drafting personalised recruiter emails autonomously every morning at 8 AM.

Built for the **Gappy AI Hackathon (June 2026)** on the [Lemma](https://lemma.work) platform.

---

## 🎯 What It Does

Placement Pilot is an autonomous AI agent system that:

1. **Hunts jobs every morning at 8 AM** — searches LinkedIn, Wellfound, Internshala, company sites for roles matching your skills and preferences
2. **Scores each match** — deterministic skill-overlap scorer maps your resume skills against JD requirements (0–100 score)
3. **Drafts personalised emails** — researches each company, finds specific facts, writes sharp outreach under 180 words
4. **Waits for your approval** — human-in-the-loop: you review, edit, approve or skip each draft
5. **Sends approved emails** — directly via Gmail connector (Composio OAuth)

---

## 🏗️ Architecture

```
Lemma Pod
├── Tables (RLS ON)
│   ├── users              — login credentials (email + password hash)
│   ├── user_profiles      — target roles, locations, preferences
│   ├── resumes            — uploaded PDFs + parsed skill JSON
│   ├── job_postings       — jobs found by hunter
│   ├── job_matches        — scored resume ↔ job pairs
│   └── outreach_messages  — drafted & sent emails
│
├── Agents
│   ├── resume_parser      — reads PDF, extracts skills/role/education
│   ├── job_hunter         — web search → writes job_postings rows
│   ├── placement_runner   — orchestrates parse → hunt → score → draft
│   └── outreach_composer  — drafts personalised email per match
│
├── Functions
│   ├── score_match              — deterministic skill-overlap scorer
│   └── kick_off_parsed_resumes  — triggers pipeline for all parsed resumes
│
├── Workflow: placement_cycle
│   kick_off → hunt → approve (human) → send via Gmail
│
├── Schedule: weekdays 8 AM IST (cron: 0 8 * * 1-5)
│
└── Connectors: Gmail (Composio OAuth)
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- [Lemma](https://lemma.work) account
- [lemma-terminal](https://pypi.org/project/lemma-terminal/) CLI

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/rishidakshbansal/placement-pilot
cd placement-pilot

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Authenticate CLI
uv tool install lemma-terminal
lemma auth login

# 4. Configure environment
cp .env.example .env
# Edit .env → add your LEMMA_POD_ID

# 5. Set up the pod (creates all tables, agents, functions)
python setup_pod.py

# 6. Set up permissions
python setup_permissions.py

# 7. Import the workflow
lemma workflow create --file ./placement_cycle.json

# 8. Connect Gmail
# lemma.work → your pod → Connectors → Gmail → Connect (Composio OAuth)
# Then get your account ID:
# lemma connector accounts list --connector gmail
# Add to .env: GMAIL_ACCOUNT_ID=your_account_id

# 9. Add schedule (optional — enables autonomous 8 AM hunt)
# lemma.work → Schedules → New → Cron: 0 8 * * 1-5 → placement_cycle

# 10. Launch the app
streamlit run app.py
```

### Deploy on Streamlit Cloud

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo → `app.py`
3. Add secrets:
```toml
LEMMA_TOKEN = "your_lemma_token"
LEMMA_POD_ID = "your_pod_id"
GMAIL_ACCOUNT_ID = "your_gmail_account_id"
```
4. Deploy

Get your Lemma token: `lemma auth print-token`

---

## 🖥️ App Features

| Tab | Description |
|-----|-------------|
| 🏠 Dashboard | Live metrics — jobs found, strong matches, pending approvals, emails sent |
| 🔍 Hunt Jobs | Trigger manual hunt with custom parameters + clear & re-hunt |
| 📋 My Pipeline | All scored matches, filterable by score and status |
| ✅ Approvals | Review, edit and approve AI-drafted emails — sends via Gmail on approve |
| 📄 My Resume | Upload PDF → auto-parsed → ready for hunting |
| 👤 Profile | Edit target roles, locations, experience level, channels |

---

## 🤖 Agent Design

### `resume_parser`
Reads the uploaded PDF using Workspace CLI tools, extracts structured JSON:
```json
{
  "skills": ["python", "langchain", "rag", "chromadb"],
  "recent_role": "3rd-year B.Tech CSE undergrad | Generative AI portfolio builder",
  "years_experience": 0,
  "education": [{"institution": "IIIT Kottayam", "degree": "B.Tech CSE"}]
}
```

### `job_hunter`
Runs 6–10 targeted web searches combining target roles + locations + top skills. Deduplicates by URL. Writes structured rows to `job_postings` with full JD when available.

### `score_match` (Function)
Deterministic Python function — no LLM involved. Maps resume skills against `jd_skills` (flat list or `{required, nice_to_have}` dict). 70% weight on required skills, 30% on nice-to-have. Falls back to title-word overlap when JD has no structured skills.

### `outreach_composer`
Researches each company (2 web searches), extracts 1–2 specific facts, writes a 180-word email with:
- Company-specific hook (not generic)
- Quantified proof point from resume
- 2–3 skill matches mapped to JD language
- Call to action

Portal jobs (Internshala, Unstop, Cutshort) → writes portal apply row, no email drafted.

### `placement_runner`
Orchestrator. Reads from tables between every step — agents communicate via the shared database, not in-memory state. Makes the system restartable at any step.

---

## 📊 Results (Live Demo)

On a fresh pod with Rishi Bansal's GenAI resume:

- **22 jobs found** in one run — Airbus, Coupang, CAW Studios, Atlan, Kimberly-Clark, CRISIL, Techolution, RentoMojo and more
- **3 personalised emails drafted** — each with real company research, real skill mapping
- **1 email sent via Gmail** — directly from app on approval
- **Resume parsed accurately** — 38 skills extracted, correct education, no hallucination

Sample drafted email subject lines:
- `Generative AI Intern @ Airbus — Bengaluru Tech Hub`
- `SWE Intern @ Coupang — Hyderabad Gen AI Hub fit`
- `AI Automation Engineer Intern @ RentoMojo — back-office automation`

---

## 🗂️ Repository Structure

```
placement-pilot/
├── setup_pod.py          # Creates all tables, agents, functions on a fresh pod
├── setup_permissions.py  # Sets all agent/function grants + creates /resumes/ folder
├── placement_cycle.json  # Workflow bundle — import with lemma workflow create
├── app.py                # Streamlit app — multi-user login, full pipeline UI
├── requirements.txt
├── .env.example
├── .gitignore
└── .streamlit/
    └── config.toml       # Dark theme config
```

---

## 🔐 Multi-User

Each user registers with name, email, password and placement preferences in one flow. Profiles are isolated by `app_user_id`. For full data isolation, each user can spin up their own pod instance using `setup_pod.py` — ready in under 2 minutes.

---

## 🗺️ Roadmap

- **V2** — Multi-pod architecture (one pod per user, auto-provisioned on registration)
- **V2** — WhatsApp/Telegram notifications for portal jobs
- **V2** — LinkedIn DM outreach via connector
- **V2** — Lemma Surface (hosted web app on lemma.work)
- **V3** — Resume version management (active resume selection)
- **V3** — Company blacklist / whitelist
- **V3** — Interview prep agent (triggered when recruiter replies)

---

## 👨‍💻 Built By

**Rishi Bansal** (RishiBuilds) — 3rd year B.Tech CSE, IIIT Kottayam  
Specialising in Generative AI, RAG pipelines, and AI Agents

- GitHub: [rishidakshbansal](https://github.com/rishidakshbansal)
- Hackathon: Gappy AI Hackathon, June 2026

---

## 🏗️ Architecture

```
Lemma Pod
├── Tables (RLS ON)
│   ├── users              — login credentials (email + password hash)
│   ├── user_profiles      — target roles, locations, preferences
│   ├── resumes            — uploaded PDFs + parsed skill JSON
│   ├── job_postings       — jobs found by hunter
│   ├── job_matches        — scored resume ↔ job pairs
│   └── outreach_messages  — drafted & sent emails
│
├── Agents
│   ├── resume_parser      — reads PDF, extracts skills/role/education
│   ├── job_hunter         — web search → writes job_postings rows
│   ├── placement_runner   — orchestrates parse → hunt → score → draft
│   └── outreach_composer  — drafts personalised email per match
│
├── Functions
│   ├── score_match              — deterministic skill-overlap scorer
│   └── kick_off_parsed_resumes  — triggers pipeline for all parsed resumes
│
├── Workflow: placement_cycle
│   kick_off → hunt → approve (human) → send via Gmail
│
├── Schedule: weekdays 8 AM IST (cron: 0 8 * * 1-5)
│
└── Connectors: Gmail (Composio OAuth)
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- [Lemma](https://lemma.work) account
- [lemma-terminal](https://pypi.org/project/lemma-terminal/) CLI

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/rishidakshbansal/placement-pilot
cd placement-pilot

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Authenticate CLI
uv tool install lemma-terminal
lemma auth login

# 4. Configure environment
cp .env.example .env
# Edit .env → add your LEMMA_POD_ID

# 5. Set up the pod (creates all tables, agents, functions)
python setup_pod.py

# 6. Set up permissions
python setup_permissions.py

# 7. Import the workflow
lemma workflow create --file ./placement_cycle.json

# 8. Connect Gmail
# lemma.work → your pod → Connectors → Gmail → Connect

# 9. Add schedule (optional)
# lemma.work → Schedules → New → Cron: 0 8 * * 1-5 → placement_cycle

# 10. Launch the app
streamlit run app.py
```

---

## 🖥️ App Features

| Tab | Description |
|-----|-------------|
| 🏠 Dashboard | Live metrics — jobs found, strong matches, pending approvals, emails sent |
| 🔍 Hunt Jobs | Trigger manual hunt with custom parameters + clear & re-hunt |
| 📋 My Pipeline | All scored matches, filterable by score and status |
| ✅ Approvals | Review, edit and approve AI-drafted emails |
| 📄 My Resume | Upload PDF → auto-parsed → ready for hunting |
| 👤 Profile | Edit target roles, locations, experience level, channels |

---

## 🤖 Agent Design

### `resume_parser`
Reads the uploaded PDF using Workspace CLI tools, extracts structured JSON:
```json
{
  "skills": ["python", "langchain", "rag", "chromadb"],
  "recent_role": "3rd-year B.Tech CSE undergrad | Generative AI portfolio builder",
  "years_experience": 0,
  "education": [{"institution": "IIIT Kottayam", "degree": "B.Tech CSE"}]
}
```

### `job_hunter`
Runs 6–10 targeted web searches combining target roles + locations + top skills. Deduplicates by URL. Writes structured rows to `job_postings` with full JD when available.

### `score_match` (Function)
Deterministic Python function — no LLM involved. Maps resume skills against `jd_skills` (flat list or `{required, nice_to_have}` dict). 70% weight on required skills, 30% on nice-to-have. Falls back to title-word overlap when JD has no structured skills.

### `outreach_composer`
Researches each company (2 web searches), extracts 1–2 specific facts, writes a 180-word email with:
- Company-specific hook (not generic)
- Quantified proof point from resume
- 2–3 skill matches mapped to JD language
- Call to action

Portal jobs (Internshala, Unstop, Cutshort) → writes portal apply row, no email drafted.

### `placement_runner`
Orchestrator. Reads from tables between every step — agents communicate via the shared database, not in-memory state. Makes the system restartable at any step.

---

## 📊 Results (Live Demo)

On a fresh pod with Rishi Bansal's GenAI resume:

- **22 jobs found** in one run — Airbus, Coupang, CAW Studios, Atlan, Kimberly-Clark, CRISIL, Techolution, RentoMojo and more
- **3 personalised emails drafted** — each with real company research, real skill mapping
- **Resume parsed accurately** — 38 skills extracted, correct education, no hallucination

Sample drafted email subject lines:
- `Generative AI Intern @ Airbus — Bengaluru Tech Hub`
- `SWE Intern @ Coupang — Hyderabad Gen AI Hub fit`
- `AI Automation Engineer Intern @ RentoMojo — back-office automation`

---

## 🗂️ Repository Structure

```
placement-pilot/
├── setup_pod.py          # Creates all tables, agents, functions on a fresh pod
├── setup_permissions.py  # Sets all agent/function grants + creates /resumes/ folder
├── placement_cycle.json  # Workflow bundle — import with lemma workflow create
├── app.py                # Streamlit app — multi-user login, full pipeline UI
├── requirements.txt
├── .env.example
├── .gitignore
└── .streamlit/
    └── config.toml       # Dark theme config
```

---

## 🔐 Multi-User

Each user registers with name, email, password and placement preferences in one flow. Profiles are isolated by `app_user_id`. For full data isolation, each user can spin up their own pod instance using `setup_pod.py` — ready in under 2 minutes.

---

## 🗺️ Roadmap

- **V2** — Multi-pod architecture (one pod per user, auto-provisioned on registration)
- **V2** — WhatsApp/Telegram notifications for portal jobs
- **V2** — LinkedIn DM outreach via connector
- **V2** — Lemma Surface (hosted web app on lemma.work)
- **V3** — Resume version management (active resume selection)
- **V3** — Company blacklist / whitelist
- **V3** — Interview prep agent (triggered when recruiter replies)

---

## 👨‍💻 Built By

**Rishi Bansal** (RishiBuilds) — 3rd year B.Tech CSE, IIIT Kottayam  
Specialising in Generative AI, RAG pipelines, and AI Agents
- Hackathon: Gappy AI Hackathon, June 2026
