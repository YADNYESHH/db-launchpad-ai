import { useEffect, useState } from 'react'
import type { GovernanceMetrics } from '../types'
import { ApiError, getGovernanceMetrics } from '../api'
import { formatEur } from '../format'
import './ResponsibleAIPanel.css'

interface ProvenanceSegment {
  key: 'live_grounded' | 'synthetic' | 'public_manual'
  label: string
  count: number
  className: string
}

const CONTROLS: string[] = [
  'Deterministic, explainable scoring',
  'Banned-claim guardrail on every recommendation',
  'Missing-data caps priority band',
  'Governed scoring weights (proposed → approved)',
  'Full audit trail',
  'No confidential client data · grounded public sources only',
]

export default function ResponsibleAIPanel() {
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    getGovernanceMetrics()
      .then((data) => {
        if (active) setMetrics(data)
      })
      .catch((err: unknown) => {
        if (!active) return
        if (err instanceof ApiError) {
          setError(`Unable to load governance metrics (${err.status}): ${err.message}`)
        } else {
          setError('Unable to load governance metrics.')
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="rai-panel" aria-labelledby="rai-title">
      <header className="rai-header">
        <h2 className="rai-title" id="rai-title">
          Responsible AI &amp; Governance
        </h2>
        <p className="rai-subtitle">Fairness · Transparency · Auditability · Human-in-the-loop</p>
      </header>

      {loading && <p className="rai-status">Loading governance metrics…</p>}
      {error && (
        <p className="rai-status rai-status-error" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && metrics && <ResponsibleAIContent metrics={metrics} />}
    </section>
  )
}

function ResponsibleAIContent({ metrics }: { metrics: GovernanceMetrics }) {
  const { provenance } = metrics

  const segments: ProvenanceSegment[] = [
    { key: 'live_grounded', label: 'Live grounded', count: provenance.live_grounded, className: 'rai-seg-live' },
    { key: 'synthetic', label: 'Synthetic', count: provenance.synthetic, className: 'rai-seg-synthetic' },
    { key: 'public_manual', label: 'Public / manual', count: provenance.public_manual, className: 'rai-seg-public' },
  ]

  const provenanceTotal = segments.reduce((sum, seg) => sum + seg.count, 0)

  return (
    <>
      <div className="rai-section rai-provenance">
        <div className="rai-section-head">
          <h3 className="rai-section-title">Data provenance</h3>
          <span className="rai-citations">
            {metrics.live_citation_count} verifiable source citations
          </span>
        </div>

        <div
          className="rai-bar"
          role="img"
          aria-label={`Data provenance: ${provenance.live_grounded} live grounded, ${provenance.synthetic} synthetic, ${provenance.public_manual} public or manual`}
        >
          {provenanceTotal === 0 ? (
            <span className="rai-bar-empty" />
          ) : (
            segments.map((seg) =>
              seg.count > 0 ? (
                <span
                  key={seg.key}
                  className={`rai-bar-seg ${seg.className}`}
                  style={{ flexGrow: seg.count }}
                  title={`${seg.label}: ${seg.count}`}
                />
              ) : null,
            )
          )}
        </div>

        <ul className="rai-legend">
          {segments.map((seg) => (
            <li className="rai-legend-item" key={seg.key}>
              <span className={`rai-dot ${seg.className}`} aria-hidden="true" />
              <span className="rai-legend-label">{seg.label}</span>
              <span className="rai-legend-count">{seg.count}</span>
            </li>
          ))}
        </ul>

        <p className="rai-provenance-note">
          Grounded on public, citable sources — no fabricated data.
        </p>
      </div>

      <div className="rai-section">
        <h3 className="rai-section-title">Governance signals</h3>
        <div className="rai-stats">
          <StatCard label="Audit events logged" value={metrics.audit_event_count.toLocaleString()} />
          <StatCard label="Recommendations generated" value={metrics.recommendations_generated.toLocaleString()} />
          <StatCard label="Active weight version" value={metrics.active_weight_version ?? '—'} />
          <StatCard
            label="Human-in-the-loop"
            value={metrics.human_approval_required ? 'Required' : 'Optional'}
            tone={metrics.human_approval_required ? 'accent' : 'muted'}
          />
        </div>
        <p className="rai-pipeline-note">
          {formatEur(metrics.total_pipeline_value_eur)} indicative pipeline across{' '}
          {metrics.scored_profiles.toLocaleString()} of {metrics.total_profiles.toLocaleString()} scored profiles.
        </p>
      </div>

      <div className="rai-section">
        <h3 className="rai-section-title">Controls</h3>
        <ul className="rai-controls">
          {CONTROLS.map((control) => (
            <li className="rai-control" key={control}>
              <span className="rai-check" aria-hidden="true" />
              <span className="rai-control-label">{control}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rai-note">
        <span className="rai-note-badge">Regulatory-safe by design</span>
        <p className="rai-note-text">
          Outputs are decision-support only, human-approved, and never autonomous advice.
        </p>
      </div>
    </>
  )
}

function StatCard({
  label,
  value,
  tone = 'default',
}: {
  label: string
  value: string
  tone?: 'default' | 'accent' | 'muted'
}) {
  return (
    <div className={`rai-stat rai-stat-${tone}`}>
      <span className="rai-stat-value">{value}</span>
      <span className="rai-stat-label">{label}</span>
    </div>
  )
}
