import { useEffect, useMemo, useState } from 'react'
import { listProfiles } from '../api'
import type { PriorityBand, ProfileBundle } from '../types'
import { PRIORITY_BAND_LABELS } from '../types'

const BAND_CLASS: Record<PriorityBand, string> = {
  high_priority: 'high',
  monitor: 'monitor',
  validate: 'validate',
  no_immediate_action: 'no-action',
}

const BAND_ORDER: PriorityBand[] = ['high_priority', 'monitor', 'validate', 'no_immediate_action']

const FILTER_CHIPS: { key: PriorityBand | 'all'; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'high_priority', label: 'High priority' },
  { key: 'monitor', label: 'Monitor' },
  { key: 'validate', label: 'Validate' },
  { key: 'no_immediate_action', label: 'No action' },
]

export default function Portfolio({
  onSelect,
  selectedId,
  refreshKey,
}: {
  onSelect: (startupId: string) => void
  selectedId: string | null
  refreshKey?: number
}) {
  const [bundles, setBundles] = useState<ProfileBundle[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeBand, setActiveBand] = useState<PriorityBand | 'all'>('all')

  useEffect(() => {
    setLoading(true)
    listProfiles()
      .then(setBundles)
      .finally(() => setLoading(false))
  }, [refreshKey])

  const ranked = useMemo(
    () =>
      [...bundles].sort(
        (a, b) => (b.score?.final_score ?? -Infinity) - (a.score?.final_score ?? -Infinity),
      ),
    [bundles],
  )

  const bandCounts = useMemo(() => {
    const counts: Record<PriorityBand, number> = {
      high_priority: 0,
      monitor: 0,
      validate: 0,
      no_immediate_action: 0,
    }
    for (const b of bundles) {
      if (b.score) counts[b.score.priority_band] += 1
    }
    return counts
  }, [bundles])

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    return ranked.filter((b) => {
      if (activeBand !== 'all' && b.score?.priority_band !== activeBand) return false
      if (!q) return true
      const haystack = `${b.profile.name} ${b.profile.sector} ${b.profile.hq_country}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [ranked, search, activeBand])

  if (loading) return <div className="panel">Loading portfolio…</div>

  return (
    <div className="panel portfolio">
      <h2>Portfolio</h2>

      <div className="portfolio-summary">
        {BAND_ORDER.map((band) => (
          <span key={band} className={`portfolio-summary-cell ${BAND_CLASS[band]}`}>
            <strong>{bandCounts[band]}</strong> {PRIORITY_BAND_LABELS[band]}
          </span>
        ))}
        <span className="portfolio-summary-total">{bundles.length} total</span>
      </div>

      <input
        className="portfolio-search"
        type="search"
        placeholder="Search name, sector, country…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="portfolio-filters">
        {FILTER_CHIPS.map((chip) => (
          <button
            key={chip.key}
            type="button"
            className={`portfolio-chip${activeBand === chip.key ? ' active' : ''}`}
            onClick={() => setActiveBand(chip.key)}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {bundles.length === 0 && <p>No startups scored yet.</p>}
      {bundles.length > 0 && visible.length === 0 && (
        <p className="portfolio-empty">No startups match your filters.</p>
      )}

      <ul className="portfolio-list">
        {visible.map((b) => {
          const score = b.score
          return (
            <li
              key={b.profile.startup_id}
              className={b.profile.startup_id === selectedId ? 'selected' : ''}
              onClick={() => onSelect(b.profile.startup_id)}
            >
              <div className="portfolio-item-header">
                <span className="portfolio-item-title">
                  <strong>{b.profile.name}</strong>
                  {b.profile.synthetic_flag && <span className="badge synthetic">SYNTHETIC</span>}
                </span>
                {score ? (
                  <span className={`score-badge ${BAND_CLASS[score.priority_band]}`}>
                    {Math.round(score.final_score)}
                  </span>
                ) : (
                  <span className="score-badge unscored">—</span>
                )}
              </div>
              <div className="portfolio-item-meta">
                {b.profile.sector} &middot; {b.profile.hq_country} &rarr;{' '}
                {b.profile.target_countries.join(', ') || 'no target markets set'}
              </div>
              {score ? (
                <span className={`band-pill ${BAND_CLASS[score.priority_band]}`}>
                  {PRIORITY_BAND_LABELS[score.priority_band]}
                </span>
              ) : (
                <span className="band-pill unscored">Unscored</span>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
