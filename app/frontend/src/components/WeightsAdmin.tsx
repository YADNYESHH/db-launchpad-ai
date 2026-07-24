import { useCallback, useEffect, useMemo, useState } from 'react'
import { ApiError, activateWeights, listAllWeights, proposeWeights } from '../api'
import type { Role, WeightConfig } from '../types'
import './WeightsAdmin.css'

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 403) return "You don't have permission for this action."
    return err.message || `Request failed (${err.status}).`
  }
  return 'Something went wrong. Please try again.'
}

function shortVersion(versionId: string): string {
  return versionId.length > 12 ? `${versionId.slice(0, 8)}…` : versionId
}

function sortConfigs(configs: WeightConfig[]): WeightConfig[] {
  return [...configs].sort((a, b) => {
    if (a.active !== b.active) return a.active ? -1 : 1
    return b.created_date.localeCompare(a.created_date)
  })
}

type CapabilityKey = 'product_owner' | 'admin' | 'control_reviewer'

const CAPABILITIES: { key: CapabilityKey; label: string; verb: string }[] = [
  { key: 'product_owner', label: 'Product Owners', verb: 'propose' },
  { key: 'admin', label: 'Admins', verb: 'activate' },
  { key: 'control_reviewer', label: 'Control Reviewers', verb: 'review' },
]

export default function WeightsAdmin(props: { role: Role }) {
  const { role } = props

  const [configs, setConfigs] = useState<WeightConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [changeReason, setChangeReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [activatingId, setActivatingId] = useState<string | null>(null)

  const canPropose = role === 'product_owner'
  const canActivate = role === 'admin'

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listAllWeights()
      setConfigs(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const rows = useMemo(() => sortConfigs(configs), [configs])

  const handlePropose = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setFormError(null)
      setSuccessMessage(null)
      const reason = changeReason.trim()
      if (!reason) {
        setFormError('A change reason is required.')
        return
      }
      setSubmitting(true)
      try {
        const created = await proposeWeights({ change_reason: reason })
        setChangeReason('')
        setSuccessMessage(
          `Proposal ${shortVersion(created.version_id)} submitted — a new draft awaits Admin activation.`,
        )
        await load()
      } catch (err) {
        setFormError(errorMessage(err))
      } finally {
        setSubmitting(false)
      }
    },
    [changeReason, load],
  )

  const handleActivate = useCallback(
    async (versionId: string) => {
      setError(null)
      setSuccessMessage(null)
      setActivatingId(versionId)
      try {
        await activateWeights(versionId)
        setSuccessMessage(`Version ${shortVersion(versionId)} is now the ACTIVE scoring model.`)
        await load()
      } catch (err) {
        setError(errorMessage(err))
      } finally {
        setActivatingId(null)
      }
    },
    [load],
  )

  return (
    <div className="wa-panel">
      <header className="wa-header">
        <h2 className="wa-title">Scoring weights governance</h2>
        <p className="wa-subtitle">
          Every scoring-model change is proposed, activated, and audit-logged — no silent edits.
        </p>
      </header>

      <div className="wa-caps" role="note" aria-label="Who can do what">
        {CAPABILITIES.map((cap) => (
          <span key={cap.key} className={`wa-cap${role === cap.key ? ' wa-cap-you' : ''}`}>
            <strong>{cap.label}</strong> {cap.verb}
            {role === cap.key && <span className="wa-cap-badge">you</span>}
          </span>
        ))}
        <span className="wa-cap wa-cap-audit">
          <span className="wa-cap-dot" aria-hidden="true" />
          every change is audit-logged
        </span>
      </div>

      {successMessage && (
        <div className="wa-alert wa-alert-success" role="status">
          <span className="wa-alert-icon" aria-hidden="true">
            ✓
          </span>
          <span>{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="wa-alert wa-alert-error" role="alert">
          <span className="wa-alert-icon" aria-hidden="true">
            !
          </span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="wa-state">Loading weight configurations…</div>
      ) : rows.length === 0 ? (
        <div className="wa-state">No weight configurations found yet.</div>
      ) : (
        <div className="wa-table-wrap">
          <table className="wa-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Version</th>
                <th>Owner</th>
                <th>Created</th>
                <th>Approved</th>
                <th>Change reason</th>
                {canActivate && <th className="wa-col-action">Action</th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((cfg) => (
                <tr key={cfg.version_id} className={cfg.active ? 'wa-row-active' : ''}>
                  <td>
                    {cfg.active ? (
                      <span className="wa-badge wa-badge-active">ACTIVE</span>
                    ) : (
                      <span className="wa-badge wa-badge-inactive">Inactive</span>
                    )}
                  </td>
                  <td>
                    <code className="wa-version" title={cfg.version_id}>
                      {shortVersion(cfg.version_id)}
                    </code>
                  </td>
                  <td>{cfg.owner}</td>
                  <td>{cfg.created_date}</td>
                  <td>
                    {cfg.approved_date ?? <span className="wa-pending">pending</span>}
                  </td>
                  <td className="wa-reason">{cfg.change_reason}</td>
                  {canActivate && (
                    <td className="wa-col-action">
                      {cfg.active ? (
                        <span className="wa-muted">—</span>
                      ) : (
                        <button
                          type="button"
                          className="wa-btn wa-btn-secondary"
                          disabled={activatingId === cfg.version_id}
                          onClick={() => handleActivate(cfg.version_id)}
                        >
                          {activatingId === cfg.version_id ? 'Activating…' : 'Activate'}
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {canPropose && (
        <form className="wa-form" onSubmit={handlePropose}>
          <h3 className="wa-form-title">Propose new weight configuration</h3>
          <p className="wa-form-hint">
            Creates a new draft cloned from the current configuration. It stays inactive until an
            Admin activates it — keeping the change reviewable and auditable.
          </p>
          <label className="wa-label" htmlFor="wa-change-reason">
            Change reason <span className="wa-required">*</span>
          </label>
          <textarea
            id="wa-change-reason"
            className="wa-textarea"
            value={changeReason}
            onChange={(e) => setChangeReason(e.target.value)}
            placeholder="Explain why this change is needed…"
            rows={4}
            required
          />
          {formError && <div className="wa-form-error">{formError}</div>}
          <div className="wa-form-actions">
            <button type="submit" className="wa-btn wa-btn-primary" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Propose new configuration'}
            </button>
          </div>
        </form>
      )}

      {!canPropose && !canActivate && (
        <p className="wa-note">
          This is a read-only view for your role. Weight changes are governed — Product Owners
          propose, Admins activate, and every change is audit-logged.
        </p>
      )}
    </div>
  )
}
