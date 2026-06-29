"""
Placement Pilot — app.py
AI-powered job placement assistant built on Lemma SDK.
Single-user mode — each deployment is one user's personal pod.
Run: streamlit run app.py
"""

import streamlit as st
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from lemma_sdk import Pod, LemmaAPIError

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Placement Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stApp { background-color: #0f1117; }
    .pilot-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 12px; margin-bottom: 2rem; text-align: center;
    }
    .pilot-header h1 { color: white; font-size: 2.5rem; margin: 0; }
    .pilot-header p { color: rgba(255,255,255,0.85); margin: 0.5rem 0 0; font-size: 1.1rem; }
    .metric-card {
        background: #1e2130; border: 1px solid #2d3250;
        border-radius: 10px; padding: 1.2rem; text-align: center;
    }
    .metric-card .number { font-size: 2rem; font-weight: 700; color: #667eea; }
    .metric-card .label { font-size: 0.85rem; color: #8b92a5; margin-top: 0.3rem; }
    .score-high { color: #48bb78; font-weight: 700; }
    .score-mid { color: #ed8936; font-weight: 700; }
    .score-low { color: #fc8181; font-weight: 700; }
    .draft-card {
        background: #1a1f35; border: 1px solid #2d3250;
        border-left: 4px solid #667eea; border-radius: 8px;
        padding: 1.2rem; margin-bottom: 1rem;
    }
    div[data-testid="stSidebarContent"] { background-color: #161a27; }
    .stButton button { border-radius: 8px; font-weight: 600; }
    h1, h2, h3 { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)


# ── Pod connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_pod():
    return Pod.from_env()


def safe_list(pod, table, filter=None, **kwargs):
    try:
        result = pod.records.list(table, filter=filter, **kwargs)
        data = result.to_dict() if hasattr(result, 'to_dict') else result
        return data.get("items", []) if isinstance(data, dict) else []
    except Exception:
        return []


def safe_get(pod, table, record_id):
    try:
        result = pod.records.get(table, record_id)
        return result.to_dict() if hasattr(result, 'to_dict') else result
    except Exception:
        return None


def parse_json_field(val):
    if isinstance(val, list): return val
    if isinstance(val, str):
        try: return json.loads(val)
        except: return []
    return []


# ── Onboarding ─────────────────────────────────────────────────────────────────
def show_onboarding(pod):
    st.markdown("""
    <div class="pilot-header">
        <h1>🚀 Placement Pilot</h1>
        <p>Your AI co-pilot for campus placements — running autonomously every morning at 8 AM.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👋 Welcome! Set up your placement profile")
    st.markdown("This takes 2 minutes and personalises every job hunt to your skills and goals.")
    st.markdown("---")

    with st.form("onboarding_form"):
        name = st.text_input("Your full name *", placeholder="Rishi Bansal")
        roles_input = st.text_area("Target roles * (one per line)",
            placeholder="ML Engineer Intern\nGenAI Engineer\nAI Automation Engineer", height=100)
        locations_input = st.text_area("Preferred locations (one per line)",
            placeholder="Remote\nBangalore\nHyderabad", height=80)
        experience_level = st.selectbox("Experience level",
            ["intern", "fresher", "junior", "mid", "senior"], index=0)
        company_prefs_input = st.text_input("Company preferences (comma separated)",
            placeholder="startups, product companies, Series A+")
        channels = st.multiselect("Outreach channels", ["email", "linkedin"], default=["email"])

        submitted = st.form_submit_button("🚀 Get Started", use_container_width=True)
        if submitted:
            if not name or not roles_input:
                st.error("Name and target roles are required.")
            else:
                try:
                    pod.records.create("user_profiles", {
                        "name": name,
                        "target_roles": [r.strip() for r in roles_input.split("\n") if r.strip()],
                        "locations": [l.strip() for l in locations_input.split("\n") if l.strip()] or ["Remote"],
                        "experience_level": experience_level,
                        "company_prefs": [c.strip() for c in company_prefs_input.split(",") if c.strip()] or ["startups"],
                        "channels": channels or ["email"],
                        "is_active": True,
                    })
                    st.success("✅ Profile created! Now upload your resume.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")


# ── Sidebar ────────────────────────────────────────────────────────────────────
def show_sidebar(pod, profile):
    with st.sidebar:
        st.markdown("## 🚀 Placement Pilot")
        st.markdown(f"**{profile.get('name', 'User')}**")
        st.markdown(f"_{profile.get('experience_level', 'intern')} level_")
        st.markdown("---")

        page = st.radio("Navigate", [
            "🏠 Dashboard", "🔍 Hunt Jobs", "📋 My Pipeline",
            "✅ Approvals", "📄 My Resume", "👤 Profile"
        ], label_visibility="collapsed")

        st.markdown("---")
        matches = safe_list(pod, "job_matches", limit=100)
        drafts = safe_list(pod, "outreach_messages", limit=100)
        pending = [d for d in drafts if d.get("status") == "drafted"]
        st.metric("Total Matches", len(matches))
        st.metric("Pending Approvals", len(pending))

        return page


# ── Dashboard ──────────────────────────────────────────────────────────────────
def show_dashboard(pod, profile):
    st.markdown("""<div class="pilot-header">
        <h1>🚀 Placement Pilot</h1>
        <p>Your AI co-pilot — hunting jobs autonomously every morning at 8 AM.</p>
    </div>""", unsafe_allow_html=True)

    jobs = safe_list(pod, "job_postings", limit=500)
    matches = safe_list(pod, "job_matches", limit=500)
    drafts = safe_list(pod, "outreach_messages", limit=500)
    resumes = safe_list(pod, "resumes", limit=10)

    pending = [d for d in drafts if d.get("status") == "drafted"]
    sent = [d for d in drafts if d.get("status") == "sent"]
    high_matches = [m for m in matches if float(m.get("score", 0)) >= 60]

    if not resumes:
        st.info("👋 **Welcome!** Upload your resume to get started → go to **📄 My Resume** tab.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="number">{len(jobs)}</div><div class="label">Jobs Found</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="number">{len(high_matches)}</div><div class="label">Strong Matches (60+)</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="number">{len(pending)}</div><div class="label">Awaiting Approval</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="number">{len(sent)}</div><div class="label">Emails Sent</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📬 Recent Matches")
        if matches:
            for m in sorted(matches, key=lambda x: float(x.get("score", 0)), reverse=True)[:5]:
                score = float(m.get("score", 0))
                score_class = "score-high" if score >= 70 else "score-mid" if score >= 50 else "score-low"
                job = safe_get(pod, "job_postings", str(m.get("job_id", "")))
                title = job.get("title", "Unknown") if job else "Unknown"
                company = job.get("company", "") if job else ""
                url = job.get("source_url", "") if job else ""
                matched = parse_json_field(m.get("matched_skills", []))
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{title}** — {company}")
                    st.caption(", ".join(matched[:5]) if matched else "no skills matched")
                with c2:
                    st.markdown(f'<span class="{score_class}">{score:.0f}%</span>', unsafe_allow_html=True)
                    if url: st.link_button("Apply →", url)
        else:
            st.info("No matches yet. Run a hunt!")

    with col2:
        st.markdown("### ⚡ Quick Actions")
        if pending:
            st.warning(f"🔔 {len(pending)} draft(s) waiting!")
        st.success("⏰ Morning hunt: weekdays 8 AM")


# ── Hunt Jobs ──────────────────────────────────────────────────────────────────
def show_hunt(pod, profile):
    st.markdown("## 🔍 Hunt Jobs")
    resumes = safe_list(pod, "resumes", limit=10)
    parsed = [r for r in resumes if r.get("status") == "parsed"]

    if not parsed:
        st.error("⚠️ No parsed resume. Go to **📄 My Resume** tab first.")
        return

    resume = parsed[0]
    resume_id = str(resume.get("id", ""))
    st.success(f"✅ Using: **{resume.get('label', 'My Resume')}**")

    col1, col2, col3 = st.columns(3)
    with col1: max_hunt = st.slider("Max jobs", 5, 30, 10)
    with col2: max_drafts = st.slider("Max drafts", 1, 5, 3)
    with col3: min_score = st.slider("Min score", 30, 80, 45)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Run Hunt Now", use_container_width=True, type="primary"):
            with st.spinner("Hunting for jobs..."):
                try:
                    channels = parse_json_field(profile.get("channels", ["email"]))
                    conv = pod.agents.run("placement_runner", json.dumps({
                        "resume_id": resume_id, "max_hunt": max_hunt,
                        "max_drafts": max_drafts, "min_score": min_score, "channels": channels
                    }))
                    conv_id = str(getattr(conv, "id", conv))
                    deadline = time.time() + 120
                    progress = st.progress(0)
                    status_text = st.empty()
                    i = 0
                    while time.time() < deadline:
                        try:
                            cur = pod.conversations.get(conv_id)
                            cur_d = cur.to_dict() if hasattr(cur, 'to_dict') else cur
                            last_status = (cur_d.get("last_run_status") or cur_d.get("status") or "").upper()
                            if last_status in {"COMPLETED", "FAILED", "STOPPED"}:
                                if last_status == "COMPLETED":
                                    out = cur_d.get("output") or {}
                                    st.success(f"✅ Found {out.get('new_jobs', 0)} jobs, drafted {len(out.get('drafted_outreach_ids', []))} emails!")
                                else:
                                    st.error(f"Hunt ended: {last_status}")
                                break
                            i = min(i + 5, 90)
                            progress.progress(i)
                            status_text.text(f"Running... ({last_status})")
                            time.sleep(10)
                        except Exception:
                            time.sleep(10)
                    else:
                        st.info("Still running in background. Check back in a few minutes.")
                except Exception as e:
                    st.error(f"Failed: {e}")

    with col2:
        with st.expander("🗑️ Clear data & fresh hunt"):
            st.warning("Deletes all jobs, matches and drafts for a clean slate.")
            if st.button("🗑️ Clear All & Re-hunt", use_container_width=True):
                with st.spinner("Clearing..."):
                    for table in ["outreach_messages", "job_matches", "job_postings"]:
                        rows = safe_list(pod, table, limit=500)
                        for row in rows:
                            try: pod.records.delete(table, str(row["id"]))
                            except: pass
                    st.success("Cleared! Starting fresh hunt...")
                    channels = parse_json_field(profile.get("channels", ["email"]))
                    pod.agents.run("placement_runner", json.dumps({
                        "resume_id": resume_id, "max_hunt": max_hunt,
                        "max_drafts": max_drafts, "min_score": min_score, "channels": channels
                    }))
                    st.info("Hunt started! Check back in 5-10 minutes.")

    st.markdown("---")
    st.markdown("### 📊 Recent Job Postings")
    jobs = safe_list(pod, "job_postings", limit=20)
    for j in jobs[:10]:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{j.get('title', 'Unknown')}** — {j.get('company', '')}")
            st.caption(f"📍 {j.get('location', 'India')} · {j.get('source', 'other')}")
        with col2:
            if j.get("source_url"): st.link_button("View", j["source_url"])
    if not jobs: st.info("No jobs yet. Run a hunt!")


# ── Pipeline ───────────────────────────────────────────────────────────────────
def show_pipeline(pod):
    st.markdown("## 📋 My Pipeline")
    matches = safe_list(pod, "job_matches", limit=100)
    if not matches:
        st.info("No matches yet. Run a hunt!")
        return

    col1, col2 = st.columns([2, 1])
    with col1: min_score_filter = st.slider("Min score", 0, 100, 0)
    with col2: status_filter = st.selectbox("Status", ["all", "new", "picked", "skipped", "applied"])

    filtered = sorted(
        [m for m in matches if float(m.get("score", 0)) >= min_score_filter
         and (status_filter == "all" or m.get("status") == status_filter)],
        key=lambda x: float(x.get("score", 0)), reverse=True
    )
    st.markdown(f"**{len(filtered)} matches**")
    st.markdown("---")

    for m in filtered:
        score = float(m.get("score", 0))
        score_class = "score-high" if score >= 70 else "score-mid" if score >= 50 else "score-low"
        match_id = str(m.get("id", ""))
        job = safe_get(pod, "job_postings", str(m.get("job_id", "")))
        title = job.get("title", "Unknown") if job else "Unknown"
        company = job.get("company", "") if job else ""
        url = job.get("source_url", "") if job else ""
        matched = parse_json_field(m.get("matched_skills", []))
        missing = parse_json_field(m.get("missing_skills", []))

        with st.expander(f"**{title}** — {company}  |  {score:.0f}%"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"✅ {', '.join(matched[:6]) if matched else 'none'}")
                st.markdown(f"❌ {', '.join(missing[:4]) if missing else 'none'}")
            with col2:
                st.markdown(f"_{m.get('reasoning', '')}_")
            with col3:
                if url: st.link_button("🔗 Apply", url, use_container_width=True)
                new_status = st.selectbox("Status", ["new", "picked", "skipped", "applied"],
                    index=["new", "picked", "skipped", "applied"].index(m.get("status", "new")),
                    key=f"s_{match_id}")
                if new_status != m.get("status"):
                    if st.button("Save", key=f"sv_{match_id}"):
                        pod.records.update("job_matches", match_id, {"status": new_status})
                        st.rerun()


# ── Approvals ──────────────────────────────────────────────────────────────────
def show_approvals(pod):
    st.markdown("## ✅ Approvals Queue")
    drafts = safe_list(pod, "outreach_messages", limit=50)
    pending = [d for d in drafts if d.get("status") == "drafted"]

    if not pending:
        sent = [d for d in drafts if d.get("status") == "sent"]
        st.success(f"✅ No pending approvals! {len(sent)} sent.")
        return

    st.info(f"🔔 {len(pending)} draft(s) waiting")
    st.markdown("---")

    for draft in pending:
        draft_id = str(draft.get("id", ""))
        channel = draft.get("channel", "email")
        recipient = draft.get("recipient", "")
        subject = draft.get("subject", "")
        body = draft.get("body", "")
        job = safe_get(pod, "job_postings", str(draft.get("job_id", ""))) if draft.get("job_id") else None
        job_title = job.get("title", "Unknown") if job else "Unknown"
        company = job.get("company", "") if job else ""
        job_url = job.get("source_url", "") if job else ""

        st.markdown(f'<div class="draft-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {job_title} @ {company}")
            if channel == "portal":
                st.markdown(f"🌐 **Portal** — Apply at: [{recipient}]({recipient})")
            else:
                st.markdown(f"📧 **{channel.upper()}** → `{recipient}`")
                if subject: st.markdown(f"**Subject:** {subject}")
        with col2:
            if job_url: st.link_button("🔗 View Job", job_url, use_container_width=True)

        if channel != "portal" and body:
            with st.expander("📝 View / Edit draft"):
                edited = st.text_area("Email body", value=body, height=250, key=f"edit_{draft_id}")
                if edited != body:
                    if st.button("💾 Save edits", key=f"save_edit_{draft_id}"):
                        pod.records.update("outreach_messages", draft_id, {"body": edited})
                        st.success("Saved!")

        col1, col2 = st.columns(2)
        with col1:
            btn_label = "✅ Mark as Applied" if channel == "portal" else "✅ Approve & Send"
            if st.button(btn_label, key=f"approve_{draft_id}", use_container_width=True, type="primary"):
                try:
                    if channel == "portal":
                        pod.records.update("outreach_messages", draft_id, {
                            "status": "sent", "sent_at": datetime.utcnow().isoformat()
                        })
                        st.success("✅ Marked as applied!")
                        st.rerun()
                    else:
                        with st.spinner("Sending..."):
                            try:
                                pod.connectors.operations.execute(
                                    auth_config="gmail",
                                    operation="GMAIL_SEND_EMAIL",
                                    payload={"to": recipient, "subject": subject or f"Opportunity — {job_title}", "body": body},
                                    account_id=os.getenv("GMAIL_ACCOUNT_ID", "")
                                )
                                pod.records.update("outreach_messages", draft_id, {
                                    "status": "sent",
                                    "approved_at": datetime.utcnow().isoformat(),
                                    "sent_at": datetime.utcnow().isoformat()
                                })
                                st.success("✅ Email sent!")
                                st.rerun()
                            except Exception as send_err:
                                st.error(f"❌ Send failed: {send_err}")
                except Exception as e:
                    st.error(f"Failed: {e}")
        with col2:
            if st.button("❌ Skip", key=f"skip_{draft_id}", use_container_width=True):
                pod.records.update("outreach_messages", draft_id, {"status": "skipped"})
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("")


# ── Resume ─────────────────────────────────────────────────────────────────────
def show_resume(pod):
    st.markdown("## 📄 My Resume")
    resumes = safe_list(pod, "resumes", limit=10)

    if resumes:
        for r in resumes:
            resume_id = str(r.get("id", ""))
            status = r.get("status", "raw")
            icon = "🟢" if status == "parsed" else "🟡" if status == "parsing" else "🔴"

            with st.expander(f"{icon} **{r.get('label', 'Resume')}** — `{status}`"):
                if status == "parsed" and r.get("parsed"):
                    parsed = r.get("parsed", {})
                    if isinstance(parsed, str):
                        try: parsed = json.loads(parsed)
                        except: parsed = {}
                    skills = parsed.get("skills", [])
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Role:** {parsed.get('recent_role', 'N/A')}")
                        st.markdown(f"**Experience:** {parsed.get('years_experience', 0)} years")
                        edu = parsed.get("education", [])
                        if edu and isinstance(edu, list):
                            e = edu[0]
                            if isinstance(e, dict):
                                st.markdown(f"**Education:** {e.get('institution', '')} — {e.get('degree', '')}")
                    with col2:
                        st.markdown(f"**Skills ({len(skills)}):**")
                        st.markdown(", ".join(skills[:20]))
                elif status == "raw":
                    st.info("Not parsed yet.")
                    if st.button("🔍 Parse Now", key=f"parse_{resume_id}"):
                        pod.agents.run("resume_parser", json.dumps({"resume_id": resume_id}))
                        st.success("Parsing started!")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Re-parse", key=f"reparse_{resume_id}"):
                        pod.records.update("resumes", resume_id, {"status": "raw"})
                        pod.agents.run("resume_parser", json.dumps({"resume_id": resume_id}))
                        st.success("Re-parsing started!")
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{resume_id}", type="secondary"):
                        try:
                            fp = r.get("file_path", "")
                            if fp:
                                try: pod.files.delete(fp)
                                except: pass
                            pod.records.delete("resumes", resume_id)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown("### Upload New Resume")
    uploaded = st.file_uploader("Choose PDF", type=["pdf"])
    label = st.text_input("Label", placeholder="Rishi Bansal - GenAI 2026")

    if uploaded and st.button("📤 Upload", type="primary"):
        with st.spinner("Uploading..."):
            try:
                path = f"/resumes/{uploaded.name}"
                pod.files.upload_file(uploaded, path=path, filename=uploaded.name)
                pod.records.create("resumes", {"label": label or uploaded.name, "file_path": path, "status": "raw"})
                st.success("✅ Resume uploaded! It will be parsed automatically when you run a hunt.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")


# ── Profile ────────────────────────────────────────────────────────────────────
def show_profile(pod, profile):
    st.markdown("## 👤 My Profile")
    profile_id = str(profile.get("id", ""))

    with st.form("profile_form"):
        name = st.text_input("Full name", value=profile.get("name", ""))
        roles = parse_json_field(profile.get("target_roles", []))
        roles_input = st.text_area("Target roles (one per line)", value="\n".join(roles), height=120)
        locs = parse_json_field(profile.get("locations", []))
        locations_input = st.text_area("Preferred locations (one per line)", value="\n".join(locs), height=80)
        exp_options = ["intern", "fresher", "junior", "mid", "senior"]
        exp = profile.get("experience_level", "intern")
        experience_level = st.selectbox("Experience level", exp_options,
            index=exp_options.index(exp) if exp in exp_options else 0)
        prefs = parse_json_field(profile.get("company_prefs", []))
        company_prefs_input = st.text_input("Company preferences (comma separated)", value=", ".join(prefs))
        chans = parse_json_field(profile.get("channels", ["email"]))
        channels = st.multiselect("Outreach channels", ["email", "linkedin"],
            default=[c for c in chans if c in ["email", "linkedin"]])

        if st.form_submit_button("💾 Save Profile", use_container_width=True):
            try:
                pod.records.update("user_profiles", profile_id, {
                    "name": name,
                    "target_roles": [r.strip() for r in roles_input.split("\n") if r.strip()],
                    "locations": [l.strip() for l in locations_input.split("\n") if l.strip()],
                    "experience_level": experience_level,
                    "company_prefs": [c.strip() for c in company_prefs_input.split(",") if c.strip()],
                    "channels": channels,
                })
                st.success("✅ Profile updated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    try:
        pod = get_pod()
    except Exception as e:
        st.error(f"Failed to connect to pod: {e}")
        st.markdown("Make sure `LEMMA_POD_ID` is in `.env` and you've run `lemma auth login`.")
        return

    profiles = safe_list(pod, "user_profiles", limit=1)
    profile = profiles[0] if profiles else None

    if not profile:
        show_onboarding(pod)
        return

    page = show_sidebar(pod, profile)

    if page == "🏠 Dashboard": show_dashboard(pod, profile)
    elif page == "🔍 Hunt Jobs": show_hunt(pod, profile)
    elif page == "📋 My Pipeline": show_pipeline(pod)
    elif page == "✅ Approvals": show_approvals(pod)
    elif page == "📄 My Resume": show_resume(pod)
    elif page == "👤 Profile": show_profile(pod, profile)


if __name__ == "__main__":
    main()