import { useEffect, useState, type ReactNode } from 'react'
import { getMetrics } from '../api'
import type { Metrics } from '../types'

function StatPill({ ok, children }: { ok: boolean; children: ReactNode }) {
  return <span className={ok ? 'stat-pill good' : 'stat-pill neutral'}>{children}</span>
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [error, setError] = useState('')

  function refresh() {
    setError('')
    getMetrics().then(setMetrics).catch((err: Error) => setError(err.message))
  }

  useEffect(() => { refresh() }, [])

  if (error) return <div className="error-banner">Could not load metrics: {error}</div>
  if (!metrics) return <div className="loading-card">Loading experiment metrics…</div>

  const control = metrics.variants.find((v) => v.variant === 'control')
  const guided = metrics.variants.find((v) => v.variant === 'guided')

  return (
    <div className="dashboard-layout">
      <section className="dashboard-heading">
        <div><div className="eyebrow">EXPERIMENT ANALYTICS</div><h1>Activation dashboard</h1><p>Compare variants, inspect funnel leakage, and check whether the observed uplift is statistically credible.</p></div>
        <button className="secondary-button" onClick={refresh}>Refresh metrics</button>
      </section>

      <section className="metric-grid">
        <div className="metric-card"><span>Total sessions</span><strong>{metrics.sessions}</strong></div>
        <div className="metric-card"><span>Activated users</span><strong>{metrics.activated}</strong></div>
        <div className="metric-card"><span>Activation rate</span><strong>{metrics.activation_rate}%</strong></div>
        <div className="metric-card"><span>Avg. time to value</span><strong>{metrics.average_time_to_activation_minutes}m</strong></div>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-heading"><div><div className="eyebrow">A/B TEST</div><h2>Variant performance</h2></div></div>
          <div className="variant-table">
            {metrics.variants.map((variant) => <div className="variant-row" key={variant.variant}><div><strong>{variant.label}</strong><span>{variant.sessions} sessions · {variant.activated} activated</span></div><div className="rate-number">{variant.activation_rate}%</div></div>)}
          </div>
          <div className="experiment-callout">
            <div><span>Guided − Control</span><strong>{metrics.experiment.difference_pp > 0 ? '+' : ''}{metrics.experiment.difference_pp} pp</strong></div>
            <div><span>Relative uplift</span><strong>{metrics.experiment.relative_uplift_percent > 0 ? '+' : ''}{metrics.experiment.relative_uplift_percent}%</strong></div>
            <div><span>p-value</span><strong>{metrics.experiment.p_value}</strong></div>
          </div>
          <div className="pill-row">
            <StatPill ok={metrics.experiment.significant_at_95}>{metrics.experiment.significant_at_95 ? '95% significance reached' : 'Needs more evidence'}</StatPill>
            <StatPill ok={!metrics.experiment.sample_ratio_mismatch.flagged}>{metrics.experiment.sample_ratio_mismatch.flagged ? 'Sample ratio warning' : 'Sample ratio healthy'}</StatPill>
          </div>
          <p className="panel-note">95% CI for difference: {metrics.experiment.ci_95_difference_pp[0]} to {metrics.experiment.ci_95_difference_pp[1]} percentage points.</p>
        </article>

        <article className="panel">
          <div className="panel-heading"><div><div className="eyebrow">FUNNEL</div><h2>Step conversion</h2></div></div>
          <div className="funnel-list">
            {metrics.funnel.map((item) => <div className="funnel-item" key={item.step}><div className="funnel-label"><span>{item.label}</span><strong>{item.rate}%</strong></div><div className="mini-track"><div style={{ width: `${item.rate}%` }} /></div><small>{item.count} users · A {item.by_variant.control.rate}% · B {item.by_variant.guided.rate}%</small></div>)}
          </div>
        </article>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <div className="panel-heading"><div><div className="eyebrow">EVENT PIPELINE</div><h2>Instrumented events</h2></div></div>
          <div className="event-grid">
            {Object.entries(metrics.event_counts).map(([name, count]) => <div className="event-chip" key={name}><code>{name}</code><strong>{count}</strong></div>)}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading"><div><div className="eyebrow">DATA OPERATIONS</div><h2>Customer imports</h2></div></div>
          <div className="import-summary">
            {Object.entries(metrics.import_summary).length ? Object.entries(metrics.import_summary).map(([name, count]) => <div key={name}><span>{name}</span><strong>{count}</strong></div>) : <p>No persisted import jobs yet. Seeded demo data intentionally does not fake import jobs.</p>}
          </div>
          <p className="panel-note">Control: {control?.sessions ?? 0} users. Guided: {guided?.sessions ?? 0} users. The seeded dataset is demonstration data, not a claim of real-world uplift.</p>
        </article>
      </section>
    </div>
  )
}
