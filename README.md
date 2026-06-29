# 🚀 Placement Pilot

> Your AI co-pilot for campus placements — hunting jobs, scoring matches, and drafting personalised recruiter emails autonomously every morning at 8 AM.

Built for the **Gappy AI Hackathon (June 2026)** on the [Lemma](https://lemma.work) platform.

**🔗 Live app:** https://placement-pilot.apps.lemma.work

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
│   ├── user_profiles      — target roles, locations, preferences
│   ├── resumes            — uploaded PDFs + parsed skill JSON
│   ├── job_postings       — jobs found by hunter
│   ├── job_matches        — scored resume ↔ job pairs
│   └── outreach_messages  — drafted & sent emails
│
├── Agents (all built via lemma-sdk)
│   ├── resume_parser      — reads PDF via WORKSPACE_CLI, extracts skills/role/education
│   ├── job_hunter         — web search → writes job_postings rows
│   ├── placement_runner   — orchestrates parse → hunt → score → draft
│   └── outreach_composer  — researches company, drafts 180-word personalised email
│
├── Functions (Python, deterministic)
│   ├── score_match              — 0-100 skill-overlap scorer, no LLM
│   └── kick_off_parsed_resumes  — autonomous trigger for all parsed resumes
│
├── Workflow: placement_cycle
│   kick_off → hunt → approve (human) → send via Gmail
│
├── Schedule: weekdays 8 AM IST (cron: 0 8 * * 1-5)
│
└── Connectors: Gmail (Composio OAuth)
```

---

## ⚡ Reproducible Pod Setup

> **The entire pod — tables, agents, functions, workflow — can be recreated on any fresh Lemma pod in under 2 minutes using 3 commands.**

```bash
python setup_pod.py                                    # tables + agents + functions
python setup_permissions.py                            # all grants + /resumes/ folder  
lemma workflow create --file ./placement_cycle.json    # import workflow graph
```

That's it. No manual clicking in the UI required for setup.

---

## 📦 Full Installation Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ (for Lemma app only)
- [Lemma](https://lemma.work) account with a pod created
- Gmail account for outreach

### Step 1 — Clone & Install Python Dependencies

```bash
git clone https://github.com/rishidakshbansal/placement-pilot
cd placement-pilot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Install & Authenticate Lemma CLI

```bash
pip install uv
uv tool install lemma-terminal
source $HOME/.local/bin/env   # add uv tools to PATH

lemma auth login   # opens browser → sign in with your Lemma account
```

### Step 3 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
LEMMA_POD_ID=your_pod_id_here       # from lemma.work URL: /pod/YOUR-POD-ID/
GMAIL_ACCOUNT_ID=                   # fill after Step 6
# LEMMA_TOKEN=                      # only needed for Streamlit Cloud (not local dev)
```

Get your Pod ID from the URL bar when you're inside your pod on lemma.work.

### Step 4 — Set Up the Pod (3 commands)

```bash
# Creates 5 tables, 4 agents, 2 functions
python setup_pod.py

# Sets all permissions + creates /resumes/ folder in Docs
python setup_permissions.py

# Imports the placement_cycle workflow
lemma workflow create --file ./placement_cycle.json
```

Expected output from `setup_pod.py`:
```
📦 Creating tables...
  ✅ Created table: user_profiles
  ✅ Created table: resumes
  ✅ Created table: job_postings
  ✅ Created table: job_matches
  ✅ Created table: outreach_messages
🤖 Creating agents...
  ✅ Created agent: job_hunter
  ✅ Created agent: resume_parser
  ✅ Created agent: placement_runner
  ✅ Created agent: outreach_composer
⚙️  Creating functions...
  ✅ Created function: score_match
  ✅ Created function: kick_off_parsed_resumes
✅ Pod setup complete!
```

### Step 5 — Connect Gmail

1. lemma.work → your pod → **Connectors** → **+ Add**
2. Search **Gmail** → click Connect
3. Select **Composio → System default → Use default**
4. Authenticate with your Gmail

Get your Gmail account ID:
```bash
lemma connector accounts list --connector gmail
# Copy the Id column value
```

Add to `.env`:
```
GMAIL_ACCOUNT_ID=paste_id_here
```

### Step 6 — Set Up Telegram Notifications (Optional)

Get notified on Telegram when jobs are found and emails are drafted.

1. Open Telegram → message **@BotFather** → send `/newbot`
2. Follow prompts → copy the **API token**
3. Send any message to your new bot
4. Get your Chat ID:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
# Copy the chat.id from the response
```
5. After setting up the app → go to **👤 Profile** → enter Bot Token + Chat ID → save

### Step 8 — Add Morning Schedule

1. lemma.work → your pod → **Schedules** → **New Schedule**
2. Type: **Time** | Cron: `0 8 * * 1-5` | Target: `placement_cycle`
3. Save

Autonomous job hunting now runs every weekday at 8 AM.

### Step 9A — Run Streamlit App (Local)

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

First time → fill profile form → upload resume → run hunt → approve emails.

### Step 9B — Deploy Lemma App (Hosted on lemma.work)

```bash
cd placement-pilot-app
npm install
cp .env.local.example .env.local
# Edit .env.local with your values (see below)
npm run build

# Replace YOUR-NAME with your identifier (e.g. rishi, john, etc.)
lemma apps deploy placement-pilot-YOUR-NAME .
# → App live at https://placement-pilot-YOUR-NAME.apps.lemma.work
```

`.env.local` values needed:
```
VITE_LEMMA_POD_ID=your_pod_id
VITE_ORG_ID=your_org_id          # from: lemma org list
VITE_GMAIL_ACCOUNT_ID=your_gmail_account_id
VITE_LEMMA_API_URL=https://api.lemma.work
VITE_LEMMA_AUTH_URL=https://lemma.work/auth
VITE_LEMMA_APP_BASE_PATH=/
```

Get org ID: `lemma org list`

---

## 🖥️ App Features

| Tab | Description |
|-----|-------------|
| 🏠 Dashboard | Live metrics — jobs found, strong matches, pending approvals, emails sent |
| 🔍 Hunt Jobs | Trigger manual hunt + clear & re-hunt option |
| 📋 My Pipeline | All scored matches, filterable by score and status |
| ✅ Approvals | Review, edit and approve AI-drafted emails — sends via Gmail on approve |
| 📄 My Resume | Upload PDF → auto-parsed at hunt time |
| 👤 Profile | Edit target roles, locations, experience level, channels |

---

## 🤖 Agent Design

### `resume_parser`
Uses `WORKSPACE_CLI` toolset to read the uploaded PDF directly. Extracts structured JSON:
```json
{
  "skills": ["python", "langchain", "rag", "chromadb", "gemini api"],
  "recent_role": "3rd-year B.Tech CSE undergrad | Generative AI portfolio builder",
  "years_experience": 0,
  "education": [{"institution": "IIIT Kottayam", "degree": "B.Tech CSE", "gpa": "8.7/10"}]
}
```

### `job_hunter`
Runs 6–10 targeted web searches combining target roles + locations + top skills. Filters by experience level (intern/fresher only for students). Deduplicates by URL. Writes full JD when scrapeable, marks as `stub` otherwise.

### `score_match` (Function — deterministic, no LLM)
Maps resume skills against `jd_skills`. Handles both flat list `["python","rag"]` and structured `{required:[], nice_to_have:[]}` formats. 70% weight on required skills, 30% on nice-to-have. Title-word overlap fallback when JD has no structured skills.

### `outreach_composer`
2 web searches per company → extracts specific facts → writes 180-word email with company hook, quantified proof point, skill mapping, CTA. Portal jobs (Internshala/Unstop/Cutshort) → portal apply row instead.

### `placement_runner`
Orchestrator. **Agents communicate via the shared database between steps** — not in-memory state. Makes the pipeline restartable at any step. Reads `job_postings` table directly after hunting (doesn't rely on hunter's output) to get job IDs for scoring.

---

## 📊 Results (Live Demo)

On a fresh pod with Rishi Bansal's GenAI resume:

- **22 real jobs found** in one run — Airbus, Coupang, CAW Studios, Atlan, Kimberly-Clark, CRISIL, Techolution, RentoMojo, Zuddl, Cerebrone.ai and more
- **3 personalised emails drafted** — each with real company research, real skill mapping, real numbers
- **Emails sent via Gmail** — directly from app on one-click approval
- **Resume parsed accurately** — 38 skills extracted, correct education, zero hallucination

Sample drafted email subject lines:
- `Generative AI Intern @ Airbus — Bengaluru Tech Hub`
- `SWE Intern @ Coupang — Hyderabad Gen AI Hub fit`
- `AI Automation Engineer Intern @ RentoMojo — back-office automation`

---

## 🗂️ Repository Structure

```
placement-pilot/
├── setup_pod.py              # Reproducible pod setup — tables, agents, functions
├── setup_permissions.py      # Agent/function grants + /resumes/ folder
├── placement_cycle.json      # Workflow bundle for lemma workflow create
├── app.py                    # Streamlit app (local dev)
├── requirements.txt
├── .env.example              # Environment template
├── .gitignore
├── .streamlit/
│   └── config.toml           # Dark theme
└── placement-pilot-app/      # Lemma-hosted React app
    ├── src/
    │   ├── main.tsx           # Full React UI
    │   └── styles.css
    ├── .env.local.example     # Environment template for React app
    ├── lemma.app.json
    └── package.json
```

---

## 🔐 Architecture Notes

- **One pod per user** — each deployment is a fully isolated workspace
- **RLS on all tables** — data is scoped to the authenticated Lemma user
- **Agents communicate via tables** — not in-memory, making the system resilient and restartable
- **Deterministic scoring** — `score_match` uses no LLM, just Python set operations

---

## 🗺️ Roadmap

- **V2** — Telegram/WhatsApp notifications for portal jobs
- **V2** — LinkedIn DM outreach via connector
- **V3** — Multi-pod provisioning (auto-create pod on sign-up)
- **V3** — Resume version management
- **V3** — Interview prep agent (triggered when recruiter replies)

---

## 👨‍💻 Built By

**Rishi Bansal** — 3rd year B.Tech CSE, IIIT Kottayam (CGPA 8.7)  
Specialising in Generative AI, RAG pipelines, and AI Agents

- GitHub: [rishidakshbansal](https://github.com/rishidakshbansal)
- LinkedIn: [rishi-bansal1901](https://linkedin.com/in/rishi-bansal1901)
- Hackathon: Gappy AI Hackathon, June 2026
