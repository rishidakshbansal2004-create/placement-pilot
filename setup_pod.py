"""
Placement Pilot — setup_pod.py
Recreates the entire pod structure from scratch using lemma-sdk.

Usage:
    pip install lemma-sdk python-dotenv
    cp .env.example .env   # fill in LEMMA_POD_ID (token from CLI session)
    lemma auth login        # authenticate CLI
    python setup_pod.py
    lemma workflow create --file ./placement_cycle.json

This script is idempotent — skips resources that already exist, updates agent instructions.
"""

import os
import sys
from dotenv import load_dotenv
from lemma_sdk import Pod, LemmaAPIError
from lemma_sdk.openapi_client.models.create_table_request import CreateTableRequest
from lemma_sdk.openapi_client.models.create_agent_request import CreateAgentRequest
from lemma_sdk.openapi_client.models.agent_toolset import AgentToolset
from lemma_sdk.openapi_client.models.update_agent_request import UpdateAgentRequest
from lemma_sdk.openapi_client.models.create_function_request import CreateFunctionRequest
from lemma_sdk.openapi_client.models.update_function_request import UpdateFunctionRequest
from lemma_sdk.openapi_client.models.datastore_data_type import DatastoreDataType

load_dotenv()


# ── Helpers ────────────────────────────────────────────────────────────────────

def create_table(pod, payload, label):
    try:
        pod.tables.create_from_dict(payload)
        print(f"  ✅ Created table: {label}")
    except LemmaAPIError as e:
        if "already exists" in str(getattr(e, 'message', '')).lower() or getattr(e, 'status_code', 0) == 409:
            print(f"  ⏭  Table already exists: {label}")
        else:
            print(f"  ❌ Failed table {label}: {getattr(e, 'message', str(e))}")
            raise


def make_schema(fields):
    """Build input/output schema dict from list of (name, type, description, required) tuples."""
    properties = {}
    required = []
    for field in fields:
        fname, ftype, fdesc = field[0], field[1], field[2]
        freq = field[3] if len(field) > 3 else False
        properties[fname] = {"type": ftype, "description": fdesc}
        if freq:
            required.append(fname)
    schema_dict = {"type": "object", "properties": properties}
    if required:
        schema_dict["required"] = required
    return schema_dict


def create_agent(pod, name, instruction, description="", toolsets=None, input_schema=None, output_schema=None):
    try:
        pod.agents.create(CreateAgentRequest(
            name=name,
            instruction=instruction,
            description=description,
            toolsets=toolsets or [],
            input_schema=input_schema,
            output_schema=output_schema,
        ))
        print(f"  ✅ Created agent: {name}")
    except LemmaAPIError as e:
        if "already exists" in str(getattr(e, 'message', '')).lower() or getattr(e, 'status_code', 0) == 409:
            print(f"  ⏭  Agent already exists: {name}")
        else:
            print(f"  ❌ Failed agent {name}: {getattr(e, 'message', str(e))}")
            raise


def update_agent_instruction(pod, name, instruction, toolsets=None, input_schema=None, output_schema=None):
    try:
        pod.agents.update(name, UpdateAgentRequest(
            instruction=instruction,
            toolsets=toolsets or [],
            input_schema=input_schema,
            output_schema=output_schema,
        ))
        print(f"  ✅ Updated agent: {name}")
    except LemmaAPIError as e:
        print(f"  ❌ Failed to update {name}: {getattr(e, 'message', str(e))}")


def create_function(pod, name, code, description=""):
    try:
        pod.functions.create(CreateFunctionRequest(
            name=name,
            code=code,
            description=description,
        ))
        print(f"  ✅ Created function: {name}")
    except LemmaAPIError as e:
        if "already exists" in str(getattr(e, 'message', '')).lower() or getattr(e, 'status_code', 0) == 409:
            print(f"  ⏭  Function already exists: {name}")
        else:
            print(f"  ❌ Failed function {name}: {getattr(e, 'message', str(e))}")
            raise


def update_function(pod, name, code, description=""):
    try:
        pod.functions.update(name, UpdateFunctionRequest(code=code, description=description))
        print(f"  ✅ Updated function: {name}")
    except LemmaAPIError as e:
        print(f"  ❌ Failed to update function {name}: {getattr(e, 'message', str(e))}")


# ── Table definitions ──────────────────────────────────────────────────────────

def setup_tables(pod):
    print("\n📦 Creating tables...")

    create_table(pod, {
        "name": "users",
        "enable_rls": False,
        "columns": [
            {"name": "name",          "type": "TEXT", "required": True},
            {"name": "email",         "type": "TEXT", "required": True,
             "description": "Unique email address for login"},
            {"name": "password_hash", "type": "TEXT", "required": True,
             "description": "SHA-256 hash of password"},
        ],
    }, "users")

    create_table(pod, {
        "name": "user_profiles",
        "enable_rls": True,
        "columns": [
            {"name": "app_user_id",      "type": "TEXT",    "required": False,
             "description": "Links to users.id for app-level multi-user support"},
            {"name": "name",             "type": "TEXT",    "required": True},
            {"name": "target_roles",     "type": "JSON",    "required": True,
             "description": '["ML Engineer Intern", "GenAI Engineer"]'},
            {"name": "locations",        "type": "JSON",    "required": True,
             "description": '["Remote", "Bangalore"]'},
            {"name": "experience_level", "type": "ENUM",    "required": True,
             "options": ["intern", "fresher", "junior", "mid", "senior"]},
            {"name": "company_prefs",    "type": "JSON",    "required": False,
             "description": '["startups", "product companies"]'},
            {"name": "channels",         "type": "JSON",    "required": False,
             "description": '["email", "linkedin"]'},
            {"name": "is_active",        "type": "BOOLEAN", "required": False,
             "default": True},
        ],
    }, "user_profiles")

    create_table(pod, {
        "name": "resumes",
        "enable_rls": True,
        "columns": [
            {"name": "label",            "type": "TEXT",      "required": True},
            {"name": "file_path",        "type": "FILE_PATH", "required": True},
            {"name": "status",           "type": "ENUM",      "required": True,
             "options": ["raw", "parsing", "parsed", "stale", "error"]},
            {"name": "parsed",           "type": "JSON",      "required": False},
            {"name": "raw_text_preview", "type": "TEXT",      "required": False},
            {"name": "error",            "type": "TEXT",      "required": False},
        ],
    }, "resumes")

    create_table(pod, {
        "name": "job_postings",
        "enable_rls": True,
        "columns": [
            {"name": "title",        "type": "TEXT", "required": True},
            {"name": "company",      "type": "TEXT", "required": True},
            {"name": "location",     "type": "TEXT", "required": False},
            {"name": "source",       "type": "ENUM", "required": True,
             "options": ["linkedin", "indeed", "glassdoor", "wellfound", "company_site", "other"]},
            {"name": "source_url",   "type": "TEXT", "required": True},
            {"name": "description",  "type": "TEXT", "required": False},
            {"name": "jd_skills",    "type": "JSON", "required": False},
            {"name": "salary_text",  "type": "TEXT", "required": False},
            {"name": "posted_at",    "type": "DATE", "required": False},
            {"name": "completeness", "type": "ENUM", "required": False,
             "options": ["stub", "full"]},
        ],
    }, "job_postings")

    create_table(pod, {
        "name": "job_matches",
        "enable_rls": True,
        "columns": [
            {"name": "job_id",          "type": "UUID",    "required": True},
            {"name": "resume_id",       "type": "UUID",    "required": True},
            {"name": "score",           "type": "FLOAT",   "required": True},
            {"name": "matched_skills",  "type": "JSON",    "required": False},
            {"name": "missing_skills",  "type": "JSON",    "required": False},
            {"name": "reasoning",       "type": "TEXT",    "required": False},
            {"name": "rank",            "type": "INTEGER", "required": False},
            {"name": "status",          "type": "ENUM",    "required": True,
             "options": ["new", "picked", "skipped", "dismissed", "applied"]},
        ],
    }, "job_matches")

    create_table(pod, {
        "name": "outreach_messages",
        "enable_rls": True,
        "columns": [
            {"name": "match_id",     "type": "UUID", "required": False},
            {"name": "job_id",       "type": "UUID", "required": False},
            {"name": "channel",      "type": "ENUM", "required": True,
             "options": ["email", "linkedin", "portal", "whatsapp", "telegram"]},
            {"name": "recipient",    "type": "TEXT", "required": True},
            {"name": "subject",      "type": "TEXT", "required": False},
            {"name": "body",         "type": "TEXT", "required": True},
            {"name": "status",       "type": "ENUM", "required": True,
             "options": ["drafted", "waiting_approval", "approved", "sent", "replied", "failed", "skipped"]},
            {"name": "error",        "type": "TEXT", "required": False},
            {"name": "external_ref", "type": "TEXT", "required": False},
            {"name": "approved_at",  "type": "DATETIME", "required": False},
            {"name": "sent_at",      "type": "DATETIME", "required": False},
        ],
    }, "outreach_messages")


# ── Agent instructions ─────────────────────────────────────────────────────────

JOB_HUNTER_INSTRUCTION = """
CRITICAL PRE-CHECKS (read before anything else)

1. EXPERIENCE LEVEL FILTER
After reading user_profiles, set experience_level filter:
- If experience_level = 'intern' or 'fresher' → ONLY collect roles with words: intern, internship, fresher, trainee, junior, entry-level
- STRICTLY SKIP any role with: Senior, Sr., Lead, Manager, Director, VP, Head, Principal, Staff
- If a URL looks like a job but title contains those senior words → skip it entirely

2. URL QUALITY FILTER — skip these URL patterns entirely:
- internshala.com/jobs/{anything}-jobs/
- internshala.com/internships/internship-in-{anything}/
- naukri.com/jobs-listings/ or naukri.com/{keyword}-jobs
- glassdoor.com/Jobs/ (category pages)
- indeed.com/jobs?q= (search results pages)
- Any URL that is clearly a search results page, not an individual job posting
ONLY store URLs pointing to a SPECIFIC job at a SPECIFIC company.

You turn a user's profile + parsed resume into a fresh batch of job_postings rows. You DO NOT talk to recruiters.

INPUTS
- resume_id: the row in resumes with a parsed profile
- keyword_overrides: optional extra search phrases
- location_hint: optional location override
- max_results: cap on new rows written (default 25)

STEP 1 — Read user context
Read the resumes row for resume_id. Get the parsed JSON (skills, recent_role, years_experience).
Then read user_profiles where user_id matches the resume's user_id. Get:
- target_roles, locations, experience_level, company_prefs
If user_profiles row does not exist, use resume.parsed.recent_role as target role and "Remote OR India" as location.

STEP 2 — Build search queries
Build 6-10 search queries combining target_roles + locations + skills:
- "{target_role} {experience_level} {location} 2026"
- "{target_role} hiring {location} site:linkedin.com"
- "{target_role} {top_skill} internship India 2026"
- site:internshala.com/internships/detail "{target_role}"
- site:cutshort.io "{target_role}"
- site:unstop.com "{target_role}"
- site:wellfound.com "{target_role} India"

STEP 3 — Run searches
Run each query via web search. Save promising hits. Target 15-20 candidates before deduplication.

STEP 4 — Deduplicate
Check if source_url already exists in job_postings (case-insensitive). Skip duplicates.

STEP 5 — Write job_postings rows
For each new posting decide source from URL:
linkedin.com → linkedin, indeed.com → indeed, glassdoor.com → glassdoor,
wellfound.com → wellfound, internshala.com → other, cutshort.io → other,
unstop.com → other, company domain → company_site, else → other
Best-effort scrape for full JD. If not possible, mark completeness='stub'.

STEP 6 — Return: resume_id, fetched, new_jobs, duplicates, top_results

BOUNDARIES
- DO NOT touch job_matches or outreach_messages
- DO NOT synthesize URLs you have not seen in a search result
- If resume status is 'raw', return error
- Always prefer Indian job boards and remote-friendly postings
""".strip()

RESUME_PARSER_INSTRUCTION = """
You parse a resume PDF. You will receive a resume_id as input.

CRITICAL: You MUST use actual tool calls to read data. NEVER generate, invent, or assume any resume content.

STEP 1 — Read the resume row
Use records.get to fetch the resumes row for resume_id.
Get file_path and current status from the result.
Update status to 'parsing'.

STEP 2 — Read the actual file
Use workspace file tools to read the file at file_path.
If the file cannot be read, set status='error' with error message and STOP.
DO NOT proceed if you cannot read the file.
DO NOT invent any content — not the name, not the university, not the skills.

STEP 3 — Extract from the actual text you read
Only use information from the file text you actually received in Step 2.
Extract:
- skills: list of all technical skills mentioned (lowercase)
- recent_role:
  * If real work experience → "<title> at <company>"
  * If only student/club roles → "<N>-year <degree> undergrad | <domain> portfolio builder"
- years_experience: float
- education: list of education entries
- raw_text_preview: first 2000 chars of the file text

STEP 4 — Save to table
Update the resumes row with:
- parsed = the extracted JSON
- raw_text_preview = first 2000 chars
- status = 'parsed'

STEP 5 — Return parsed JSON summary

BOUNDARIES
- NEVER write fake data
- NEVER assume university, employer, or skills
- If file unreadable → status='error', stop immediately
- recent_role must not contain candidate name
""".strip()

PLACEMENT_RUNNER_INSTRUCTION = """
You run the placement cycle: ensure the resume is parsed, hunt jobs, score them, and turn the top matches into drafts. You are the coordinator of three specialists and one deterministic helper. You never send any message yourself.

Sub-tools you can call:
- function_score_match(resume_id, job_id) -> dict with score, status, matched/missing
- agent_resume_parser(resume_id) -> string summary
- agent_job_hunter(resume_id, keyword_overrides?, location_hint?) -> string summary
- agent_outreach_composer(match_id, channels?, recipient_suggestion?) -> string summary

IMPORTANT: Use the DATABASE as shared memory between steps. Do not try to pass data between agents in memory.

LOOP

1. Parse resume if needed.
   Read the resumes row. If status in ('raw','stale','error'), call agent_resume_parser.
   If status='parsed', skip. If parsing fails, record error and stop.

2. Hunt jobs.
   Note the current timestamp as run_start.
   Call agent_job_hunter with resume_id and max_results = input.max_hunt or 25.
   The hunter writes rows to job_postings table automatically.

3. Score each fresh job.
   Read job_postings table rows where created_at >= run_start (new rows from this hunt).
   For each row, get its id and call function_score_match(resume_id, job_id).
   DO NOT rely on the hunter's output for job IDs — always read from the table directly.

4. Compose drafts for top matches.
   Read job_matches table to get scored matches for this resume_id.
   Sort by score desc, take top max_drafts (default 3) where score >= min_score (default 45).
   For each match, call agent_outreach_composer(match_id, channels=['email']).

5. Return output_schema:
   parsed_ok, new_jobs, scored, matches_above_threshold, drafted_outreach_ids[], errors[]

BOUNDARIES
- NEVER call send_outreach
- NEVER write to the resume's underlying file
- If anything fails, record error string and keep going unless resume parse fails
- Always read from tables, never rely on in-memory data passed between agent calls
""".strip()

OUTREACH_COMPOSER_INSTRUCTION = """
You turn a single job_match into channel-appropriate drafts in outreach_messages. You NEVER send — you write drafts at status='drafted'.

INPUTS
- match_id: the job_matches row
- channels: list of channels to draft for
- recipient_suggestion: optional explicit recipient

STEP 1 — Read context
Read job_matches row → get job_id, resume_id, score, matched_skills, missing_skills.
Read job_postings row → get title, company, description, jd_skills, source_url, source.
Read resumes row → get parsed JSON.
Read user_profiles where user_id matches → get name, experience_level.

STEP 2 — Decide outreach strategy based on source
If source is internshala, unstop, cutshort, indeed, glassdoor:
  → PORTAL APPLY strategy
  → Write ONE outreach_messages row: channel='portal', recipient=source_url, body='Apply directly: '+source_url, status='drafted'
  → Return immediately

If source is linkedin → draft LinkedIn DM
If source is company_site or wellfound → draft email

STEP 3 — Research company (skip if portal strategy)
Search: "{company} product engineering culture India 2026"
Search: "{company} recent launch OR funding 2026"
Extract 1-2 specific facts. Never invent facts.

STEP 4 — Compose email (under 180 words)
Subject: {role} @ {company} — {one specific tie-in, max 8 words}
Para 1: One specific company tie-in from research.
Para 2: One quantified proof point from resume (real numbers only).
Para 3: 2-3 matched_skills mapped to JD language.
Para 4: Ask for 15-min chat.

Tone: Sharp, warm, confident. Not a template.

STEP 5 — Write outreach_messages row
channel, recipient, subject (email only), body, status='drafted'
Skip if matching row already exists with status in (drafted, waiting_approval, approved, sent).

STEP 6 — Return outreach_ids, strategy used, recipient_guessed

BOUNDARIES
- DO NOT mark drafts as approved, sent, or replied
- DO NOT send anything via connectors
- DO NOT write more than one draft per channel per match
- NEVER draft email for internshala, unstop, cutshort, indeed, glassdoor sources
""".strip()


# ── Agent schemas ──────────────────────────────────────────────────────────────

RESUME_PARSER_INPUT = [
    ("resume_id", "string", "The UUID of the resumes row to parse", True),
]
RESUME_PARSER_OUTPUT = [
    ("resume_id",        "string", "The UUID of the parsed resume"),
    ("status",           "string", "Parsing status: parsed or error"),
    ("skills",           "array",  "List of technical skills extracted"),
    ("recent_role",      "string", "Most recent role or student descriptor"),
    ("years_experience", "number", "Years of experience"),
    ("education",        "array",  "Education entries"),
    ("raw_text_preview", "string", "First 2000 chars of resume text"),
]

PLACEMENT_RUNNER_INPUT = [
    ("resume_id",  "string",  "UUID of the resumes row to run pipeline for", True),
    ("max_hunt",   "integer", "Max job postings to find (default 25)"),
    ("max_drafts", "integer", "Max outreach drafts to create (default 3)"),
    ("min_score",  "integer", "Minimum match score to draft (default 45)"),
    ("channels",   "array",   "Outreach channels e.g. ['email']"),
]
PLACEMENT_RUNNER_OUTPUT = [
    ("parsed_ok",                  "boolean", "Whether resume was parsed successfully"),
    ("new_jobs",                   "integer", "Number of new job postings found"),
    ("scored",                     "integer", "Number of jobs scored"),
    ("matches_above_threshold",    "integer", "Number of matches above min_score"),
    ("drafted_outreach_ids",       "array",   "UUIDs of drafted outreach_messages rows"),
    ("errors",                     "array",   "Any errors encountered"),
]

JOB_HUNTER_INPUT = [
    ("resume_id",         "string", "UUID of the resumes row to hunt for", True),
    ("keyword_overrides", "array",  "Optional extra search keywords"),
    ("location_hint",     "string", "Optional location override"),
    ("max_results",       "integer","Max job postings to write (default 25)"),
]
JOB_HUNTER_OUTPUT = [
    ("resume_id",   "string",  "UUID of the resume used"),
    ("fetched",     "integer", "Total candidates found in search"),
    ("new_jobs",    "integer", "New rows written to job_postings"),
    ("duplicates",  "integer", "Skipped duplicate URLs"),
    ("top_results", "array",   "Top job titles found"),
]

OUTREACH_COMPOSER_INPUT = [
    ("match_id",             "string", "UUID of the job_matches row", True),
    ("channels",             "array",  "Channels to draft for e.g. ['email']"),
    ("recipient_suggestion", "string", "Optional explicit recipient email"),
]
OUTREACH_COMPOSER_OUTPUT = [
    ("outreach_ids",    "array",  "UUIDs of created outreach_messages rows"),
    ("strategy",        "string", "Strategy used: email, linkedin, or portal"),
    ("recipient_guessed","boolean","Whether recipient was guessed or known"),
]


def setup_agents(pod):
    print("\n🤖 Creating agents...")
    create_agent(pod, "job_hunter", JOB_HUNTER_INSTRUCTION,
                 "Searches the web for job postings matching a parsed resume + preferences",
                 toolsets=[AgentToolset.POD, AgentToolset.WEB_SEARCH, AgentToolset.WORKSPACE_CLI],
                 input_schema=make_schema(JOB_HUNTER_INPUT),
                 output_schema=make_schema(JOB_HUNTER_OUTPUT))
    create_agent(pod, "resume_parser", RESUME_PARSER_INSTRUCTION,
                 "Parses uploaded resume PDF into structured skills/experience JSON",
                 toolsets=[AgentToolset.POD, AgentToolset.WORKSPACE_CLI],
                 input_schema=make_schema(RESUME_PARSER_INPUT),
                 output_schema=make_schema(RESUME_PARSER_OUTPUT))
    create_agent(pod, "placement_runner", PLACEMENT_RUNNER_INSTRUCTION,
                 "Orchestrates the full placement cycle: parse → hunt → score → draft",
                 toolsets=[AgentToolset.POD, AgentToolset.SUBAGENTS, AgentToolset.WORKSPACE_CLI],
                 input_schema=make_schema(PLACEMENT_RUNNER_INPUT),
                 output_schema=make_schema(PLACEMENT_RUNNER_OUTPUT))
    create_agent(pod, "outreach_composer", OUTREACH_COMPOSER_INSTRUCTION,
                 "Drafts personalised recruiter outreach per job match",
                 toolsets=[AgentToolset.POD, AgentToolset.WEB_SEARCH, AgentToolset.WORKSPACE_CLI],
                 input_schema=make_schema(OUTREACH_COMPOSER_INPUT),
                 output_schema=make_schema(OUTREACH_COMPOSER_OUTPUT))


def update_agents(pod):
    print("\n🔄 Updating agent instructions, toolsets and schemas...")
    update_agent_instruction(pod, "job_hunter", JOB_HUNTER_INSTRUCTION,
                             toolsets=[AgentToolset.POD, AgentToolset.WEB_SEARCH, AgentToolset.WORKSPACE_CLI],
                             input_schema=make_schema(JOB_HUNTER_INPUT),
                             output_schema=make_schema(JOB_HUNTER_OUTPUT))
    update_agent_instruction(pod, "resume_parser", RESUME_PARSER_INSTRUCTION,
                             toolsets=[AgentToolset.POD, AgentToolset.WORKSPACE_CLI],
                             input_schema=make_schema(RESUME_PARSER_INPUT),
                             output_schema=make_schema(RESUME_PARSER_OUTPUT))
    update_agent_instruction(pod, "placement_runner", PLACEMENT_RUNNER_INSTRUCTION,
                             toolsets=[AgentToolset.POD, AgentToolset.SUBAGENTS, AgentToolset.WORKSPACE_CLI],
                             input_schema=make_schema(PLACEMENT_RUNNER_INPUT),
                             output_schema=make_schema(PLACEMENT_RUNNER_OUTPUT))
    update_agent_instruction(pod, "outreach_composer", OUTREACH_COMPOSER_INSTRUCTION,
                             toolsets=[AgentToolset.POD, AgentToolset.WEB_SEARCH, AgentToolset.WORKSPACE_CLI],
                             input_schema=make_schema(OUTREACH_COMPOSER_INPUT),
                             output_schema=make_schema(OUTREACH_COMPOSER_OUTPUT))


# ── Functions ──────────────────────────────────────────────────────────────────

SCORE_MATCH_CODE = '''#input_type_name: ScoreMatchInput
#output_type_name: ScoreMatchResult
#function_name: score_match
"""Deterministic skill-overlap scorer. Reads the parsed resume + the parsed JD's jd_skills, computes a
simple but defensible 0-100 score, and writes (or updates) the job_matches row."""
from __future__ import annotations
import re
from typing import Iterable
from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext, Pod

class ScoreMatchInput(BaseModel):
    resume_id: str = Field(..., description="resumes.id of the resume to score against.")
    job_id: str = Field(..., description="job_postings.id to score.")
    min_score_to_notify: float = Field(50.0, description="If the score is below this, mark the match as 'skipped' (no draft).")

class ScoreMatchResult(BaseModel):
    match_id: str = ""
    score: float = 0.0
    status: str = "skipped"
    matched_skills: list = []
    missing_skills: list = []

def _norm(s: str) -> str:
    return re.sub(r"\\s+", " ", s.strip().lower())

def _as_set(items: Iterable) -> set:
    out: set = set()
    for it in items or []:
        if isinstance(it, str):
            n = _norm(it)
            if n:
                out.add(n)
    return out

async def score_match(ctx: FunctionContext, data: ScoreMatchInput) -> ScoreMatchResult:
    pod = Pod.from_env()
    resume = pod.table("resumes").get(data.resume_id)
    job = pod.table("job_postings").get(data.job_id)
    parsed = resume.get("parsed") or {}
    jd = job.get("jd_skills") or {}
    resume_skills = _as_set(parsed.get("skills", []) if isinstance(parsed, dict) else [])
    # Handle both flat list ["python","rag"] and dict {"required":[], "nice_to_have":[]}
    if isinstance(jd, list):
        required = _as_set(jd)
        nice = set()
    elif isinstance(jd, dict):
        required = _as_set(jd.get("required", []))
        nice = _as_set(jd.get("nice_to_have", []))
    else:
        required = set()
        nice = set()
    if not required and not nice:
        title_words = _as_set(re.findall(r"[a-zA-Z]+", job.get("title") or ""))
        recent = _as_set(re.findall(r"[a-zA-Z]+", parsed.get("recent_role", "") or ""))
        overlap = len(title_words & recent)
        score = float(min(90.0, 40.0 + overlap * 8))
        matched = sorted(title_words & recent)
        missing = sorted(title_words - recent)
    else:
        matched_req = sorted(resume_skills & required)
        matched_nice = sorted(resume_skills & nice)
        missing_req = sorted(required - resume_skills)
        missing_nice = sorted(nice - resume_skills)
        cov_req = (len(matched_req) / max(1, len(required))) if required else 0.5
        cov_nice = (len(matched_nice) / max(1, len(nice))) if nice else 0.0
        score = round(70.0 * cov_req + 30.0 * cov_nice, 1)
        matched = matched_req + matched_nice
        missing = missing_req + missing_nice
    existing = pod.records.list(
        "job_matches", limit=1,
        filter=[
            {"field": "resume_id", "op": "eq", "value": data.resume_id},
            {"field": "job_id", "op": "eq", "value": data.job_id},
        ],
    ).to_dict()["items"]
    status = "new" if score >= data.min_score_to_notify else "skipped"
    payload = {
        "job_id": data.job_id, "resume_id": data.resume_id,
        "score": score, "matched_skills": matched,
        "missing_skills": missing,
        "reasoning": f"{len(matched)} skill hits -> {score}/100",
        "status": status,
    }
    if existing:
        match_id = str(existing[0]["id"])
        pod.table("job_matches").update(match_id, payload)
    else:
        row = pod.table("job_matches").create(payload)
        match_id = str(row["id"])
    return ScoreMatchResult(match_id=match_id, score=score, status=status, matched_skills=matched, missing_skills=missing)
'''

KICK_OFF_CODE = '''#input_type_name: KickOffInput
#output_type_name: KickOffResult
#function_name: kick_off_parsed_resumes
"""Kick off the placement pipeline for every parsed resume. Replaces the human Kicker form step."""
from __future__ import annotations
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from lemma_sdk import FunctionContext, Pod

POLL_INTERVAL_SEC = 2.0
DEFAULT_RESUME_TIMEOUT_SEC = 600.0
DEFAULT_MAX_HUNT = 25
DEFAULT_MAX_DRAFTS = 5
DEFAULT_MIN_SCORE = 55
DEFAULT_CHANNELS = ["email"]

class KickOffInput(BaseModel):
    max_hunt: int = Field(DEFAULT_MAX_HUNT, ge=1, le=100)
    max_drafts: int = Field(DEFAULT_MAX_DRAFTS, ge=1, le=20)
    min_score: int = Field(DEFAULT_MIN_SCORE, ge=0, le=100)
    channels: List = Field(default_factory=lambda: list(DEFAULT_CHANNELS))
    resume_timeout_sec: float = Field(DEFAULT_RESUME_TIMEOUT_SEC, ge=30.0, le=3600.0)
    poll_interval_sec: float = Field(POLL_INTERVAL_SEC, ge=0.5, le=15.0)

class KickOffResult(BaseModel):
    resume_ids: List = Field(default_factory=list)
    parsed_resume_count: int = 0
    draft_count: int = 0
    total_new_jobs: int = 0
    total_scored: int = 0
    total_matches_above_threshold: int = 0
    drafted_outreach_ids: List = Field(default_factory=list)
    per_resume: List = Field(default_factory=list)
    errors: List = Field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _to_plain(record_or_model: Any) -> dict:
    if record_or_model is None:
        return {}
    if hasattr(record_or_model, "to_dict"):
        return record_or_model.to_dict()
    if isinstance(record_or_model, dict):
        return record_or_model
    return dict(record_or_model)

async def _run_pipeline_for_resume(pod: Pod, resume: dict, cfg: KickOffInput) -> dict:
    rid = str(resume["id"])
    label = resume.get("label") or ""
    out: dict = {"resume_id": rid, "label": label, "status": "pending"}
    try:
        directive = json.dumps({"resume_id": rid, "max_hunt": cfg.max_hunt, "max_drafts": cfg.max_drafts, "min_score": cfg.min_score, "channels": list(cfg.channels)}, separators=(",", ":"))
        conv = pod.agents.run("placement_runner", directive)
        conv_id = str(getattr(conv, "id", conv))
        deadline = time.time() + cfg.resume_timeout_sec
        last_status = None
        cur_d: dict = {}
        while time.time() < deadline:
            try:
                cur = pod.conversations.get(conv_id)
            except Exception as poll_exc:
                out.setdefault("poll_warnings", []).append(str(poll_exc))
                await asyncio.sleep(cfg.poll_interval_sec)
                continue
            cur_d = _to_plain(cur)
            last_status = (cur_d.get("last_run_status") or cur_d.get("status") or "").upper() or None
            if last_status in {"COMPLETED", "FAILED", "STOPPED", "CANCELLED"}:
                break
            await asyncio.sleep(cfg.poll_interval_sec)
        if last_status != "COMPLETED":
            out["status"] = "failed"
            out["error"] = f"placement_runner ended in state={last_status}"
            return out
        agent_output = cur_d.get("output") or {}
        drafted = agent_output.get("drafted_outreach_ids") or []
        if not isinstance(drafted, list):
            drafted = []
        out.update({"status": "completed", "new_jobs": int(agent_output.get("new_jobs") or 0), "scored": int(agent_output.get("scored") or 0), "matches_above_threshold": int(agent_output.get("matches_above_threshold") or 0), "drafted_outreach_ids": drafted, "errors": list(agent_output.get("errors") or [])})
        return out
    except Exception as exc:
        out["status"] = "failed"
        out["error"] = str(exc)
        return out

async def kick_off_parsed_resumes(ctx: FunctionContext, data: Optional[KickOffInput] = None) -> KickOffResult:
    cfg = data or KickOffInput()
    pod = Pod.from_env()
    started = _now_iso()
    listing = pod.records.list("resumes", limit=500, filter=[{"field": "status", "op": "eq", "value": "parsed"}])
    listing_d = _to_plain(listing)
    raw_items = listing_d.get("items") or []
    parsed_resumes: List = []
    for r in raw_items:
        if isinstance(r, dict) and r.get("status") == "parsed":
            parsed_resumes.append({"id": str(r.get("id")), "label": r.get("label") or ""})
    result = KickOffResult(resume_ids=[r["id"] for r in parsed_resumes], parsed_resume_count=len(parsed_resumes), started_at=started)
    if not parsed_resumes:
        result.finished_at = _now_iso()
        result.errors.append("No resumes with status=\'parsed\' found.")
        return result
    for resume in parsed_resumes:
        summary = await _run_pipeline_for_resume(pod, resume, cfg)
        result.per_resume.append(summary)
        if summary.get("status") == "completed":
            result.drafted_outreach_ids.extend(summary.get("drafted_outreach_ids") or [])
            result.total_new_jobs += int(summary.get("new_jobs") or 0)
            result.total_scored += int(summary.get("scored") or 0)
            result.total_matches_above_threshold += int(summary.get("matches_above_threshold") or 0)
        else:
            result.errors.append(f"resume {summary.get(\'resume_id\')}: {summary.get(\'error\') or \'unknown\'}")
    seen = set()
    deduped: List = []
    for oid in result.drafted_outreach_ids:
        if oid not in seen:
            seen.add(oid)
            deduped.append(oid)
    result.drafted_outreach_ids = deduped
    result.draft_count = len(result.drafted_outreach_ids)
    result.finished_at = _now_iso()
    return result
'''


def setup_functions(pod):
    print("\n⚙️  Creating functions...")
    create_function(pod, "score_match", SCORE_MATCH_CODE,
                    "Score and persist a (resume, job) pair. Deterministic overlap score, written to job_matches.")
    create_function(pod, "kick_off_parsed_resumes", KICK_OFF_CODE,
                    "Read every resumes row with status='parsed' and run placement_runner for each one.")


def update_functions(pod):
    print("\n🔄 Updating functions...")
    update_function(pod, "score_match", SCORE_MATCH_CODE,
                    "Score and persist a (resume, job) pair. Deterministic overlap score, written to job_matches.")
    update_function(pod, "kick_off_parsed_resumes", KICK_OFF_CODE,
                    "Read every resumes row with status='parsed' and run placement_runner for each one.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    pod_id = os.getenv("LEMMA_POD_ID")

    if not pod_id:
        print("❌ Missing LEMMA_POD_ID in environment.")
        print("   Copy .env.example to .env and fill in your pod ID.")
        sys.exit(1)

    print("🚀 Setting up Placement Pilot pod...")
    print(f"   Pod ID: {pod_id[:8]}...")

    with Pod.from_env() as pod:
        setup_tables(pod)
        setup_agents(pod)
        setup_functions(pod)
        update_agents(pod)
        update_functions(pod)

    print("\n📋 Next step — create the workflow:")
    print("  lemma workflow create --file ./placement_cycle.json")
    print("\n✅ Pod setup complete!")
    print("\nNext steps:")
    print("  1. Upload your resume: Docs → Personal files → placement")
    print("  2. Add your profile: Data → user_profiles → New Record")
    print("  3. lemma workflow create --file ./placement_cycle.json")
    print("  4. python setup_permissions.py")
    print("  5. streamlit run app.py")


if __name__ == "__main__":
    main()