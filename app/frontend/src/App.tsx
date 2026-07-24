import { useCallback, useEffect, useState } from 'react'
import { getPortfolioSummary, getToken, listProfiles, me, seedLivePortfolio, setToken } from './api'
import type { SeedPortfolioResult } from './api'
import type { PortfolioSummary, ProfileBundle, UserPublic } from './types'
import Login from './components/Login'
import Portfolio from './components/Portfolio'
import StartupDetail from './components/StartupDetail'
import DiscoveryPanel from './components/DiscoveryPanel'
import CompareView from './components/CompareView'
import WeightsAdmin from './components/WeightsAdmin'
import ExecutiveView from './components/ExecutiveView'
import ResponsibleAIPanel from './components/ResponsibleAIPanel'
import { formatEur } from './format'
import {
  AppHeader,
  ApplicationFlow,
  DecisionBandLegend,
  InfoBar,
  PolicyChips,
  PrinciplesFooter,
  StatTiles,
} from './components/DashboardChrome'
import './theme.css'
import './App.css'

type View = 'portfolio' | 'executive' | 'discovery' | 'compare' | 'weights' | 'responsible'

const NAV: { key: View; label: string }[] = [
  { key: 'portfolio', label: 'Portfolio' },
  { key: 'executive', label: 'Executive' },
  { key: 'discovery', label: 'Live discovery' },
  { key: 'compare', label: 'Compare' },
  { key: 'weights', label: 'Weights governance' },
  { key: 'responsible', label: 'Responsible AI' },
]

function App() {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [view, setView] = useState<View>('portfolio')
  const [bundles, setBundles] = useState<ProfileBundle[]>([])
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [seeding, setSeeding] = useState(false)
  const [seedResult, setSeedResult] = useState<SeedPortfolioResult | null>(null)
  const [seedError, setSeedError] = useState<string | null>(null)

  useEffect(() => {
    if (!getToken()) {
      setCheckingSession(false)
      return
    }
    me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setCheckingSession(false))
  }, [])

  useEffect(() => {
    if (!user) return
    listProfiles()
      .then(setBundles)
      .catch(() => setBundles([]))
    getPortfolioSummary()
      .then(setSummary)
      .catch(() => setSummary(null))
  }, [user, refreshKey])

  const handleRefresh = useCallback(() => setRefreshKey((k) => k + 1), [])

  const handleSeedLive = useCallback(async () => {
    setSeeding(true)
    setSeedError(null)
    setSeedResult(null)
    try {
      const result = await seedLivePortfolio()
      setSeedResult(result)
      setRefreshKey((k) => k + 1)
    } catch {
      setSeedError('Live portfolio population is unavailable right now. The existing portfolio is unchanged.')
    } finally {
      setSeeding(false)
    }
  }, [])

  function handleLogout() {
    setToken(null)
    setUser(null)
    setSelectedId(null)
    setView('portfolio')
  }

  if (checkingSession) return <div className="loading-screen">Loading…</div>
  if (!user) return <Login onLogin={setUser} />

  const highCount = summary?.band_counts?.['high_priority'] ?? 0
  const tiles = [
    {
      label: 'Portfolio pipeline value',
      value: summary ? formatEur(summary.total_pipeline_value_eur) : '—',
      hint: 'indicative annual bank revenue',
    },
    { label: 'High-priority opportunities', value: String(highCount), hint: 'act-now targets' },
    {
      label: 'Assessed',
      value: summary ? `${summary.scored_count}/${summary.total_count}` : '—',
      hint: 'startups scored',
    },
    { label: 'Governance', value: 'Human-in-the-loop', hint: 'every step audit-logged' },
  ]

  return (
    <div className="app-shell">
      <AppHeader user={user} onLogout={handleLogout} />

      <InfoBar />

      <div className="app-toolbar">
        <nav className="view-nav">
          {NAV.map((n) => (
            <button
              key={n.key}
              type="button"
              className={`view-nav-btn${view === n.key ? ' active' : ''}`}
              onClick={() => setView(n.key)}
            >
              {n.label}
            </button>
          ))}
        </nav>
        <PolicyChips />
      </div>

      <ApplicationFlow />

      <StatTiles tiles={tiles} />

      <main className="main-content">
        {view === 'portfolio' && (
          <div className="main-layout">
            <div className="portfolio-column">
              <Portfolio onSelect={setSelectedId} selectedId={selectedId} refreshKey={refreshKey} />
              <DecisionBandLegend />
            </div>
            {selectedId ? (
              <StartupDetail startupId={selectedId} role={user.role} />
            ) : (
              <div className="panel empty-state">Select a startup from the portfolio to begin.</div>
            )}
          </div>
        )}

        {view === 'executive' && (
          <div className="panel">
            <ExecutiveView
              onSelect={(id) => {
                setSelectedId(id)
                setView('portfolio')
              }}
            />
          </div>
        )}

        {view === 'discovery' && (
          <div className="panel">
            <div className="live-populate">
              <div className="live-populate-copy">
                <h3>Populate a live portfolio</h3>
                <p>
                  Discover real companies across cross-border payments, fintech, e-commerce,
                  logistics and health sectors via grounded web search. Results are flagged
                  live-grounded with source citations; if live discovery is unavailable the
                  existing portfolio stays intact.
                </p>
              </div>
              <button type="button" onClick={handleSeedLive} disabled={seeding}>
                {seeding ? 'Populating live data…' : 'Populate live portfolio'}
              </button>
            </div>
            {seedResult && (
              <div className={`live-populate-status${seedResult.live ? ' ok' : ''}`}>
                {seedResult.live
                  ? `Added ${seedResult.added} live companies across ${seedResult.sectors.length} sectors. Portfolio now has ${seedResult.total_profiles} startups.`
                  : 'No live companies were added (live discovery unavailable). The existing portfolio is unchanged.'}
                {seedResult.reasons.length > 0 && (
                  <ul className="live-populate-reasons">
                    {seedResult.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
            {seedError && <div className="error-banner">{seedError}</div>}
            <DiscoveryPanel onDiscovered={handleRefresh} />
          </div>
        )}

        {view === 'compare' && (
          <div className="panel">
            <CompareView bundles={bundles} />
          </div>
        )}

        {view === 'weights' && (
          <div className="panel">
            <WeightsAdmin role={user.role} />
          </div>
        )}

        {view === 'responsible' && (
          <div className="panel">
            <ResponsibleAIPanel />
          </div>
        )}
      </main>

      <PrinciplesFooter />
    </div>
  )
}

export default App
