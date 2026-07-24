import { PRIORITY_BAND_LABELS } from '../types'
import type { RecommendationRecord, ScoreRecord } from '../types'
import ScoreDonut from './ScoreDonut'

function bandClass(score: number): string {
  if (score >= 80) return 'high'
  if (score >= 60) return 'monitor'
  if (score >= 40) return 'validate'
  return 'no-action'
}

// Executive-glance summary: score, band, top opportunity, top risk, and
// evidence confidence in one row, so the detail tabs below are optional
// reading rather than required reading.
export default function SummaryStrip({
  score,
  recommendation,
}: {
  score: ScoreRecord
  recommendation: RecommendationRecord | null
}) {
  const topOpportunity = recommendation?.product_themes[0] ?? null
  const topRisk = recommendation?.caveats.find((c) => !c.startsWith('All data used is synthetic')) ?? null

  return (
    <div className={`summary-strip ${bandClass(score.final_score)}`}>
      <ScoreDonut score={score.final_score} band={score.priority_band} label="Opportunity" />
      <div className="summary-cell">
        <span className="summary-label">Priority</span>
        <span className="summary-value">{PRIORITY_BAND_LABELS[score.priority_band]}</span>
      </div>
      <div className="summary-cell">
        <span className="summary-label">Top opportunity</span>
        <span className="summary-value">{topOpportunity ?? '—'}</span>
      </div>
      <div className="summary-cell">
        <span className="summary-label">Top risk</span>
        <span className="summary-value">{topRisk ?? (recommendation ? 'None flagged' : '—')}</span>
      </div>
      {recommendation && (
        <div className="summary-cell">
          <span className="summary-label">Evidence confidence</span>
          <span className={`confidence-pill ${recommendation.evidence_confidence}`}>
            {recommendation.evidence_confidence}
          </span>
        </div>
      )}
    </div>
  )
}
