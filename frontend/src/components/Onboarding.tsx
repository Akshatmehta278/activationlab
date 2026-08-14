import { useRef, useState } from 'react'
import {
  connectIntegration,
  createCampaign,
  getImportStatus,
  getSession,
  updateProfile,
  uploadCustomerCsv,
} from '../api'
import type { ImportJob, Session, StepKey } from '../types'

interface Props {
  session: Session
  onSessionChange: (session: Session) => void
  onReset: () => void
}

const steps: Array<{ key: StepKey; number: string; title: string; description: string }> = [
  { key: 'workspace_created', number: '01', title: 'Create your workspace', description: 'Give the product business context so the activation journey can adapt.' },
  { key: 'integration_connected', number: '02', title: 'Connect a data source', description: 'Attach a demo commerce source and record the integration event.' },
  { key: 'data_imported', number: '03', title: 'Import customer data', description: 'Upload a real CSV. The backend validates, stores, and instruments the import.' },
  { key: 'campaign_created', number: '04', title: 'Create first-value output', description: 'Create a welcome campaign draft to complete the activation path.' },
]

function demoCsvFile() {
  const csv = [
    'customer_id,email,first_name,last_name,lifetime_value,subscribed,tags',
    'demo-1,ava@example.com,Ava,Shah,420.50,true,vip;repeat',
    'demo-2,noah@example.com,Noah,Kim,88.00,true,new',
    'demo-3,mia@example.com,Mia,Garcia,215.75,true,repeat',
    'demo-4,liam@example.com,Liam,Brown,32.10,false,winback',
    'demo-5,emma@example.com,Emma,Wilson,640.00,true,vip;high-value',
  ].join('\n')
  return new File([csv], 'activationlab-demo-customers.csv', { type: 'text/csv' })
}

export default function Onboarding({ session, onSessionChange, onReset }: Props) {
  const [companyName, setCompanyName] = useState(session.company_name || 'Northstar Commerce')
  const [businessType, setBusinessType] = useState(session.business_type || 'Ecommerce')
  const [provider, setProvider] = useState('shopify-demo')
  const [campaignName, setCampaignName] = useState('Welcome Series')
  const [busyStep, setBusyStep] = useState<StepKey | null>(null)
  const [importJob, setImportJob] = useState<ImportJob | null>(null)
  const [error, setError] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)
  const isGuided = session.variant === 'guided'

  const firstIncomplete = steps.findIndex((step) => !session.completed_steps.includes(step.key))

  async function saveWorkspace() {
    if (!companyName.trim()) return setError('Enter a company name.')
    setBusyStep('workspace_created')
    setError('')
    try {
      onSessionChange(await updateProfile(session.visitor_id, companyName.trim(), businessType))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create workspace.')
    } finally {
      setBusyStep(null)
    }
  }

  async function saveIntegration() {
    setBusyStep('integration_connected')
    setError('')
    try {
      onSessionChange(await connectIntegration(session.visitor_id, provider))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not connect integration.')
    } finally {
      setBusyStep(null)
    }
  }

  async function upload(file: File) {
    setBusyStep('data_imported')
    setError('')
    try {
      let job = await uploadCustomerCsv(session.visitor_id, file)
      setImportJob(job)
      for (let attempt = 0; attempt < 30 && (job.status === 'pending' || job.status === 'processing'); attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        job = await getImportStatus(session.visitor_id, job.id)
        setImportJob(job)
      }
      if (job.status === 'failed') throw new Error(job.error_message || 'Import failed.')
      if (job.status !== 'completed') throw new Error('Import is still processing. Check again in a moment.')
      onSessionChange(await getSession(session.visitor_id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not import customers.')
    } finally {
      setBusyStep(null)
    }
  }

  async function saveCampaign() {
    if (!campaignName.trim()) return setError('Enter a campaign name.')
    setBusyStep('campaign_created')
    setError('')
    try {
      onSessionChange(await createCampaign(session.visitor_id, campaignName.trim()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create campaign.')
    } finally {
      setBusyStep(null)
    }
  }

  function locked(key: StepKey) {
    if (!isGuided) return false
    const index = steps.findIndex((step) => step.key === key)
    return firstIncomplete >= 0 && index > firstIncomplete && !session.completed_steps.includes(key)
  }

  return (
    <div className="onboarding-layout">
      <section className="hero-card">
        <div className="eyebrow">LIVE ACTIVATION EXPERIMENT</div>
        <div className="hero-row">
          <div>
            <h1>{session.is_activated ? 'First value reached.' : 'Turn setup into measurable activation.'}</h1>
            <p>Every meaningful action becomes an event, every visitor gets a stable experiment variant, and every funnel step is measurable.</p>
          </div>
          <div className={`variant-badge ${session.variant}`}>
            <span>Assigned experience</span>
            <strong>{isGuided ? 'B · Guided' : 'A · Control'}</strong>
          </div>
        </div>
        {isGuided && <div className="guided-tip"><strong>Guided variant:</strong> steps unlock in sequence, progress is explicit, and contextual help reduces decision load.</div>}
        <div className="progress-header"><span>Activation progress</span><strong>{session.progress_percent}%</strong></div>
        <div className="progress-track"><div className="progress-fill" style={{ width: `${session.progress_percent}%` }} /></div>
        <div className="session-facts">
          <span><strong>{session.customer_count}</strong> customers</span>
          <span><strong>{session.campaign_count}</strong> campaign drafts</span>
          <span><strong>{session.integration?.provider ?? 'No integration'}</strong></span>
        </div>
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="steps-grid">
        <article className={session.completed_steps.includes('workspace_created') ? 'step-card complete' : 'step-card'}>
          <div className="step-topline"><span className="step-number">01</span><span className={session.completed_steps.includes('workspace_created') ? 'status-pill done' : 'status-pill'}>{session.completed_steps.includes('workspace_created') ? 'Completed' : 'Ready'}</span></div>
          <h2>Create your workspace</h2><p>{steps[0].description}</p>
          {!session.completed_steps.includes('workspace_created') && <div className="form-stack"><label>Company name<input value={companyName} onChange={(e) => setCompanyName(e.target.value)} /></label><label>Business type<select value={businessType} onChange={(e) => setBusinessType(e.target.value)}><option>Ecommerce</option><option>SaaS</option><option>Marketplace</option><option>Creator</option></select></label></div>}
          <button className="primary-button" disabled={session.completed_steps.includes('workspace_created') || busyStep !== null} onClick={saveWorkspace}>{session.completed_steps.includes('workspace_created') ? 'Completed ✓' : busyStep === 'workspace_created' ? 'Saving…' : 'Create workspace'}</button>
        </article>

        <article className={session.completed_steps.includes('integration_connected') ? 'step-card complete' : 'step-card'}>
          <div className="step-topline"><span className="step-number">02</span><span className={session.completed_steps.includes('integration_connected') ? 'status-pill done' : 'status-pill'}>{session.completed_steps.includes('integration_connected') ? 'Completed' : locked('integration_connected') ? 'Locked' : 'Ready'}</span></div>
          <h2>Connect a data source</h2><p>{steps[1].description}</p>
          {!session.completed_steps.includes('integration_connected') && <label className="single-field">Demo provider<select value={provider} onChange={(e) => setProvider(e.target.value)}><option value="shopify-demo">Shopify demo</option><option value="custom-api">Custom API</option><option value="stripe-demo">Stripe demo</option></select></label>}
          <button className="primary-button" disabled={session.completed_steps.includes('integration_connected') || locked('integration_connected') || busyStep !== null} onClick={saveIntegration}>{session.completed_steps.includes('integration_connected') ? 'Completed ✓' : busyStep === 'integration_connected' ? 'Connecting…' : 'Connect integration'}</button>
        </article>

        <article className={session.completed_steps.includes('data_imported') ? 'step-card complete' : 'step-card'}>
          <div className="step-topline"><span className="step-number">03</span><span className={session.completed_steps.includes('data_imported') ? 'status-pill done' : 'status-pill'}>{session.completed_steps.includes('data_imported') ? 'Completed' : locked('data_imported') ? 'Locked' : 'Ready'}</span></div>
          <h2>Import customer data</h2><p>{steps[2].description}</p>
          {importJob && <div className={`import-status ${importJob.status}`}><strong>{importJob.status}</strong><span>{importJob.imported_rows} imported · {importJob.failed_rows} failed</span></div>}
          <input ref={fileInput} hidden type="file" accept=".csv,text/csv" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          <div className="button-stack">
            <button className="primary-button" disabled={session.completed_steps.includes('data_imported') || locked('data_imported') || busyStep !== null} onClick={() => fileInput.current?.click()}>{session.completed_steps.includes('data_imported') ? 'Completed ✓' : busyStep === 'data_imported' ? 'Processing CSV…' : 'Upload customer CSV'}</button>
            {!session.completed_steps.includes('data_imported') && <button className="secondary-button full" disabled={locked('data_imported') || busyStep !== null} onClick={() => upload(demoCsvFile())}>Use built-in demo CSV</button>}
          </div>
        </article>

        <article className={session.completed_steps.includes('campaign_created') ? 'step-card complete' : 'step-card'}>
          <div className="step-topline"><span className="step-number">04</span><span className={session.completed_steps.includes('campaign_created') ? 'status-pill done' : 'status-pill'}>{session.completed_steps.includes('campaign_created') ? 'Completed' : locked('campaign_created') ? 'Locked' : 'Ready'}</span></div>
          <h2>Create first-value output</h2><p>{steps[3].description}</p>
          {!session.completed_steps.includes('campaign_created') && <label className="single-field">Campaign name<input value={campaignName} onChange={(e) => setCampaignName(e.target.value)} /></label>}
          <button className="primary-button" disabled={session.completed_steps.includes('campaign_created') || locked('campaign_created') || busyStep !== null} onClick={saveCampaign}>{session.completed_steps.includes('campaign_created') ? 'Completed ✓' : busyStep === 'campaign_created' ? 'Creating…' : 'Create welcome draft'}</button>
        </article>
      </section>

      <section className="explain-card">
        <div><div className="eyebrow">UNDER THE HOOD</div><h2>One action, several product signals</h2></div>
        <div className="event-flow"><span>React action</span><b>→</b><span>Django API</span><b>→</b><span>Domain model</span><b>→</b><span>ProductEvent</span><b>→</b><span>Experiment metric</span></div>
        <button className="text-button" onClick={onReset}>New experiment visitor</button>
      </section>
    </div>
  )
}
