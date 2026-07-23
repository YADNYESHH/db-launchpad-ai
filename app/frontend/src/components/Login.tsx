import { useState } from 'react'
import { login, setToken } from '../api'
import type { UserPublic } from '../types'

export default function Login({ onLogin }: { onLogin: (user: UserPublic) => void }) {
  const [email, setEmail] = useState('anna.schmidt@launchpad.demo')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await login(email, password)
      setToken(result.access_token)
      onLogin(result.user)
    } catch {
      setError('Login failed. Check email/password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>LaunchPad AI</h1>
        <p className="subtitle">RM decision-support demo &mdash; synthetic data only</p>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <select value={email} onChange={(e) => setEmail(e.target.value)}>
              <option value="anna.schmidt@launchpad.demo">Anna Schmidt (Relationship Manager)</option>
              <option value="priya.nair@launchpad.demo">Priya Nair (Product Owner)</option>
              <option value="wei.chen@launchpad.demo">Wei Chen (Control Reviewer)</option>
              <option value="admin@launchpad.demo">Admin User (Admin)</option>
            </select>
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="error-banner">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="hint">Demo password for every seeded user: demo1234</p>
      </div>
    </div>
  )
}
