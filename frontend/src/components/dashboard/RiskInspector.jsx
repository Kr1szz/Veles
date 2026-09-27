export default function RiskInspector({ event }) {
  if (!event) {
    return (
      <aside className="inspector">
        <span className="eyebrow">Risk inspector</span>
        <h2>No request selected</h2>
        <p className="muted" style={{ marginTop: 9 }}>
          Select an entry in the live stream to examine masked telemetry and rule outcomes.
        </p>
      </aside>
    );
  }

  const score = Math.round((event.risk_score || 0) * 100);
  const riskLabel = score >= 70 ? 'HIGH RISK' : score >= 30 ? 'MEDIUM RISK' : 'LOW RISK';

  return (
    <aside className="inspector" aria-label="Risk inspector">
      <div className="inspector-heading">
        <div>
          <span className="eyebrow">Risk inspector</span>
          <h2>Request #{String(event.id || 'live').slice(0, 8)}</h2>
        </div>
        <span className={`decision-tag ${(event.decision || '').toLowerCase()}`}>{event.decision}</span>
      </div>

      <section className="inspector-section">
        <span className="section-label">User &amp; device telemetry</span>
        <dl className="telemetry-list">
          <div><dt>Session</dt><dd>{event.name || 'Masked subject'}</dd></div>
          <div><dt>Type</dt><dd>{event.type || 'Verification'}</dd></div>
          <div><dt>Observed</dt><dd>{event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : 'Live'}</dd></div>
        </dl>
      </section>

      <section className="inspector-section">
        <span className="section-label">Entropy &amp; risk</span>
        <div className="gauge-wrap">
          <div className="gauge" style={{ '--val': `${score * 3.6}deg` }}>
            <div className="gauge-inner"><strong>{score}</strong><small>/100</small></div>
          </div>
          <div>
            <div className="gauge-scale"><i className="scale-bar" /><span>low → high</span></div>
            <div className="gauge-hi" style={{ marginTop: 6 }}>{riskLabel}</div>
          </div>
        </div>
      </section>

      <section className="inspector-section">
        <span className="section-label">Triggered controls</span>
        {event.rules_count ? (
          <p className="rule-alert">
            {event.rules_count} control{event.rules_count === 1 ? '' : 's'} contributed to this decision.
          </p>
        ) : (
          <p className="muted" style={{ marginTop: 9 }}>No deterministic controls were triggered.</p>
        )}
      </section>
    </aside>
  );
}
