import { useEffect, useState } from 'react'
import { getToken, me, setToken } from './api'
import type { UserPublic } from './types'
import Login from './components/Login'
import Portfolio from './components/Portfolio'
import StartupDetail from './components/StartupDetail'
import './App.css'

function App() {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)

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

  function handleLogout() {
    setToken(null)
    setUser(null)
    setSelectedId(null)
  }

  if (checkingSession) return <div className="loading-screen">Loading…</div>
  if (!user) return <Login onLogin={setUser} />

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand">LaunchPad AI</div>
        <div className="user-info">
          <span>
            {user.name} &middot; {user.role.replace(/_/g, ' ')}
          </span>
          <button onClick={handleLogout} className="secondary">
            Sign out
          </button>
        </div>
      </header>
      <main className="main-layout">
        <Portfolio onSelect={setSelectedId} selectedId={selectedId} />
        {selectedId ? (
          <StartupDetail startupId={selectedId} role={user.role} />
        ) : (
          <div className="panel empty-state">Select a startup from the portfolio to begin.</div>
        )}
      </main>
    </div>
  )
}

export default App
