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

export function AppHeader(props: { user: UserPublic; onLogout: () => void }) {
  const { user, onLogout } = props
  return (
    <header className="lp-header">
      <div className="lp-header-brand">
        <span className="lp-wordmark">LaunchPad AI</span>
        <span className="lp-tagline">
          Cross-border payments opportunity intelligence
        </span>
      </div>
      <div className="lp-header-user">
        <div className="lp-header-identity">
          <span className="lp-user-name">{user.name}</span>
          <span className="lp-role-chip">{humanizeRole(user.role)}</span>
        </div>
        <button
          type="button"
          className="lp-signout-btn"
          onClick={onLogout}
        >
          Sign out
        </button>
      </div>
    </header>
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
        <div key={tile.label} className="lp-stat-tile lp-surface">
          <span className="lp-stat-value">{tile.value}</span>
          <span className="lp-stat-label">{tile.label}</span>
          {tile.hint ? (
            <span className="lp-stat-hint">{tile.hint}</span>
          ) : null}
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
          <span className={`lp-band-dot ${BAND_COLOR_CLASS[band]}`} aria-hidden="true" />
          <span className="lp-band-label">{PRIORITY_BAND_LABELS[band]}</span>
          <span className="lp-band-meaning">{BAND_MEANINGS[band]}</span>
        </div>
      ))}
    </div>
  )
}

export function PrinciplesFooter() {
  return (
    <footer className="lp-footer">
      <span className="lp-footer-text">
        Built for the 2026 TDI Global Hackathon · Honest, explainable,
        human-governed AI
      </span>
    </footer>
  )
}
