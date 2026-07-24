import type { PipelineValue } from '../types'
import { formatEur } from '../format'
import './PipelineValuePanel.css'

const ACRONYMS: Record<string, string> = {
  fx: 'FX',
  nii: 'NII',
}

function humanizeKey(key: string): string {
  const words = key.split('_').filter(Boolean)
  return words
    .map((word, index) => {
      const acronym = ACRONYMS[word.toLowerCase()]
      if (acronym) return acronym
      if (index === 0) {
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      }
      return word.toLowerCase()
    })
    .join(' ')
}

export default function PipelineValuePanel(props: { pipelineValue: PipelineValue | null }) {
  const { pipelineValue } = props

  if (!pipelineValue) {
    return (
      <div className="pipe-panel">
        <p className="pipe-placeholder">Indicative pipeline value unavailable.</p>
      </div>
    )
  }

  const { estimated_annual_bank_revenue_eur, breakdown, basis } = pipelineValue

  const rows = Object.entries(breakdown).sort(([, a], [, b]) => b - a)

  return (
    <div className="pipe-panel">
      <h3 className="pipe-heading">Indicative pipeline value</h3>

      <div className="pipe-headline">
        <span className="pipe-figure">{formatEur(estimated_annual_bank_revenue_eur)}</span>
        <span className="pipe-caption">estimated annual bank revenue</span>
      </div>

      <dl className="pipe-breakdown">
        {rows.map(([key, value]) => (
          <div className="pipe-row" key={key}>
            <dt className="pipe-row-label">{humanizeKey(key)}</dt>
            <dd className="pipe-row-value">{formatEur(value)}</dd>
          </div>
        ))}
      </dl>

      <p className="pipe-basis">{basis}</p>
    </div>
  )
}
