import { useMemo, useState } from 'react'
import { PRIORITY_BAND_LABELS } from '../types'
import type { ProfileBundle, PriorityBand } from '../types'
import './CompareView.css'

const MAX_SELECTION = 3

const eurFormatter = new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
})

function formatEur(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return eurFormatter.format(value)
}

function bandPillClass(band: PriorityBand): string {
  switch (band) {
    case 'high_priority':
      return 'cmp-pill-high'
    case 'monitor':
      return 'cmp-pill-monitor'
    case 'validate':
      return 'cmp-pill-validate'
    default:
      return 'cmp-pill-none'
  }
}

// Top 3 Decathlon dimensions by score, formatted as "Label (score)".
function topDecathlon(bundle: ProfileBundle): { label: string; score: number }[] {
  const dims = bundle.decathlon?.dimensions ?? []
  return [...dims]
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((d) => ({ label: d.label, score: d.score }))
}

// A numeric metric row: extracts a comparable value per bundle so the row's
// leader (max) can be highlighted. null values are treated as absent.
interface NumericRow {
  kind: 'numeric'
  label: string
  value: (b: ProfileBundle) => number | null
  format: (v: number | null) => string
}

interface CustomRow {
  kind: 'custom'
  label: string
  render: (b: ProfileBundle) => React.ReactNode
}

type Row = NumericRow | CustomRow

const ROWS: Row[] = [
  {
    kind: 'custom',
    label: 'Priority band',
    render: (b) => {
      const band = b.score?.priority_band
      if (!band) return <span className="cmp-empty">—</span>
      return <span className={`cmp-pill ${bandPillClass(band)}`}>{PRIORITY_BAND_LABELS[band]}</span>
    },
  },
  {
    kind: 'numeric',
    label: 'Opportunity score',
    value: (b) => b.score?.final_score ?? null,
    format: (v) => (v == null ? '—' : Math.round(v).toString()),
  },
  {
    kind: 'custom',
    label: 'Sector',
    render: (b) => b.profile.sector || <span className="cmp-empty">—</span>,
  },
  {
    kind: 'custom',
    label: 'HQ country',
    render: (b) => b.profile.hq_country || <span className="cmp-empty">—</span>,
  },
  {
    kind: 'numeric',
    label: 'Annual revenue',
    value: (b) => b.profile.annual_revenue_eur ?? null,
    format: formatEur,
  },
  {
    kind: 'numeric',
    label: 'Cross-border payment value',
    value: (b) => b.payment?.annual_cross_border_payment_value_eur ?? null,
    format: formatEur,
  },
  {
    kind: 'numeric',
    label: 'Indicative pipeline value',
    value: (b) => b.pipeline_value?.estimated_annual_bank_revenue_eur ?? null,
    format: formatEur,
  },
  {
    kind: 'custom',
    label: 'Top Decathlon dimensions',
    render: (b) => {
      const top = topDecathlon(b)
      if (top.length === 0) return <span className="cmp-empty">—</span>
      return (
        <ul className="cmp-decathlon">
          {top.map((d) => (
            <li key={d.label}>
              <span className="cmp-decathlon-label">{d.label}</span>
              <span className="cmp-decathlon-score">{Math.round(d.score)}</span>
            </li>
          ))}
        </ul>
      )
    },
  },
]

function scoreOf(bundle: ProfileBundle): number {
  return bundle.score?.final_score ?? -Infinity
}

export default function CompareView(props: { bundles: ProfileBundle[] }) {
  const { bundles } = props

  // Default selection: top 2 by final score, when scores are available.
  const defaultSelection = useMemo(() => {
    return [...bundles]
      .sort((a, b) => scoreOf(b) - scoreOf(a))
      .filter((b) => b.score != null)
      .slice(0, 2)
      .map((b) => b.profile.startup_id)
  }, [bundles])

  const [selectedIds, setSelectedIds] = useState<string[]>(defaultSelection)

  const selectedBundles = useMemo(
    () =>
      selectedIds
        .map((id) => bundles.find((b) => b.profile.startup_id === id))
        .filter((b): b is ProfileBundle => b != null),
    [selectedIds, bundles],
  )

  const atLimit = selectedIds.length >= MAX_SELECTION

  function toggle(id: string): void {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= MAX_SELECTION) return prev
      return [...prev, id]
    })
  }

  // Per-numeric-row leader index (position within selectedBundles). Ties: first
  // maximum wins. Returns -1 when no bundle has a value.
  function leaderIndex(row: NumericRow): number {
    let best = -Infinity
    let idx = -1
    selectedBundles.forEach((b, i) => {
      const v = row.value(b)
      if (v != null && v > best) {
        best = v
        idx = i
      }
    })
    return idx
  }

  return (
    <div className="cmp-root">
      <div className="cmp-selector">
        <div className="cmp-selector-head">
          <h2 className="cmp-title">Compare startups</h2>
          <span className="cmp-selector-count">
            {selectedIds.length}/{MAX_SELECTION} selected
          </span>
        </div>
        <ul className="cmp-selector-list">
          {bundles.map((b) => {
            const id = b.profile.startup_id
            const checked = selectedIds.includes(id)
            const disabled = !checked && atLimit
            const band = b.score?.priority_band
            return (
              <li key={id} className="cmp-selector-item">
                <label className={`cmp-selector-label${disabled ? ' cmp-selector-label-disabled' : ''}`}>
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggle(id)}
                  />
                  <span className="cmp-selector-name">{b.profile.name}</span>
                  {band && (
                    <span className={`cmp-pill cmp-pill-sm ${bandPillClass(band)}`}>
                      {PRIORITY_BAND_LABELS[band]}
                    </span>
                  )}
                </label>
              </li>
            )
          })}
        </ul>
      </div>

      {selectedBundles.length === 0 ? (
        <p className="cmp-hint">Select up to 3 startups to compare</p>
      ) : (
        <div className="cmp-table-wrap">
          <table className="cmp-table">
            <thead>
              <tr>
                <th className="cmp-metric-head" scope="col">
                  Metric
                </th>
                {selectedBundles.map((b) => (
                  <th key={b.profile.startup_id} scope="col" className="cmp-startup-head">
                    {b.profile.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => {
                const leader = row.kind === 'numeric' ? leaderIndex(row) : -1
                const multi = selectedBundles.length > 1
                return (
                  <tr key={row.label}>
                    <th scope="row" className="cmp-metric-cell">
                      {row.label}
                    </th>
                    {selectedBundles.map((b, i) => {
                      if (row.kind === 'numeric') {
                        const v = row.value(b)
                        const isLeader = multi && i === leader && v != null
                        return (
                          <td
                            key={b.profile.startup_id}
                            className={`cmp-cell${isLeader ? ' cmp-leader' : ''}`}
                          >
                            {v == null ? <span className="cmp-empty">—</span> : row.format(v)}
                            {isLeader && <span className="cmp-leader-mark" aria-label="Best value"> ▲</span>}
                          </td>
                        )
                      }
                      return (
                        <td key={b.profile.startup_id} className="cmp-cell">
                          {row.render(b)}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
