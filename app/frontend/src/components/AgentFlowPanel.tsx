import type { ProfileBundle } from '../types'
import './AgentFlowPanel.css'

type ChipTone = 'done' | 'pending' | 'live' | 'human' | 'neutral'

interface Stage {
  title: string
  description: string
  status: string
  tone: ChipTone
}

// Honest narration of the multi-agent pipeline. Every stage's status is derived
// from the data actually present in the bundle — we never claim a step ran if
// the corresponding data is missing, and seed/manual data is labelled as such
// rather than dressed up as a live discovery.
function buildStages(bundle: ProfileBundle): Stage[] {
  const { profile, payment, pain, signals, score, decathlon, pipeline_value } = bundle

  // 1. Discovery — reflect the true provenance of this profile.
  const sourceType = profile.data_source_type
  let discoveryStatus: string
  let discoveryTone: ChipTone
  if (sourceType === 'live_grounded') {
    const citationCount = profile.source_citations?.length ?? 0
    discoveryStatus =
      citationCount > 0
        ? `Live-grounded · ${citationCount} source${citationCount === 1 ? '' : 's'}`
        : 'Live-grounded'
    discoveryTone = 'live'
  } else if (sourceType === 'synthetic') {
    discoveryStatus = 'Seed data'
    discoveryTone = 'neutral'
  } else if (sourceType === 'public_manual') {
    discoveryStatus = 'Manual entry'
    discoveryTone = 'neutral'
  } else {
    discoveryStatus = sourceType || 'Unknown source'
    discoveryTone = 'neutral'
  }

  // 2. Digital-twin builder — a bundle exists, so the profile is built; note the
  // richness of what was assembled without overstating it.
  const twinParts: string[] = []
  twinParts.push(`${signals.length} signal${signals.length === 1 ? '' : 's'}`)
  twinParts.push(payment ? 'payments ✓' : 'payments —')
  twinParts.push(pain ? 'pain ✓' : 'pain —')
  const twinStatus = `Built · ${twinParts.join(', ')}`

  // 3. Decathlon twin — computed only when dimensions are present.
  const dimCount = decathlon?.dimensions.length ?? 0
  const decathlonStatus = dimCount > 0 ? `Computed · ${dimCount} dims` : 'Pending'
  const decathlonTone: ChipTone = dimCount > 0 ? 'done' : 'pending'

  // 4. Opportunity scoring.
  const scoreStatus = score ? `Scored (${score.final_score.toFixed(0)})` : 'Not scored'
  const scoreTone: ChipTone = score ? 'done' : 'pending'

  // 5. Pipeline valuation.
  const pipelineStatus = pipeline_value ? 'Estimated' : 'Pending'
  const pipelineTone: ChipTone = pipeline_value ? 'done' : 'pending'

  return [
    {
      title: 'Discovery agent',
      description: 'Finds real startups via grounded web search (Gemini + Google Search).',
      status: discoveryStatus,
      tone: discoveryTone,
    },
    {
      title: 'Digital-twin builder',
      description: 'Assembles a structured profile: payments, pain points, expansion signals.',
      status: twinStatus,
      tone: 'done',
    },
    {
      title: 'Decathlon twin',
      description: 'Scores 10 business-maturity dimensions.',
      status: decathlonStatus,
      tone: decathlonTone,
    },
    {
      title: 'Opportunity scoring',
      description: 'Weighted, explainable 7-factor opportunity score with priority band.',
      status: scoreStatus,
      tone: scoreTone,
    },
    {
      title: 'Pipeline valuation',
      description: 'Estimates indicative annual bank revenue.',
      status: pipelineStatus,
      tone: pipelineTone,
    },
    {
      title: 'Recommendation + guardrail',
      description: 'Drafts an RM-ready recommendation and screens it for banned claims.',
      status: 'On request',
      tone: 'neutral',
    },
    {
      title: 'Human approval + audit',
      description: 'A reviewer approves/revises; every step is audit-logged.',
      status: 'Human-in-the-loop',
      tone: 'human',
    },
  ]
}

export default function AgentFlowPanel(props: { bundle: ProfileBundle | null }) {
  const { bundle } = props
  if (!bundle) {
    return null
  }

  const stages = buildStages(bundle)

  return (
    <section className="flow-panel" aria-label="Agent pipeline">
      <header className="flow-header">
        <h3 className="flow-title">Agent pipeline</h3>
        <p className="flow-subtitle">
          How this assessment was produced — each stage reflects the data actually present.
        </p>
      </header>
      <ol className="flow-timeline">
        {stages.map((stage, index) => (
          <li key={stage.title} className="flow-stage">
            <div className="flow-marker" aria-hidden="true">
              <span className="flow-dot" />
              {index < stages.length - 1 && <span className="flow-connector" />}
            </div>
            <div className="flow-body">
              <div className="flow-row">
                <span className="flow-stage-title">{stage.title}</span>
                <span className={`flow-chip flow-chip-${stage.tone}`}>{stage.status}</span>
              </div>
              <p className="flow-desc">{stage.description}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}
