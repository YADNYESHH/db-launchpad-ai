import { useEffect, useState } from 'react'
import { listProfiles } from '../api'
import type { ProfileBundle } from '../types'

export default function Portfolio({
  onSelect,
  selectedId,
}: {
  onSelect: (startupId: string) => void
  selectedId: string | null
}) {
  const [bundles, setBundles] = useState<ProfileBundle[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listProfiles()
      .then(setBundles)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="panel">Loading portfolio…</div>

  return (
    <div className="panel portfolio">
      <h2>Portfolio</h2>
      {bundles.length === 0 && <p>No startups scored yet.</p>}
      <ul className="portfolio-list">
        {bundles.map((b) => (
          <li
            key={b.profile.startup_id}
            className={b.profile.startup_id === selectedId ? 'selected' : ''}
            onClick={() => onSelect(b.profile.startup_id)}
          >
            <div className="portfolio-item-header">
              <strong>{b.profile.name}</strong>
              {b.profile.synthetic_flag && <span className="badge synthetic">SYNTHETIC</span>}
            </div>
            <div className="portfolio-item-meta">
              {b.profile.sector} &middot; {b.profile.hq_country} &rarr;{' '}
              {b.profile.target_countries.join(', ') || 'no target markets set'}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
