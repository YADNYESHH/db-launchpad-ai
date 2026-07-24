import { useCallback, useEffect, useState } from 'react'
import { getPortfolioSummary, getToken, listProfiles, me, setToken } from './api'
import type { PortfolioSummary, ProfileBundle, UserPublic } from './types'
import Login from './components/Login'
import Portfolio from './components/Portfolio'
import StartupDetail from './components/StartupDetail'
import DiscoveryPanel from './components/DiscoveryPanel'
import CompareView from './components/CompareView'
import WeightsAdmin from './components/WeightsAdmin'
import { formatEur } from './format'
import {
  AppHeader,
  DecisionBandLegend,
  PolicyChips,
  PrinciplesFooter,
  StatTiles,
} from './components/DashboardChrome'
import './theme.css'
import './App.css'

type View = 'portfolio' | 'discovery' | 'compare' | 'weights'

const NAV: { key: View; label: string }[] = [
  { key: 'portfolio', label: 'Portfolio' },
  { key: 'discovery', label: 'Live discovery' },
  { key: 'compare', label: 'Compare' },
  { key: 'weights', label: 'Weights governance' },
]

function App() {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [view, setView] = useState<View>('portfolio')
  const [bundles, setBundles] = useState<ProfileBundle[]>([])
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

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

        {view === 'discovery' && (
          <div className="panel">
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
      </main>

      <PrinciplesFooter />
    </div>
  )
}

export default App
