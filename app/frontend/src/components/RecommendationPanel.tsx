import { useState } from 'react'
import { decideRecommendation } from '../api'
import type { RecommendationRecord, Role } from '../types'

export default function RecommendationPanel({
  recommendation,
  role,
  onDecided,
}: {
  recommendation: RecommendationRecord
  role: Role
  onDecided: (updated: RecommendationRecord) => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canApprove = role === 'relationship_manager' && recommendation.approval_status === 'draft'

  async function decide(decision: 'approved' | 'rejected') {
    setBusy(true)
    setError(null)
    try {
      const updated = await decideRecommendation(recommendation.recommendation_id, decision)
      onDecided(updated)
    } catch {
      setError('Could not record decision.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="recommendation-panel">
      <div className={`approval-status-banner ${recommendation.approval_status}`}>
        Status: {recommendation.approval_status.replace(/_/g, ' ')}
        {recommendation.approver && <span> &middot; by {recommendation.approver}</span>}
      </div>

      <section>
        <h3>Client summary</h3>
        <p>{recommendation.client_summary}</p>
      </section>

      <section>
        <h3>Why now</h3>
        <p>{recommendation.why_now}</p>
      </section>

      <section className="two-col">
        <div>
          <h3>Top drivers</h3>
          <ul>
            {recommendation.top_drivers.map((d) => (
              <li key={d}>{d.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Weak / missing drivers</h3>
          <ul>
            {recommendation.missing_drivers.length === 0 && <li>None</li>}
            {recommendation.missing_drivers.map((d) => (
              <li key={d}>{d.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>
      </section>

      <section>
        <h3>Evidence used</h3>
        <ul>
          {recommendation.evidence_used.length === 0 && <li>No signal evidence on file.</li>}
          {recommendation.evidence_used.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
      </section>

      <section>
        <h3>Suggested RM questions</h3>
        <ol>
          {recommendation.suggested_questions.map((q, i) => (
            <li key={i}>{q}</li>
          ))}
        </ol>
      </section>

      <section>
        <h3>Product conversation themes</h3>
        <div className="chip-row">
          {recommendation.product_themes.map((t) => (
            <span className="chip" key={t}>
              {t}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3>Caveats</h3>
        <ul>
          {recommendation.caveats.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </section>

      <section className="non-claims">
        <h3>What this brief does NOT claim</h3>
        <ul>
          {recommendation.what_not_to_claim.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </section>

      <div className="generation-meta">
        Generated {new Date(recommendation.generated_at).toLocaleString()} &middot; narrative source:{' '}
        {recommendation.llm_used ? 'Vertex AI Gemini (guardrail-checked)' : 'deterministic template'}
        {recommendation.guardrail_flags.length > 0 && (
          <span className="guardrail-warning"> &middot; guardrail flags: {recommendation.guardrail_flags.join(', ')}</span>
        )}
      </div>

      {canApprove && (
        <div className="approval-actions">
          <button disabled={busy} onClick={() => decide('approved')} className="approve">
            Approve
          </button>
          <button disabled={busy} onClick={() => decide('rejected')} className="reject">
            Reject
          </button>
        </div>
      )}
      {!canApprove && recommendation.approval_status === 'draft' && (
        <p className="hint">Only a Relationship Manager can approve or reject this brief.</p>
      )}
      {error && <div className="error-banner">{error}</div>}
    </div>
  )
}
