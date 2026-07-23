import { PRIORITY_BAND_LABELS, SUB_SCORE_LABELS } from '../types'
import type { ScoreRecord } from '../types'

function bandClass(score: number): string {
  if (score >= 80) return 'high'
  if (score >= 60) return 'monitor'
  if (score >= 40) return 'validate'
  return 'no-action'
}

export default function ScoreCard({ record }: { record: ScoreRecord }) {
  return (
    <div className="scorecard">
      <div className={`final-score-banner ${bandClass(record.final_score)}`}>
        <div className="final-score-value">{record.final_score.toFixed(1)} / 100</div>
        <div className="final-score-band">{PRIORITY_BAND_LABELS[record.priority_band]}</div>
        {record.missing_data_flags.length > 0 && (
          <div className="missing-data-warning">
            Missing/incomplete data: {record.missing_data_flags.join(', ')}
          </div>
        )}
      </div>

      <div className="sub-scores">
        {record.sub_scores.map((sub) => (
          <details key={sub.sub_score_type} className="sub-score-card">
            <summary>
              <span>{SUB_SCORE_LABELS[sub.sub_score_type] ?? sub.sub_score_type}</span>
              <span className={`sub-score-value ${bandClass(sub.score_value)}`}>
                {sub.score_value.toFixed(1)}
              </span>
              <span className={`confidence-pill ${sub.confidence_band}`}>{sub.confidence_band} confidence</span>
            </summary>
            <p className="rationale">{sub.rationale}</p>
            <table className="driver-table">
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Weight</th>
                  <th>Raw</th>
                  <th>Weighted</th>
                  <th>Rationale</th>
                </tr>
              </thead>
              <tbody>
                {sub.driver_scores.map((d) => (
                  <tr key={d.driver_name} className={d.missing_data ? 'missing' : ''}>
                    <td>{d.driver_name.replace(/_/g, ' ')}</td>
                    <td>{d.weight}</td>
                    <td>{d.raw_score.toFixed(0)}</td>
                    <td>{d.weighted_score.toFixed(1)}</td>
                    <td className="driver-rationale">{d.rationale}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        ))}
      </div>
    </div>
  )
}
