import React, { useState, useRef } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  AuthGuard,
  useCurrentUser,
  useRecords,
  useCreateRecord,
  useUpdateRecord,
  useUploadFile,
  useAgentTask,
} from 'lemma-sdk/react'
import { lemmaClient } from './lemma-client'
import './styles.css'

const queryClient = new QueryClient()

function parseJson(val: unknown): any[] {
  if (Array.isArray(val)) return val
  if (typeof val === 'string') { try { return JSON.parse(val) } catch { return [] } }
  return []
}

// ── Types ──────────────────────────────────────────────────────────────────────
type Page = 'dashboard' | 'hunt' | 'pipeline' | 'approvals' | 'resume' | 'profile'

// ── Onboarding ─────────────────────────────────────────────────────────────────
function Onboarding({ onCreate }: { onCreate: () => void }) {
  const createProfile = useCreateRecord({ client: lemmaClient, tableName: 'user_profiles' })
  const [form, setForm] = useState({
    name: '', roles: '', locations: '', experience: 'intern', company_prefs: '', channels: ['email'],
    telegram_bot_token: '', telegram_chat_id: ''
  })
  const [error, setError] = useState('')

  const submit = async () => {
    if (!form.name || !form.roles) return setError('Name and target roles are required.')
    setError('')
    try {
      await createProfile.create({
        name: form.name,
        target_roles: form.roles.split('\n').map(r => r.trim()).filter(Boolean),
        locations: form.locations.split('\n').map(l => l.trim()).filter(Boolean),
        experience_level: form.experience,
        company_prefs: form.company_prefs.split(',').map(c => c.trim()).filter(Boolean),
        channels: form.channels,
        telegram_bot_token: form.telegram_bot_token || '',
        telegram_chat_id: form.telegram_chat_id || '',
        is_active: true,
      })
      onCreate()
    } catch (e: any) {
      setError(e.message || 'Failed to create profile')
    }
  }

  return (
    <div className="onboarding-wrap">
      <div className="hero-banner" style={{ marginBottom: 24 }}>
        <h1>🚀 Welcome to Placement Pilot</h1>
        <p>Set up your profile to start hunting jobs autonomously every morning at 8 AM.</p>
      </div>
      <div className="onboarding-card">
        <h2>Complete your profile</h2>
        <p className="muted" style={{ marginBottom: 20 }}>This takes 2 minutes and personalises every job hunt.</p>

        <label className="field-label">Full name *</label>
        <input className="input" placeholder="Rishi Bansal" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />

        <label className="field-label">Target roles * (one per line)</label>
        <textarea className="input" rows={4} placeholder="ML Engineer Intern&#10;GenAI Engineer&#10;AI Automation Engineer" value={form.roles} onChange={e => setForm(f => ({ ...f, roles: e.target.value }))} />

        <label className="field-label">Preferred locations (one per line)</label>
        <textarea className="input" rows={3} placeholder="Remote&#10;Bangalore&#10;Hyderabad" value={form.locations} onChange={e => setForm(f => ({ ...f, locations: e.target.value }))} />

        <label className="field-label">Experience level</label>
        <select className="input" value={form.experience} onChange={e => setForm(f => ({ ...f, experience: e.target.value }))}>
          {['intern', 'fresher', 'junior', 'mid', 'senior'].map(o => <option key={o}>{o}</option>)}
        </select>

        <label className="field-label">Company preferences (comma separated)</label>
        <input className="input" placeholder="startups, product companies, Series A+" value={form.company_prefs} onChange={e => setForm(f => ({ ...f, company_prefs: e.target.value }))} />

        <label className="field-label">Outreach channels</label>
        <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
          {['email', 'linkedin'].map(ch => (
            <label key={ch} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
              <input type="checkbox" checked={form.channels.includes(ch)}
                onChange={e => setForm(f => ({
                  ...f,
                  channels: e.target.checked ? [...f.channels, ch] : f.channels.filter(c => c !== ch)
                }))} />
              {ch}
            </label>
          ))}
        </div>

        <hr style={{ borderColor: '#2d3250', margin: '16px 0' }} />
        <p style={{ fontSize: 13, color: '#8b92a5', marginBottom: 12 }}>
          📱 <strong style={{ color: '#e2e8f0' }}>Telegram Notifications</strong> (optional) — get notified when jobs are found and emails are drafted.
        </p>
        <label className="field-label">Telegram Bot Token</label>
        <input className="input" type="password" placeholder="8404655790:AAH..."
          value={form.telegram_bot_token}
          onChange={e => setForm(f => ({ ...f, telegram_bot_token: e.target.value }))} />
        <label className="field-label">Telegram Chat ID</label>
        <input className="input" placeholder="1622560998"
          value={form.telegram_chat_id}
          onChange={e => setForm(f => ({ ...f, telegram_chat_id: e.target.value }))} />

        {error && <div className="alert-warn">{error}</div>}
        <button className="btn-primary btn-large" onClick={submit} disabled={createProfile.isSubmitting}>
          {createProfile.isSubmitting ? '⏳ Setting up...' : '🚀 Get Started'}
        </button>
      </div>
    </div>
  )
}

// ── Nav ────────────────────────────────────────────────────────────────────────
function Nav({ page, setPage, pendingCount, userName }: { page: Page; setPage: (p: Page) => void; pendingCount: number; userName: string }) {
  const items: { id: Page; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
    { id: 'hunt', label: 'Hunt Jobs', icon: '🔍' },
    { id: 'pipeline', label: 'Pipeline', icon: '📋' },
    { id: 'approvals', label: `Approvals${pendingCount > 0 ? ` (${pendingCount})` : ''}`, icon: '✅' },
    { id: 'resume', label: 'My Resume', icon: '📄' },
    { id: 'profile', label: 'Profile', icon: '👤' },
  ]
  return (
    <nav className="sidebar">
      <div className="brand">
        <span style={{ fontSize: 24 }}>🚀</span>
        <div>
          <strong>Placement Pilot</strong>
          <span style={{ fontSize: 11, color: '#8b92a5', display: 'block' }}>{userName}</span>
        </div>
      </div>
      {items.map(item => (
        <button key={item.id} className={`nav-btn ${page === item.id ? 'active' : ''}`} onClick={() => setPage(item.id)}>
          {item.icon} {item.label}
        </button>
      ))}
      <div style={{ marginTop: 'auto', padding: '12px 8px' }}>
        <div className="schedule-badge">⏰ Morning hunt: 8 AM weekdays</div>
      </div>
    </nav>
  )
}

// ── Dashboard ──────────────────────────────────────────────────────────────────
function Dashboard({ jobs, matches, drafts, resumes, setPage }: any) {
  const pending = drafts.filter((d: any) => d.status === 'drafted')
  const sent = drafts.filter((d: any) => d.status === 'sent')
  const highMatches = matches.filter((m: any) => parseFloat(m.score || 0) >= 60)
  const hasParsedResume = resumes.some((r: any) => r.status === 'parsed')

  return (
    <div className="page">
      <div className="hero-banner">
        <h1>🚀 Placement Pilot</h1>
        <p>Your AI co-pilot for campus placements — hunting jobs autonomously every morning at 8 AM.</p>
      </div>

      {!hasParsedResume && (
        <div className="alert-banner" style={{ marginBottom: 20 }}>
          👋 <strong>Welcome!</strong> Upload your resume to get started.
          <button className="btn-primary" onClick={() => setPage('resume')} style={{ marginTop: 8, width: 'fit-content' }}>
            📄 Upload Resume →
          </button>
        </div>
      )}

      <div className="metrics">
        {[
          { n: jobs.length, l: 'Jobs Found' },
          { n: highMatches.length, l: 'Strong Matches (60+)' },
          { n: pending.length, l: 'Awaiting Approval' },
          { n: sent.length, l: 'Emails Sent' },
        ].map(m => (
          <div key={m.l} className="metric-card">
            <div className="metric-num">{m.n}</div>
            <div className="metric-label">{m.l}</div>
          </div>
        ))}
      </div>

      <div className="two-col">
        <div className="panel">
          <h3>📬 Recent Matches</h3>
          {matches.length === 0 && <p className="muted">No matches yet. Run a hunt!</p>}
          {[...matches]
            .sort((a: any, b: any) => parseFloat(b.score) - parseFloat(a.score))
            .slice(0, 5)
            .map((m: any) => {
              const score = parseFloat(m.score || 0)
              const scoreClass = score >= 70 ? 'score-high' : score >= 50 ? 'score-mid' : 'score-low'
              const matched = parseJson(m.matched_skills).slice(0, 4).join(', ')
              return (
                <div key={m.id} className="match-row">
                  <div>
                    <div className="muted" style={{ fontSize: 11 }}>Match {m.id?.slice(0, 8)}...</div>
                    <div style={{ fontSize: 12, color: '#8b92a5' }}>{matched || 'no skills matched'}</div>
                  </div>
                  <span className={scoreClass}>{score.toFixed(0)}%</span>
                </div>
              )
            })}
        </div>
        <div className="panel">
          <h3>⚡ Quick Actions</h3>
          {pending.length > 0 && (
            <div className="alert-banner" style={{ marginBottom: 12 }}>
              🔔 {pending.length} draft(s) waiting!
              <button className="btn-primary" onClick={() => setPage('approvals')} style={{ marginTop: 8, width: 'fit-content' }}>Review Drafts →</button>
            </div>
          )}
          <button className="btn-primary" style={{ width: '100%', marginBottom: 10 }} onClick={() => setPage('hunt')}>
            🔍 Run Hunt Now
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Hunt Jobs ──────────────────────────────────────────────────────────────────
function HuntJobs({ resumes, jobs, profile }: any) {
  const [maxHunt, setMaxHunt] = useState(10)
  const [maxDrafts, setMaxDrafts] = useState(3)
  const [minScore, setMinScore] = useState(45)
  const [msg, setMsg] = useState('')
  const agentTask = useAgentTask({ client: lemmaClient, agentName: 'placement_runner' })
  const updateResume = useUpdateRecord({ client: lemmaClient, tableName: 'resumes' })

  const parsed = resumes.filter((r: any) => r.status === 'parsed')

  const runHunt = async () => {
    if (!parsed[0]) return setMsg('⚠️ No parsed resume found. Go to My Resume tab first.')
    setMsg('🔍 Hunt started! Jobs are being found and emails drafted in the background. Check back in 5-10 minutes...')
    agentTask.run({
      resume_id: parsed[0].id,
      max_hunt: maxHunt,
      max_drafts: maxDrafts,
      min_score: minScore,
      channels: parseJson(profile?.channels).length ? parseJson(profile.channels) : ['email'],
    }).catch((e: any) => setMsg(`❌ Error: ${e.message}`))
  }

  return (
    <div className="page">
      <h2>🔍 Hunt Jobs</h2>
      <p className="muted">Trigger a fresh job search based on your profile and resume.</p>

      {parsed[0] ? (
        <div className="success-badge">✅ Using: <strong>{parsed[0].label || 'My Resume'}</strong></div>
      ) : (
        <div className="alert-warn">⚠️ No parsed resume. Go to My Resume tab first.</div>
      )}

      <div className="controls">
        <label>Max jobs to find: <strong>{maxHunt}</strong>
          <input type="range" min={5} max={30} value={maxHunt} onChange={e => setMaxHunt(+e.target.value)} />
        </label>
        <label>Max emails to draft: <strong>{maxDrafts}</strong>
          <input type="range" min={1} max={5} value={maxDrafts} onChange={e => setMaxDrafts(+e.target.value)} />
        </label>
        <label>Min match score: <strong>{minScore}</strong>
          <input type="range" min={30} max={80} value={minScore} onChange={e => setMinScore(+e.target.value)} />
        </label>
      </div>

      <button className="btn-primary btn-large" onClick={runHunt} disabled={agentTask.isRunning}>
        {agentTask.isRunning ? `⏳ ${agentTask.activity || 'Running...'}` : '🚀 Run Hunt Now'}
      </button>

      {msg && <div className="status-msg">{msg}</div>}

      <div className="panel" style={{ marginTop: 24 }}>
        <h3>📊 Recent Job Postings ({jobs.length})</h3>
        {jobs.slice(0, 10).map((j: any) => (
          <div key={j.id} className="job-row">
            <div>
              <strong>{j.title}</strong> — {j.company}
              <div className="muted" style={{ fontSize: 12 }}>📍 {j.location || 'India'} · {j.source}</div>
            </div>
            {j.source_url && (
              <a href={j.source_url} target="_blank" rel="noreferrer" className="btn-secondary">View →</a>
            )}
          </div>
        ))}
        {jobs.length === 0 && <p className="muted">No jobs found yet. Run a hunt!</p>}
      </div>
    </div>
  )
}

// ── Pipeline ───────────────────────────────────────────────────────────────────
function Pipeline({ matches, jobs }: any) {
  const [minFilter, setMinFilter] = useState(0)
  const updateMatch = useUpdateRecord({ client: lemmaClient, tableName: 'job_matches' })

  const jobMap: Record<string, any> = {}
  jobs.forEach((j: any) => { jobMap[j.id] = j })

  const filtered = [...matches]
    .filter((m: any) => parseFloat(m.score || 0) >= minFilter)
    .sort((a: any, b: any) => parseFloat(b.score) - parseFloat(a.score))

  return (
    <div className="page">
      <h2>📋 My Pipeline</h2>
      <label className="field-label">Min score: <strong>{minFilter}%</strong></label>
      <input type="range" min={0} max={100} value={minFilter} onChange={e => setMinFilter(+e.target.value)} style={{ width: '100%', marginBottom: 16, accentColor: '#667eea' }} />
      <p className="muted" style={{ marginBottom: 16 }}>{filtered.length} matches</p>

      {filtered.map((m: any) => {
        const score = parseFloat(m.score || 0)
        const scoreClass = score >= 70 ? 'score-high' : score >= 50 ? 'score-mid' : 'score-low'
        const matched = parseJson(m.matched_skills)
        const missing = parseJson(m.missing_skills)
        const job = jobMap[m.job_id]

        return (
          <div key={m.id} className="match-card">
            <div className="match-header">
              <div>
                {job && <strong>{job.title} — {job.company}</strong>}
                {!job && <span className="muted">Job {m.job_id?.slice(0, 8)}...</span>}
              </div>
              <span className={scoreClass} style={{ fontSize: 20, fontWeight: 700 }}>{score.toFixed(0)}%</span>
            </div>
            <div style={{ fontSize: 13, marginBottom: 6 }}>
              ✅ <span style={{ color: '#48bb78' }}>{matched.slice(0, 6).join(', ') || 'none'}</span>
            </div>
            <div style={{ fontSize: 13, marginBottom: 10 }}>
              ❌ <span style={{ color: '#fc8181' }}>{missing.slice(0, 4).join(', ') || 'none'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <select
                value={m.status || 'new'}
                onChange={async e => {
                  await updateMatch.update({ status: e.target.value }, { recordId: m.id })
                }}
              >
                {['new', 'picked', 'skipped', 'applied'].map(s => <option key={s}>{s}</option>)}
              </select>
              {job?.source_url && (
                <a href={job.source_url} target="_blank" rel="noreferrer" className="btn-secondary">🔗 Apply</a>
              )}
            </div>
          </div>
        )
      })}
      {filtered.length === 0 && <p className="muted">No matches yet. Run a hunt!</p>}
    </div>
  )
}

// ── Approvals ──────────────────────────────────────────────────────────────────
function Approvals({ drafts, jobs }: any) {
  const [sending, setSending] = useState<string | null>(null)
  const [doneIds, setDoneIds] = useState<string[]>([])
  const updateDraft = useUpdateRecord({ client: lemmaClient, tableName: 'outreach_messages' })

  const jobMap: Record<string, any> = {}
  jobs.forEach((j: any) => { jobMap[j.id] = j })

  const pending = drafts.filter((d: any) => d.status === 'drafted' && !doneIds.includes(d.id))

  const sendEmail = async (draft: any) => {
    setSending(draft.id)
    try {
      await (lemmaClient as any).connectors.operations.execute(
        {
          organizationId: import.meta.env.VITE_ORG_ID || '',
          authConfigName: 'gmail',
        },
        'GMAIL_SEND_EMAIL',
        {
          recipient_email: draft.recipient,
          subject: draft.subject || 'Internship Opportunity',
          message_body: draft.body,
        },
        import.meta.env.VITE_GMAIL_ACCOUNT_ID || ''
      )
      await updateDraft.update({ status: 'sent', sent_at: new Date().toISOString() }, { recordId: draft.id })
      // Send Telegram notification
      try {
        await (lemmaClient as any).functions.run('send_telegram', {
          message: `✅ Email sent!\n📋 ${draft.subject || 'Outreach'}\n📧 To: ${draft.recipient}`
        })
      } catch (_) {}
      setDoneIds(prev => [...prev, draft.id])
    } catch (e: any) {
      alert(`Send failed: ${e.message}`)
    } finally {
      setSending(null)
    }
  }

  const markApplied = async (draft: any) => {
    await updateDraft.update({ status: 'sent', sent_at: new Date().toISOString() }, { recordId: draft.id })
    setDoneIds(prev => [...prev, draft.id])
  }

  const skip = async (draft: any) => {
    await updateDraft.update({ status: 'skipped' }, { recordId: draft.id })
    setDoneIds(prev => [...prev, draft.id])
  }

  if (pending.length === 0) {
    const sent = drafts.filter((d: any) => d.status === 'sent')
    return (
      <div className="page">
        <h2>✅ Approvals</h2>
        <div className="success-badge">✅ No pending approvals! {sent.length} email(s) sent.</div>
      </div>
    )
  }

  return (
    <div className="page">
      <h2>✅ Approvals Queue</h2>
      <p className="muted" style={{ marginBottom: 20 }}>{pending.length} draft(s) waiting for review</p>

      {pending.map((d: any) => {
        const job = jobMap[d.job_id]
        const isPortal = d.channel === 'portal'

        return (
          <div key={d.id} className="draft-card">
            <div className="draft-header">
              <div>
                {job && <strong style={{ fontSize: 16 }}>{job.title} @ {job.company}</strong>}
                <div style={{ marginTop: 4 }}>
                  <span className="badge">{d.channel?.toUpperCase()}</span>
                  {!isPortal && <span style={{ marginLeft: 8, fontSize: 13, color: '#8b92a5' }}>→ {d.recipient}</span>}
                </div>
                {d.subject && !isPortal && <div style={{ marginTop: 6, fontWeight: 600, fontSize: 14 }}>{d.subject}</div>}
              </div>
              {job?.source_url && (
                <a href={job.source_url} target="_blank" rel="noreferrer" className="btn-secondary" style={{ flexShrink: 0 }}>🔗 View Job</a>
              )}
            </div>

            {isPortal ? (
              <div className="alert-warn">🌐 Apply directly at: <a href={d.recipient} target="_blank" rel="noreferrer" style={{ color: '#b794f4' }}>{d.recipient}</a></div>
            ) : (
              <div className="draft-body">{d.body}</div>
            )}

            <div className="draft-actions">
              {isPortal ? (
                <button className="btn-primary" onClick={() => markApplied(d)}>✅ Mark as Applied</button>
              ) : (
                <button className="btn-primary" onClick={() => sendEmail(d)} disabled={sending === d.id}>
                  {sending === d.id ? '⏳ Sending...' : '✅ Approve & Send'}
                </button>
              )}
              <button className="btn-secondary" onClick={() => skip(d)}>❌ Skip</button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Resume ─────────────────────────────────────────────────────────────────────
function MyResume({ resumes, onRefresh }: any) {
  const uploadFile = useUploadFile({ client: lemmaClient })
  const createResume = useCreateRecord({ client: lemmaClient, tableName: 'resumes' })
  const updateResume = useUpdateRecord({ client: lemmaClient, tableName: 'resumes' })
  const reParseAgent = useAgentTask({ client: lemmaClient, agentName: 'resume_parser' })
  const fileRef = useRef<HTMLInputElement>(null)
  const [label, setLabel] = useState('')
  const [msg, setMsg] = useState('')

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file) return setMsg('Please select a PDF file.')
    setMsg('⏳ Uploading...')
    try {
      const uploaded = await uploadFile.upload(file, {
        name: file.name,
        directoryPath: '/resumes',
        searchEnabled: true,
      })
      if (!uploaded) throw new Error('Upload failed')
      await createResume.create({
        label: label || file.name,
        file_path: `/resumes/${file.name}`,
        status: 'raw',
      })
      setMsg('✅ Resume uploaded! It will be parsed automatically when you run a hunt.')
      onRefresh()
    } catch (e: any) {
      setMsg(`❌ Error: ${e.message}`)
    }
  }

  const reparse = async (resumeId: string) => {
    await updateResume.update({ status: 'raw' }, { recordId: resumeId })
    await reParseAgent.run({ resume_id: resumeId })
    setMsg('✅ Re-parsing started!')
    onRefresh()
  }

  return (
    <div className="page">
      <h2>📄 My Resume</h2>

      {resumes.map((r: any) => {
        const parsed = typeof r.parsed === 'object' ? r.parsed : {}
        const skills: string[] = parseJson(parsed?.skills)
        const statusIcon = r.status === 'parsed' ? '🟢' : r.status === 'parsing' ? '🟡' : '🔴'

        return (
          <div key={r.id} className="panel" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <strong>{statusIcon} {r.label || 'My Resume'}</strong>
                <span className="muted" style={{ marginLeft: 10, fontSize: 12 }}>{r.status}</span>
              </div>
              <button className="btn-secondary" style={{ fontSize: 12 }} onClick={() => reparse(r.id)}>
                🔄 Re-parse
              </button>
            </div>
            {r.status === 'parsed' && parsed?.recent_role && (
              <div style={{ marginTop: 12, fontSize: 13 }}>
                <div><strong>Role:</strong> {parsed.recent_role}</div>
                <div style={{ marginTop: 6 }}><strong>Skills ({skills.length}):</strong> {skills.slice(0, 20).join(', ')}</div>
              </div>
            )}
            {r.status === 'raw' && <p className="muted" style={{ marginTop: 8 }}>Waiting to be parsed. Click Re-parse.</p>}
          </div>
        )
      })}

      <div className="panel">
        <h3>Upload New Resume</h3>
        <p className="muted" style={{ marginBottom: 16 }}>Upload your latest PDF — we'll parse it automatically.</p>
        <input className="input" placeholder="Label (e.g. Rishi Bansal - GenAI 2026)" value={label} onChange={e => setLabel(e.target.value)} />
        <input type="file" accept=".pdf" ref={fileRef} style={{ marginBottom: 12, color: '#e2e8f0' }} />
        <button className="btn-primary" onClick={handleUpload} disabled={uploadFile.isSubmitting}>
          {uploadFile.isSubmitting ? '⏳ Uploading...' : '📤 Upload Resume'}
        </button>
        {msg && <div className="status-msg" style={{ marginTop: 12 }}>{msg}</div>}
      </div>
    </div>
  )
}

// ── Profile ────────────────────────────────────────────────────────────────────
function Profile({ profile, onSave }: any) {
  const updateProfile = useUpdateRecord({ client: lemmaClient, tableName: 'user_profiles' })
  const [form, setForm] = useState({
    name: profile?.name || '',
    roles: parseJson(profile?.target_roles).join('\n'),
    locations: parseJson(profile?.locations).join('\n'),
    experience: profile?.experience_level || 'intern',
    company_prefs: parseJson(profile?.company_prefs).join(', '),
    channels: parseJson(profile?.channels).length ? parseJson(profile.channels) : ['email'],
    telegram_bot_token: (profile?.telegram_bot_token as string) || '',
    telegram_chat_id: (profile?.telegram_chat_id as string) || '',
  })
  const [msg, setMsg] = useState('')

  const save = async () => {
    try {
      await updateProfile.update({
        name: form.name,
        target_roles: form.roles.split('\n').map(r => r.trim()).filter(Boolean),
        locations: form.locations.split('\n').map(l => l.trim()).filter(Boolean),
        experience_level: form.experience,
        company_prefs: form.company_prefs.split(',').map(c => c.trim()).filter(Boolean),
        channels: form.channels,
        telegram_bot_token: form.telegram_bot_token || '',
        telegram_chat_id: form.telegram_chat_id || '',
      }, { recordId: profile.id })
      setMsg('✅ Profile saved!')
      onSave()
    } catch (e: any) {
      setMsg(`❌ Error: ${e.message}`)
    }
  }

  return (
    <div className="page">
      <h2>👤 My Profile</h2>
      <div className="panel">
        <label className="field-label">Full name</label>
        <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />

        <label className="field-label">Target roles (one per line)</label>
        <textarea className="input" rows={4} value={form.roles} onChange={e => setForm(f => ({ ...f, roles: e.target.value }))} />

        <label className="field-label">Preferred locations (one per line)</label>
        <textarea className="input" rows={3} value={form.locations} onChange={e => setForm(f => ({ ...f, locations: e.target.value }))} />

        <label className="field-label">Experience level</label>
        <select className="input" value={form.experience} onChange={e => setForm(f => ({ ...f, experience: e.target.value }))}>
          {['intern', 'fresher', 'junior', 'mid', 'senior'].map(o => <option key={o}>{o}</option>)}
        </select>

        <label className="field-label">Company preferences (comma separated)</label>
        <input className="input" value={form.company_prefs} onChange={e => setForm(f => ({ ...f, company_prefs: e.target.value }))} />

        <label className="field-label">Outreach channels</label>
        <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
          {['email', 'linkedin'].map(ch => (
            <label key={ch} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', color: '#e2e8f0' }}>
              <input type="checkbox" checked={form.channels.includes(ch)}
                onChange={e => setForm(f => ({
                  ...f,
                  channels: e.target.checked ? [...f.channels, ch] : f.channels.filter(c => c !== ch)
                }))} />
              {ch}
            </label>
          ))}
        </div>

        <hr style={{ borderColor: '#2d3250', margin: '16px 0' }} />
        <p style={{ fontSize: 13, color: '#8b92a5', marginBottom: 12 }}>
          📱 <strong style={{ color: '#e2e8f0' }}>Telegram Notifications</strong> (optional)
        </p>
        <label className="field-label">Bot Token</label>
        <input className="input" type="password" value={form.telegram_bot_token}
          onChange={e => setForm(f => ({ ...f, telegram_bot_token: e.target.value }))}
          placeholder="8404655790:AAH..." />
        <label className="field-label">Chat ID</label>
        <input className="input" value={form.telegram_chat_id}
          onChange={e => setForm(f => ({ ...f, telegram_chat_id: e.target.value }))}
          placeholder="1622560998" />
        <p className="muted" style={{ marginBottom: 16, fontSize: 12 }}>
          Create a bot via @BotFather → get Chat ID by messaging your bot then checking getUpdates
        </p>

        <button className="btn-primary" onClick={save} disabled={updateProfile.isSubmitting}>
          {updateProfile.isSubmitting ? '⏳ Saving...' : '💾 Save Profile'}
        </button>
        {msg && <div className="status-msg" style={{ marginTop: 12 }}>{msg}</div>}
      </div>
    </div>
  )
}

// ── Main App ───────────────────────────────────────────────────────────────────
function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [refreshKey, setRefreshKey] = useState(0)
  const { user } = useCurrentUser({ client: lemmaClient })

  const jobsQ = useRecords({ client: lemmaClient, tableName: 'job_postings', limit: 500 })
  const matchesQ = useRecords({ client: lemmaClient, tableName: 'job_matches', limit: 500 })
  const draftsQ = useRecords({ client: lemmaClient, tableName: 'outreach_messages', limit: 100 })
  const resumesQ = useRecords({ client: lemmaClient, tableName: 'resumes', limit: 10 })
  const profileQ = useRecords({ client: lemmaClient, tableName: 'user_profiles', limit: 1 })

  const jobs = jobsQ.records
  const matches = matchesQ.records
  const drafts = draftsQ.records
  const resumes = resumesQ.records
  const profile = profileQ.records[0] || null

  const refresh = () => {
    setRefreshKey(k => k + 1)
    jobsQ.refresh()
    matchesQ.refresh()
    draftsQ.refresh()
    resumesQ.refresh()
    profileQ.refresh()
  }

  const pending = drafts.filter((d: any) => d.status === 'drafted')

  // Show onboarding if no profile
  if (!profileQ.isLoading && !profile) {
    return <Onboarding onCreate={() => { profileQ.refresh(); setPage('resume') }} />
  }

  if (profileQ.isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0f1117', color: '#e2e8f0' }}>
        <div>🚀 Loading Placement Pilot...</div>
      </div>
    )
  }

  return (
    <div className="app-layout">
      <Nav page={page} setPage={setPage} pendingCount={pending.length} userName={user?.email || 'User'} />
      <main className="content">
        {page === 'dashboard' && <Dashboard jobs={jobs} matches={matches} drafts={drafts} resumes={resumes} setPage={setPage} />}
        {page === 'hunt' && <HuntJobs resumes={resumes} jobs={jobs} profile={profile} />}
        {page === 'pipeline' && <Pipeline matches={matches} jobs={jobs} />}
        {page === 'approvals' && <Approvals drafts={drafts} jobs={jobs} />}
        {page === 'resume' && <MyResume resumes={resumes} onRefresh={refresh} />}
        {page === 'profile' && profile && <Profile profile={profile} onSave={refresh} />}
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthGuard
        client={lemmaClient}
        loadingFallback={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0f1117', color: '#e2e8f0' }}>
            <div>🚀 Loading Placement Pilot...</div>
          </div>
        }
      >
        <App />
      </AuthGuard>
    </QueryClientProvider>
  </React.StrictMode>,
)
