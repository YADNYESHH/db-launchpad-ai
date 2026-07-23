import type { AuditEvent } from '../types'

export default function AuditTrail({ events }: { events: AuditEvent[] }) {
  if (events.length === 0) return <p>No audit events yet for this startup.</p>

  return (
    <ol className="audit-trail">
      {events.map((e) => (
        <li key={e.audit_id}>
          <div className="audit-event-header">
            <span className="audit-event-type">{e.event_type.replace(/_/g, ' ')}</span>
            <span className="audit-event-time">{new Date(e.timestamp).toLocaleString()}</span>
          </div>
          <div className="audit-event-actor">actor: {e.actor}</div>
          <pre className="audit-event-payload">{JSON.stringify(e.payload, null, 2)}</pre>
        </li>
      ))}
    </ol>
  )
}
