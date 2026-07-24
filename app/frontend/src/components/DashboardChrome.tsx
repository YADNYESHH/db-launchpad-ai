import type { UserPublic, Role, PriorityBand } from '../types'
import { PRIORITY_BAND_LABELS } from '../types'
import '../theme.css'
import './DashboardChrome.css'

const ROLE_LABELS: Record<Role, string> = {
  relationship_manager: 'Relationship Manager',
  product_owner: 'Product Owner',
  control_reviewer: 'Control Reviewer',
  admin: 'Admin',
}

function humanizeRole(role: Role): string {
  return ROLE_LABELS[role] ?? role
}

const ROLE_HINTS: Record<Role, string> = {
  relationship_manager: 'You can ask, score, generate briefs, approve.',
  product_owner: 'You can add startups, propose weights.',
  control_reviewer: 'You can view and audit only.',
  admin: 'You can do all of the above, plus activate weight changes.',
}

export function AppHeader(props: { user: UserPublic; onLogout: () => void }) {
  const { user, onLogout } = props
  return (
    <header className="lp-header">
      <div className="lp-header-brand">
        <span className="lp-brandmark" aria-hidden="true">
          DB
        </span>
        <span className="lp-brand-text">
          <span className="lp-wordmark">DB LaunchPad AI</span>
          <span className="lp-tagline">
            AI-powered digital twin &amp; opportunity scoring for high-growth
            companies
          </span>
        </span>
      </div>
      <div className="lp-header-user">
        <div className="lp-header-identity-col">
          <div className="lp-header-identity">
            <span className="lp-user-name">{user.name}</span>
            <span className="lp-role-chip">{humanizeRole(user.role)}</span>
          </div>
          <span className="lp-role-hint">{ROLE_HINTS[user.role] ?? ''}</span>
        </div>
        <button type="button" className="lp-signout-btn" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  )
}

const INFO_CARDS: { label: string; value: string }[] = [
  {
    label: 'Release 1 · Focus use case',
    value: 'Cross-border payments, collections & cash management',
  },
  {
    label: 'Data policy',
    value: 'Live-first, human-reviewed. No confidential client data.',
  },
  {
    label: 'Purpose',
    value: 'Decision support only. Human review required.',
  },
  {
    label: 'Users',
    value: 'Relationship Managers, POs, Control Reviewers, Admins',
  },
]

export function InfoBar() {
  return (
    <div className="lp-info-bar" aria-label="Product context">
      {INFO_CARDS.map((card) => (
        <div key={card.label} className="lp-info-card">
          <span className="lp-info-label">{card.label}</span>
          <span className="lp-info-value">{card.value}</span>
        </div>
      ))}
    </div>
  )
}

const FLOW_STEPS: { n: number; label: string }[] = [
  { n: 1, label: 'Portfolio' },
  { n: 2, label: 'Startup profile' },
  { n: 3, label: 'Signal evidence' },
  { n: 4, label: 'Decathlon twin' },
  { n: 5, label: 'Opportunity scorecard' },
  { n: 6, label: 'Decision & ranking' },
  { n: 7, label: 'RM brief' },
  { n: 8, label: 'RM approves' },
  { n: 9, label: 'Audit trail' },
  { n: 10, label: 'Monitor & rescore' },
]

export function ApplicationFlow() {
  return (
    <section className="lp-flow" aria-label="Application flow">
      <div className="lp-flow-head">
        <span className="lp-flow-title">Application flow</span>
        <span className="lp-flow-caption">3 clicks to score</span>
      </div>
      <ol className="lp-flow-steps">
        {FLOW_STEPS.map((step) => (
          <li
            key={step.n}
            className={`lp-flow-step${
              step.n <= 3 ? ' lp-flow-step--active' : ''
            }`}
          >
            <span className="lp-flow-badge">{step.n}</span>
            <span className="lp-flow-label">{step.label}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}

const POLICY_CHIPS = [
  'Human-in-the-loop',
  'Explainable scoring',
  'No fabricated data',
  'Audit-logged',
  'Grounded discovery',
]

export function PolicyChips() {
  return (
    <div className="lp-policy-chips" role="list" aria-label="Governance policies">
      {POLICY_CHIPS.map((chip) => (
        <span key={chip} className="lp-policy-chip" role="listitem">
          <span className="lp-policy-dot" aria-hidden="true" />
          {chip}
        </span>
      ))}
    </div>
  )
}

export function StatTiles(props: {
  tiles: { label: string; value: string; hint?: string }[]
}) {
  const { tiles } = props
  return (
    <div className="lp-stat-tiles">
      {tiles.map((tile) => (
        <div key={tile.label} className="lp-stat-tile">
          <span className="lp-stat-value">{tile.value}</span>
          <span className="lp-stat-label">{tile.label}</span>
          {tile.hint ? <span className="lp-stat-hint">{tile.hint}</span> : null}
        </div>
      ))}
    </div>
  )
}

const BAND_ORDER: PriorityBand[] = [
  'high_priority',
  'monitor',
  'validate',
  'no_immediate_action',
]

const BAND_MEANINGS: Record<PriorityBand, string> = {
  high_priority: 'Act now',
  monitor: 'Track',
  validate: 'Needs data',
  no_immediate_action: 'Deprioritize',
}

const BAND_RANGES: Record<PriorityBand, string> = {
  high_priority: '80–100',
  monitor: '60–79',
  validate: '40–59',
  no_immediate_action: '<40',
}

const BAND_COLOR_CLASS: Record<PriorityBand, string> = {
  high_priority: 'lp-dot-high',
  monitor: 'lp-dot-monitor',
  validate: 'lp-dot-validate',
  no_immediate_action: 'lp-dot-none',
}

export function DecisionBandLegend() {
  return (
    <div className="lp-band-legend" aria-label="Decision band legend">
      {BAND_ORDER.map((band) => (
        <div key={band} className="lp-band-item">
          <span
            className={`lp-band-dot ${BAND_COLOR_CLASS[band]}`}
            aria-hidden="true"
          />
          <span className="lp-band-label">{PRIORITY_BAND_LABELS[band]}</span>
          <span className="lp-band-range">{BAND_RANGES[band]}</span>
          <span className="lp-band-meaning">{BAND_MEANINGS[band]}</span>
        </div>
      ))}
    </div>
  )
}

const PRINCIPLES: { title: string; subtitle: string }[] = [
  {
    title: 'Synthetic-safe fallback',
    subtitle: 'Live-first, no fabricated data',
  },
  {
    title: 'Human-in-the-loop',
    subtitle: 'Every output needs human review',
  },
  {
    title: 'Explainable & traceable',
    subtitle: 'Every score has evidence',
  },
  {
    title: 'Governed & auditable',
    subtitle: 'Full audit trail and controls',
  },
]

export function PrinciplesFooter() {
  return (
    <footer className="lp-footer">
      <div className="lp-footer-pillars">
        {PRINCIPLES.map((pillar) => (
          <div key={pillar.title} className="lp-footer-pillar">
            <span className="lp-footer-pillar-title">{pillar.title}</span>
            <span className="lp-footer-pillar-subtitle">{pillar.subtitle}</span>
          </div>
        ))}
      </div>
      <span className="lp-footer-note">
        DB LaunchPad AI — prototype for the 2026 TDI Global Hackathon
      </span>
    </footer>
  )
}
