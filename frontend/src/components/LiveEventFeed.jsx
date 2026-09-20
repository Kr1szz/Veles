import React, { useState } from 'react';

const KIND = { ALL: null, APPROVE: 'approve', REVIEW: 'review', REJECT: 'reject' };

export default function LiveEventFeed({ events, onSelectEvent }) {
  const [filter, setFilter] = useState('ALL');

  const filteredEvents = events.filter((e) => filter === 'ALL' || e.decision === filter);

  return (
    <div className="stack mb">
      <div className="feed-toolbar">
        <div className="hstack">
          <h2>Decision stream</h2>
          <span className="tag tag-neutral">{events.length} in window</span>
        </div>
        <div className="chips">
          {Object.keys(KIND).map((type) => (
            <button
              key={type}
              data-kind={KIND[type]}
              className={`chip ${filter === type ? 'active' : ''}`}
              onClick={() => setFilter(type)}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      <div className="table-wrap">
        {filteredEvents.length === 0 ? (
          <div className="empty-state">
            {events.length === 0
              ? 'No verification events recorded yet. Use the test harness below to pump live pipeline events into this stream.'
              : 'No events match the selected decision filter.'}
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Subject / Identifier</th>
                <th>Decision</th>
                <th>Risk Score</th>
                <th>Engine Latency</th>
                <th>Rules</th>
                <th>Audit Hash Proof</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((evt, idx) => {
                const decision = evt.decision === 'APPROVE' || evt.decision === 'REVIEW' ? evt.decision : 'REJECT';
                const risk = Number(evt.risk_score) || 0;
                const riskLevel = risk > 0.7 ? 'high' : risk > 0.3 ? 'mid' : 'low';
                const isSub50 = (evt.latency_ms ?? 0) <= 50;

                return (
                  <tr key={evt.id || idx} className="clickable" onClick={() => onSelectEvent(evt)} title="Click to inspect risk telemetry">
                    <td>
                      <span className={`tag ${evt.type === 'KYC' ? 'tag-kyc' : 'tag-transaction'}`}>{evt.type || 'KYC'}</span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{evt.name || evt.amount || 'N/A'}</td>
                    <td><span className={`tag ${decision.toLowerCase()}`}>{evt.decision}</span></td>
                    <td>
                      <div className="risk-bar">
                        <span className="risk-track"><span className={`risk-fill ${riskLevel}`} style={{ width: `${Math.min(100, risk * 100)}%` }} /></span>
                        <span className="risk-num">{risk.toFixed(2)}</span>
                      </div>
                    </td>
                    <td>
                      <span className="mono" style={{ color: isSub50 ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>
                        {evt.latency_ms ?? 0} ms
                      </span>
                    </td>
                    <td className="cell-muted">{(evt.rules_count || 0) === 0 ? <span style={{ color: 'var(--text-3)' }}>clean</span> : <span style={{ color: 'var(--amber)' }}>{evt.rules_count} flagged</span>}</td>
                    <td><code className="hash">{evt.audit_hash ? String(evt.audit_hash).slice(0, 14) : '—'}</code></td>
                    <td className="cell-muted">{evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'Just now'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}