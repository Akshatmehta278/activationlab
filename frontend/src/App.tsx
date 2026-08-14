import { useEffect, useState } from 'react'
import { createSession } from './api'
import Copilot from './components/Copilot'
import Dashboard from './components/Dashboard'
import Onboarding from './components/Onboarding'
import type { Session } from './types'

function getVisitorId() {
  const existing = localStorage.getItem('activationlab_visitor_id')
  if (existing) return existing
  const generated = crypto.randomUUID()
  localStorage.setItem('activationlab_visitor_id', generated)
  return generated
}

export default function App() {
  const [tab, setTab] = useState<'onboarding' | 'dashboard' | 'copilot'>('onboarding')
  const [session, setSession] = useState<Session | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const visitorId = getVisitorId()
    createSession(visitorId).then(setSession).catch((err: Error) => setError(err.message))
  }, [])

  function resetDemoUser() {
    localStorage.removeItem('activationlab_visitor_id')
    window.location.reload()
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">A</div>
          <div>
            <div className="brand-name">ActivationLab</div>
            <div className="brand-subtitle">Product onboarding + experimentation</div>
          </div>
        </div>
        <nav>
          <button className={tab === 'onboarding' ? 'nav-button active' : 'nav-button'} onClick={() => setTab('onboarding')}>Onboarding</button>
          <button className={tab === 'dashboard' ? 'nav-button active' : 'nav-button'} onClick={() => setTab('dashboard')}>Experiments</button>
          <button className={tab === 'copilot' ? 'nav-button active' : 'nav-button'} onClick={() => setTab('copilot')}>Copilot</button>
        </nav>
      </header>

      <main className="page">
        {error && <div className="error-banner">API error: {error}</div>}
        {!session ? (
          <div className="loading-card">Starting your onboarding session…</div>
        ) : tab === 'onboarding' ? (
          <Onboarding session={session} onSessionChange={setSession} onReset={resetDemoUser} />
        ) : tab === 'dashboard' ? (
          <Dashboard />
        ) : (
          <Copilot session={session} />
        )}
      </main>
    </div>
  )
}
