import React, { useState } from 'react';

export default function LiveEventFeed({ events, onSelectEvent }) {
  const [filter, setFilter] = useState('ALL');

  const filteredEvents = events.filter((e) => {
    if (filter === 'ALL') return true;
    return e.decision === filter;
  });

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Real-Time Verification Stream</h2>
          <span className="status-pill online" style={{ fontSize: '0.7rem', padding: '0.15rem 0.5rem' }}>
            SSE Connected
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.35rem' }}>
          {['ALL', 'APPROVE', 'REVIEW', 'REJECT'].map((type) => (
            <button
              key={type}
              className={`btn btn-sm ${filter === type ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter(type)}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      <div className="data-table-container">
        {filteredEvents.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No verification events recorded yet. Run a verification test below to see real-time pipeline events.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Subject / Identifier</th>
                <th>Decision</th>
                <th>Risk Score</th>
                <th>Engine Latency</th>
                <th>Rules Triggered</th>
                <th>Audit Hash Proof</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((evt, idx) => {
                const decisionClass =
                  evt.decision === 'APPROVE'
                    ? 'badge-approve'
                    : evt.decision === 'REVIEW'
                    ? 'badge-review'
                    : 'badge-reject';

                const isSub50 = evt.latency_ms <= 50.0;

                return (
                  <tr
                    key={evt.id || idx}
                    style={{ cursor: 'pointer' }}
                    onClick={() => onSelectEvent(evt)}
                    title="Click to view rule evaluation details"
                  >
                    <td>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          padding: '0.15rem 0.4rem',
                          backgroundColor: evt.type === 'KYC' ? '#1e293b' : '#0f291e',
                          color: evt.type === 'KYC' ? '#93c5fd' : '#86efac',
                          borderRadius: '3px',
                          border: '1px solid rgba(255,255,255,0.1)'
                        }}
                      >
                        {evt.type}
                      </span>
                    </td>
                    <td style={{ fontWeight: 500 }}>
                      {evt.name || evt.amount || 'N/A'}
                    </td>
                    <td>
                      <span className={`badge ${decisionClass}`}>
                        {evt.decision}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <div
                          style={{
                            width: '45px',
                            height: '5px',
                            backgroundColor: 'var(--border-subtle)',
                            borderRadius: '3px',
                            overflow: 'hidden'
                          }}
                        >
                          <div
                            style={{
                              width: `${Math.min(100, (evt.risk_score || 0) * 100)}%`,
                              height: '100%',
                              backgroundColor:
                                evt.risk_score > 0.7
                                  ? 'var(--color-danger)'
                                  : evt.risk_score > 0.3
                                  ? 'var(--color-warning)'
                                  : 'var(--color-success)'
                            }}
                          />
                        </div>
                        <span className="font-mono" style={{ fontSize: '0.8rem' }}>
                          {evt.risk_score?.toFixed(2) ?? '0.00'}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span
                        className="font-mono"
                        style={{
                          color: isSub50 ? 'var(--color-success)' : 'var(--color-danger)',
                          fontWeight: 600
                        }}
                      >
                        {evt.latency_ms} ms
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: evt.rules_count > 0 ? 'var(--color-warning)' : 'var(--text-muted)' }}>
                        {evt.rules_count || 0} flagged
                      </span>
                    </td>
                    <td>
                      <code className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        {evt.audit_hash}
                      </code>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'Just now'}
                    </td>
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
