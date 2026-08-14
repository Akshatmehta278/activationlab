import { useState } from 'react'
import { getCopilot } from '../api'
import type { CopilotResponse, Session } from '../types'

export default function Copilot({ session }: { session: Session }) {
  const [goal, setGoal] = useState('Help a new merchant reach first value with the fewest safe steps.')
  const [result, setResult] = useState<CopilotResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function run() {
    setBusy(true); setError('')
    try { setResult(await getCopilot(session.visitor_id, goal)) }
    catch (err) { setError(err instanceof Error ? err.message : 'Copilot failed.') }
    finally { setBusy(false) }
  }

  return (
    <div className="copilot-layout">
      <section className="dashboard-heading"><div><div className="eyebrow">HUMAN-IN-THE-LOOP ASSISTANCE</div><h1>Onboarding copilot</h1><p>The default provider is a deterministic rules engine. If a server-side OpenAI key is configured, the same endpoint can generate recommendations with an LLM while keeping actions advisory-only.</p></div></section>
      {error && <div className="error-banner">{error}</div>}
      <section className="panel copilot-panel">
        <label>Your onboarding goal<textarea value={goal} onChange={(e) => setGoal(e.target.value)} rows={4} /></label>
        <div className="copilot-constraints"><span>No secrets requested</span><span>No automatic sends</span><span>No destructive actions</span><span>Server-side API key only</span></div>
        <button className="primary-button" onClick={run} disabled={busy}>{busy ? 'Generating…' : 'Generate safe recommendations'}</button>
      </section>
      {result && <section className="recommendation-grid">
        {result.recommendations.map((rec, index) => <article className="recommendation-card" key={`${rec.title}-${index}`}><div className="rec-top"><span>0{index + 1}</span><span className="risk-badge">{rec.risk} risk</span></div><h2>{rec.title}</h2><p>{rec.reason}</p><code>{rec.action}</code></article>)}
        <div className="provider-note">Provider used: <strong>{result.provider}</strong></div>
      </section>}
    </div>
  )
}
