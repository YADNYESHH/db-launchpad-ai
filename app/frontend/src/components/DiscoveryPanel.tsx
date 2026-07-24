import { useState } from 'react'
import { discoverStartups, ApiError } from '../api'
import type { DiscoveredItem, DiscoveryResponse, PriorityBand } from '../types'
import { PRIORITY_BAND_LABELS } from '../types'
import './DiscoveryPanel.css'

const BAND_CLASS: Record<PriorityBand, string> = {
  high_priority: 'disc-band-high',
  monitor: 'disc-band-monitor',
  validate: 'disc-band-validate',
  no_immediate_action: 'disc-band-none',
}

const LIMIT_OPTIONS = [2, 3, 4, 5, 6]

// A discovered item counts as "new" unless its status marks it as already
// tracked. The backend uses statuses like "discovered" / "already_known";
// we infer defensively from the string so unexpected values still render.
function isAlreadyTracked(status: string): boolean {
  const s = status.toLowerCase()
  return s.includes('known') || s.includes('tracked') || s.includes('existing')
}

export default function DiscoveryPanel(props: { onDiscovered?: () => void }) {
  const [sector, setSector] = useState('')
  const [limit, setLimit] = useState(4)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DiscoveryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const trimmed = sector.trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await discoverStartups(trimmed, limit)
      setResult(response)
      props.onDiscovered?.()
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError('Live discovery is available to Relationship Managers and Product Owners.')
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Live discovery failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const unavailable =
    result !== null && result.discovered.length === 0 && result.reason !== null

  return (
    <div className="disc-panel">
      <h2 className="disc-heading">Live opportunity discovery</h2>
      <p className="disc-subhead">
        Search public sources for real startups in a sector and score them live.
      </p>

      <form className="disc-form" onSubmit={handleSubmit}>
        <input
          className="disc-input"
          type="text"
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          placeholder="e.g. cross-border B2B payments"
          disabled={loading}
          aria-label="Sector to discover"
        />
        <label className="disc-limit">
          <span className="disc-limit-label">Results</span>
          <select
            className="disc-select"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            disabled={loading}
            aria-label="Number of results"
          >
            {LIMIT_OPTIONS.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <button className="disc-button" type="submit" disabled={loading || !sector.trim()}>
          {loading ? 'Searching…' : 'Discover'}
        </button>
      </form>

      {loading && (
        <div className="disc-loading" role="status">
          <span className="disc-spinner" aria-hidden="true" />
          <span>Searching live sources…</span>
        </div>
      )}

      {error && !loading && (
        <div className="disc-banner disc-banner-error" role="alert">
          {error}
        </div>
      )}

      {unavailable && !loading && (
        <div className="disc-banner disc-banner-info" role="status">
          Live discovery is currently unavailable — {result?.reason}. Showing no new results.
        </div>
      )}

      {result !== null && !unavailable && !loading && (
        <div className="disc-results">
          {result.discovered.map((item) => (
            <DiscoveryCard key={item.startup_id} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

function DiscoveryCard({ item }: { item: DiscoveredItem }) {
  const tracked = isAlreadyTracked(item.status)
  const band = item.priority_band ?? null

  return (
    <div className="disc-card">
      <div className="disc-card-head">
        <span className="disc-card-name">{item.name}</span>
        <span
          className={`disc-status ${tracked ? 'disc-status-tracked' : 'disc-status-new'}`}
        >
          {tracked ? 'Already tracked' : 'New'}
        </span>
      </div>

      <div className="disc-card-meta">
        {typeof item.final_score === 'number' && (
          <span className="disc-score">{Math.round(item.final_score)}</span>
        )}
        {band && (
          <span className={`disc-band ${BAND_CLASS[band]}`}>{PRIORITY_BAND_LABELS[band]}</span>
        )}
      </div>

      {item.note && <p className="disc-note">{item.note}</p>}

      {item.corroboration_notes && item.corroboration_notes.length > 0 && (
        <ul className="disc-corroboration">
          {item.corroboration_notes.map((note, idx) => (
            <li key={idx} className="disc-caption">
              {note}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
