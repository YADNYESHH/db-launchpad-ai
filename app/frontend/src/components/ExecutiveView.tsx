import { useEffect, useState } from 'react'
import { getGovernanceMetrics, listProfiles, ApiError } from '../api'
import type { GovernanceMetrics, ProfileBundle, PriorityBand } from '../types'
import { PRIORITY_BAND_LABELS } from '../types'
import { formatEur } from '../format'
import './ExecutiveView.css'

const BAND_ORDER: PriorityBand[] = ['high_priority', 'monitor', 'validate', 'no_immediate_action']

const BAND_TOKENS: Record<PriorityBand, { color: string; bg: string }> = {
  high_priority: { color: 'var(--lp-band-high)', bg: 'var(--lp-band-high-bg)' },
  monitor: { color: 'var(--lp-band-monitor)', bg: 'var(--lp-band-monitor-bg)' },
  validate: { color: 'var(--lp-band-validate)', bg: 'var(--lp-band-validate-bg)' },
  no_immediate_action: { color: 'var(--lp-band-none)', bg: 'var(--lp-band-none-bg)' },
}

function bandCount(metrics: GovernanceMetrics, band: PriorityBand): number {
  return metrics.band_counts[band] ?? 0
}

export default function ExecutiveView(props: { onSelect?: (startupId: string) => void }) {
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null)
  const [bundles, setBundles] = useState<ProfileBundle[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    Promise.all([getGovernanceMetrics(), listProfiles()])
      .then(([m, b]) => {
        if (!active) return
        setMetrics(m)
        setBundles(b)
      })
      .catch((err) => {
        if (!active) return
        if (err instanceof ApiError) setError(`${err.message} (${err.status})`)
        else setError('Unable to load executive portfolio.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  if (loading) {
    return (
      <div className="exec-root">
        <div className="exec-state">Loading executive portfolio…</div>
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="exec-root">
        <div className="exec-state exec-state-error">{error ?? 'No data available.'}</div>
      </div>
    )
  }

  const totalBands = BAND_ORDER.reduce((sum, band) => sum + bandCount(metrics, band), 0)
  const highCount = bandCount(metrics, 'high_priority')

  const topOpportunities = [...bundles]
    .filter((b) => b.score != null)
    .sort((a, b) => (b.score?.final_score ?? 0) - (a.score?.final_score ?? 0))
    .slice(0, 6)

  return (
    <div className="exec-root">
      {/* 1. Hero KPI band */}
      <section className="exec-hero">
        <div className="exec-hero-inner">
          <span className="exec-hero-eyebrow">Portfolio opportunity intelligence</span>
          <div className="exec-hero-value">{formatEur(metrics.total_pipeline_value_eur)}</div>
          <p className="exec-hero-caption">Indicative annual portfolio revenue at stake</p>
        </div>
      </section>

      {/* 2. KPI tiles */}
      <section className="exec-tiles">
        <div className="exec-tile">
          <span className="exec-tile-label">Total companies</span>
          <span className="exec-tile-value">{metrics.total_profiles}</span>
        </div>
        <div className="exec-tile">
          <span className="exec-tile-label">Assessed</span>
          <span className="exec-tile-value">
            {metrics.scored_profiles}
            <span className="exec-tile-sub">/ {metrics.total_profiles}</span>
          </span>
        </div>
        <div className="exec-tile">
          <span className="exec-tile-label">High-priority</span>
          <span className="exec-tile-value">{highCount}</span>
        </div>
        <div className="exec-tile">
          <span className="exec-tile-label">Live-sourced</span>
          <span className="exec-tile-value">{metrics.provenance.live_grounded}</span>
          <span className="exec-tile-caption">real companies via grounded discovery</span>
        </div>
      </section>

      {/* 3. Decision-band distribution */}
      <section className="exec-panel">
        <h3 className="exec-panel-title">Decision-band distribution</h3>
        <div className="exec-bandbar" role="img" aria-label="Decision-band distribution">
          {BAND_ORDER.map((band) => {
            const count = bandCount(metrics, band)
            const pct = totalBands > 0 ? (count / totalBands) * 100 : 0
            if (count === 0) return null
            return (
              <div
                key={band}
                className="exec-bandbar-seg"
                style={{ width: `${pct}%`, background: BAND_TOKENS[band].color }}
                title={`${PRIORITY_BAND_LABELS[band]}: ${count}`}
              >
                {pct >= 8 ? count : ''}
              </div>
            )
          })}
        </div>
        <div className="exec-bandlegend">
          {BAND_ORDER.map((band) => (
            <div key={band} className="exec-bandlegend-item">
              <span className="exec-bandlegend-dot" style={{ background: BAND_TOKENS[band].color }} />
              <span className="exec-bandlegend-label">{PRIORITY_BAND_LABELS[band]}</span>
              <span className="exec-bandlegend-count">{bandCount(metrics, band)}</span>
            </div>
          ))}
        </div>
      </section>

      {/* 4. Top opportunities */}
      <section className="exec-panel">
        <h3 className="exec-panel-title">Top opportunities</h3>
        <div className="exec-table-wrap">
          <table className="exec-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Band</th>
                <th className="exec-num">Score</th>
                <th className="exec-num">Indicative value</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {topOpportunities.map((bundle) => {
                const band = bundle.score?.priority_band
                const value = bundle.pipeline_value?.estimated_annual_bank_revenue_eur
                const isLive = bundle.profile.data_source_type === 'live_grounded'
                return (
                  <tr
                    key={bundle.profile.startup_id}
                    className="exec-row"
                    onClick={() => props.onSelect?.(bundle.profile.startup_id)}
                    tabIndex={0}
                    role="button"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        props.onSelect?.(bundle.profile.startup_id)
                      }
                    }}
                  >
                    <td className="exec-cell-name">{bundle.profile.name}</td>
                    <td>
                      {band ? (
                        <span
                          className="exec-pill"
                          style={{ color: BAND_TOKENS[band].color, background: BAND_TOKENS[band].bg }}
                        >
                          {PRIORITY_BAND_LABELS[band]}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="exec-num exec-cell-score">
                      {bundle.score ? bundle.score.final_score.toFixed(1) : '—'}
                    </td>
                    <td className="exec-num">{value != null ? formatEur(value) : '—'}</td>
                    <td>
                      <span className={`exec-chip ${isLive ? 'exec-chip-live' : 'exec-chip-synthetic'}`}>
                        {isLive ? 'LIVE' : 'SYNTHETIC'}
                      </span>
                    </td>
                  </tr>
                )
              })}
              {topOpportunities.length === 0 && (
                <tr>
                  <td colSpan={5} className="exec-empty">
                    No scored opportunities yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5. Strategic message */}
      <p className="exec-strategic">
        From reactive product fulfilment to proactive, evidence-based growth partnership.
      </p>
    </div>
  )
}
