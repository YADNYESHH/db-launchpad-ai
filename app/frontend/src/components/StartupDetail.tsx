import { useEffect, useState } from 'react'
import { ApiError, generateRecommendation, getAuditTrail, getProfile, scoreProfile } from '../api'
import type { AuditEvent, ProfileBundle, RecommendationRecord, Role, ScoreRecord } from '../types'
import ScoreCard from './ScoreCard'
import RecommendationPanel from './RecommendationPanel'
import AuditTrail from './AuditTrail'

type Tab = 'overview' | 'scorecard' | 'recommendation' | 'audit'

export default function StartupDetail({ startupId, role }: { startupId: string; role: Role }) {
  const [bundle, setBundle] = useState<ProfileBundle | null>(null)
  const [score, setScore] = useState<ScoreRecord | null>(null)
  const [recommendation, setRecommendation] = useState<RecommendationRecord | null>(null)
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [tab, setTab] = useState<Tab>('overview')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    setScore(null)
    setRecommendation(null)
    setMessage(null)
    setTab('overview')
    getProfile(startupId).then(setBundle)
    getAuditTrail(startupId).then(setAudit)
  }, [startupId])

  async function handleScore() {
    setBusy(true)
    setMessage(null)
    try {
      const result = await scoreProfile(startupId)
      setScore(result.score_record)
      setTab('scorecard')
      getAuditTrail(startupId).then(setAudit)
    } catch {
      setMessage('Scoring failed.')
    } finally {
      setBusy(false)
    }
  }

  async function handleGenerateBrief(force: boolean) {
    setBusy(true)
    setMessage(null)
    try {
      const rec = await generateRecommendation(startupId, force)
      setRecommendation(rec)
      setTab('recommendation')
      getAuditTrail(startupId).then(setAudit)
    } catch (err) {
      if (err instanceof ApiError) setMessage(err.message)
      else setMessage('Could not generate recommendation.')
    } finally {
      setBusy(false)
    }
  }

  if (!bundle) return <div className="panel">Loading…</div>

  const { profile, payment, pain, signals } = bundle

  return (
    <div className="panel startup-detail">
      <div className="startup-header">
        <h2>
          {profile.name} {profile.synthetic_flag && <span className="badge synthetic">SYNTHETIC</span>}
        </h2>
        <div className="startup-header-actions">
          <button disabled={busy} onClick={handleScore}>
            {score ? 'Re-score' : 'Score now'}
          </button>
          {score && (
            <button disabled={busy} onClick={() => handleGenerateBrief(false)}>
              Generate RM brief
            </button>
          )}
          {score && score.priority_band !== 'high_priority' && (
            <button disabled={busy} onClick={() => handleGenerateBrief(true)} className="secondary">
              Force draft brief
            </button>
          )}
        </div>
      </div>

      <nav className="tabs">
        <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>
          Overview & evidence
        </button>
        <button className={tab === 'scorecard' ? 'active' : ''} onClick={() => setTab('scorecard')} disabled={!score}>
          Scorecard
        </button>
        <button
          className={tab === 'recommendation' ? 'active' : ''}
          onClick={() => setTab('recommendation')}
          disabled={!recommendation}
        >
          RM brief
        </button>
        <button className={tab === 'audit' ? 'active' : ''} onClick={() => setTab('audit')}>
          Audit trail ({audit.length})
        </button>
      </nav>

      {message && <div className="error-banner">{message}</div>}

      {tab === 'overview' && (
        <div className="overview-tab">
          <table className="kv-table">
            <tbody>
              <tr>
                <th>Sector</th>
                <td>{profile.sector}</td>
              </tr>
              <tr>
                <th>HQ &rarr; target markets</th>
                <td>
                  {profile.hq_country} &rarr; {profile.target_countries.join(', ') || '—'}
                </td>
              </tr>
              <tr>
                <th>Growth / funding stage</th>
                <td>
                  {profile.growth_stage} / {profile.funding_stage}
                </td>
              </tr>
              <tr>
                <th>Annual revenue</th>
                <td>EUR {profile.annual_revenue_eur.toLocaleString()}</td>
              </tr>
              <tr>
                <th>Expansion timeline</th>
                <td>{profile.expansion_timeline_months ?? 'unknown'} months</td>
              </tr>
              {payment && (
                <tr>
                  <th>Annual cross-border payment value</th>
                  <td>EUR {payment.annual_cross_border_payment_value_eur.toLocaleString()}</td>
                </tr>
              )}
              {payment && (
                <tr>
                  <th>Currencies</th>
                  <td>{payment.currencies.join(', ')}</td>
                </tr>
              )}
              {pain && (
                <tr>
                  <th>Observed pain points</th>
                  <td>
                    {[
                      pain.payment_delay_issue && 'payment delays',
                      pain.cash_visibility_gap && 'cash visibility gap',
                      pain.cost_pressure && 'cost/FX pressure',
                      pain.provider_switch_risk && 'provider switch risk',
                    ]
                      .filter(Boolean)
                      .join(', ') || 'none recorded'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <h3>Signal evidence</h3>
          {signals.length === 0 && <p>No signals ingested for this startup.</p>}
          <table className="driver-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Country</th>
                <th>Date</th>
                <th>Source</th>
                <th>Confidence</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s) => (
                <tr key={s.signal_id}>
                  <td>{s.signal_type.replace(/_/g, ' ')}</td>
                  <td>{s.country ?? '—'}</td>
                  <td>{s.signal_date}</td>
                  <td>
                    {s.source_label} ({s.source_type})
                  </td>
                  <td>{s.confidence.toFixed(2)}</td>
                  <td>{s.evidence_note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'scorecard' && score && <ScoreCard record={score} />}

      {tab === 'recommendation' && recommendation && (
        <RecommendationPanel recommendation={recommendation} role={role} onDecided={setRecommendation} />
      )}

      {tab === 'audit' && <AuditTrail events={audit} />}
    </div>
  )
}
