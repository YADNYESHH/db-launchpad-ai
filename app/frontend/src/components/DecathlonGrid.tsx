import type { DecathlonTwin } from '../types'
import './DecathlonGrid.css'

function tierClass(score: number): string {
  if (score >= 70) return 'high'
  if (score >= 40) return 'mid'
  return 'low'
}

export default function DecathlonGrid(props: { decathlon: DecathlonTwin | null }) {
  const { decathlon } = props

  if (!decathlon || !decathlon.dimensions || decathlon.dimensions.length === 0) {
    return (
      <div className="deca-placeholder">
        Decathlon twin not yet computed for this startup.
      </div>
    )
  }

  const dimensions = decathlon.dimensions
  const average = Math.round(
    dimensions.reduce((sum, d) => sum + d.score, 0) / dimensions.length,
  )

  return (
    <section className="deca-root">
      <header className="deca-header">
        <div className="deca-titles">
          <h3 className="deca-title">Decathlon digital twin</h3>
          <p className="deca-caption">
            Current-state maturity across 10 business dimensions — a snapshot of
            how the startup operates today, distinct from the forward-looking
            opportunity score.
          </p>
        </div>
        <div className="deca-overall">
          <span className="deca-overall-value">{average}</span>
          <span className="deca-overall-label">avg maturity</span>
        </div>
      </header>

      <div className="deca-grid">
        {dimensions.map((dim) => {
          const width = Math.max(0, Math.min(100, dim.score))
          return (
            <div key={dim.key} className="deca-cell">
              <div className="deca-cell-head">
                <span className="deca-cell-label">{dim.label}</span>
                <span className="deca-cell-score">{Math.round(dim.score)}</span>
              </div>
              <div className="deca-bar-track">
                <div
                  className={`deca-bar-fill deca-tier-${tierClass(dim.score)}`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <p className="deca-driver">Top driver: {dim.top_driver}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
