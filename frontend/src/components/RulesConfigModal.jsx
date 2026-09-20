import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function RulesConfigModal() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRules()
      .then(data => setConfig(data))
      .catch(err => console.error('Failed to load rules:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading rule configurations...</div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '1.25rem' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Active Rule Engine &amp; Threshold Configuration</h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          High-performance rule matrix combining deterministic checks, Shannon entropy, and statistical EWMA variance.
        </p>
      </div>

      {/* Threshold Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '0.85rem' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Auto-Approve Cutoff</div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-success)' }}>
            &le; {config?.system_thresholds?.auto_approve_cutoff * 100}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Instant approval without review</div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '0.85rem' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Manual Review Range</div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-warning)' }}>
            30% – 70%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Routed to human-in-the-loop analyst</div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '0.85rem' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Hard Reject Threshold</div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-danger)' }}>
            &ge; {config?.system_thresholds?.manual_review_cutoff * 100}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>High-confidence fraud decline</div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '0.85rem' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>SLA Latency Target</div>
          <div className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-info)' }}>
            &lt; {config?.system_thresholds?.sla_max_latency_ms} ms
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Targeting sub-50ms roundtrip</div>
        </div>
      </div>

      {/* Rules Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Rule ID</th>
              <th>Name</th>
              <th>Rule Type</th>
              <th>Threshold / Parameter</th>
              <th>Action / Severity</th>
            </tr>
          </thead>
          <tbody>
            {config?.rules?.map((r) => (
              <tr key={r.id}>
                <td><code className="font-mono" style={{ fontWeight: 600 }}>{r.id}</code></td>
                <td style={{ fontWeight: 500 }}>{r.name}</td>
                <td>
                  <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.4rem', backgroundColor: '#1e293b', borderRadius: '3px' }}>
                    {r.type}
                  </span>
                </td>
                <td className="font-mono" style={{ fontSize: '0.8rem' }}>
                  {r.threshold || r.specification || (r.active_domains_count ? `${r.active_domains_count} domains` : '') || (r.high_threshold ? `Entropy > ${r.high_threshold}` : 'Default')}
                </td>
                <td>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: r.action === 'HARD_REJECT' ? 'var(--color-danger)' : r.action === 'FLAG_HIGH_RISK' ? 'var(--color-warning)' : 'var(--color-info)'
                    }}
                  >
                    {r.action}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
