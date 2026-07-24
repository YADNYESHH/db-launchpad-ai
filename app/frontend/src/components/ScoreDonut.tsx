import { useEffect, useState } from 'react'
import type { PriorityBand } from '../types'
import './ScoreDonut.css'

type BandTier = 'high' | 'monitor' | 'validate' | 'none'

const BAND_TO_TIER: Record<PriorityBand, BandTier> = {
  high_priority: 'high',
  monitor: 'monitor',
  validate: 'validate',
  no_immediate_action: 'none',
}

function tierFromScore(score: number): BandTier {
  if (score >= 80) return 'high'
  if (score >= 60) return 'monitor'
  if (score >= 40) return 'validate'
  return 'none'
}

// Circular gauge for the headline opportunity score. Renders an SVG track +
// progress arc (sweep proportional to score/100) with the rounded number in
// the center. Colour tier follows the priority band when provided, otherwise
// it is derived from the score so the visual and label always agree.
export default function ScoreDonut({
  score,
  band,
  size = 120,
  label,
}: {
  score: number
  band?: PriorityBand
  size?: number
  label?: string
}) {
  const clamped = Math.max(0, Math.min(100, score))
  const tier = band ? BAND_TO_TIER[band] : tierFromScore(clamped)

  const stroke = Math.max(6, Math.round(size * 0.09))
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const center = size / 2

  // Animate the arc from empty to its target sweep on mount.
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    const frame = requestAnimationFrame(() => setProgress(clamped))
    return () => cancelAnimationFrame(frame)
  }, [clamped])

  const dashOffset = circumference * (1 - progress / 100)
  const rounded = Math.round(clamped)

  return (
    <div
      className={`donut donut-${tier}`}
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Opportunity score ${rounded} of 100`}
    >
      <svg className="donut-svg" width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          className="donut-track"
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          strokeWidth={stroke}
        />
        <circle
          className="donut-arc"
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${center} ${center})`}
        />
      </svg>
      <div className="donut-center" aria-hidden="true">
        <span className="donut-score">{rounded}</span>
        <span className="donut-max">/100</span>
        {label && <span className="donut-label">{label}</span>}
      </div>
    </div>
  )
}
