import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function RulesConfigView() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRules()
      .then(data => setConfig(data))
      .catch(err => console.error('Failed to load rules:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="empty-state">Loading rule configurations...</div>;
  }

  const approveCutoff = Math.round((config?.system_thresholds?.auto_approve_cutoff ?? 0.3) * 100);
  const reviewCutoff = Math.round((config?.system_thresholds?.manual_review_cutoff ?? 0.7) * 100);

  return (
    <div className="stack mb">
      <div>
        <h2 style={{ fontSize: 15, fontWeight: 700 }}>Active rule engine & threshold configuration</h2>
        <p className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
          Configured deterministic checks and heuristic anomaly signals. Risk scoring has not been calibrated against labeled outcomes.
        </p>
      </div>

      <div className="kpis" style={{ marginBottom: 0 }}>
        <div className="kpi panel accent-green">
          <div className="kpi-accent" />
          <div className="kpi-label"><span>Auto-approve cutoff</span><span className="kpi-chip" style={{ color: 'var(--text-3)' }}>INSTANT</span></div>
          <div className="kpi-value mono" style={{ color: 'var(--green)' }}>&le; {(config?.system_thresholds?.auto_approve_cutoff * 100)}%</div>
          <div className="kpi-sub">Approved without human review</div>
        </div>

        <div className="kpi panel accent-amber">
          <div className="kpi-accent" />
          <div className="kpi-label"><span>Manual review range</span><span className="kpi-chip" style={{ color: 'var(--text-3)' }}>HITL</span></div>
          <div className="kpi-value mono" style={{ color: 'var(--amber)' }}>&gt;{approveCutoff}% – &lt;{reviewCutoff}%</div>
          <div className="kpi-sub">Routed to in-loop analyst</div>
        </div>

        <div className="kpi panel accent-red">
          <div className="kpi-accent" />
          <div className="kpi-label"><span>Hard reject threshold</span><span className="kpi-chip" style={{ color: 'var(--text-3)' }}>BLOCK</span></div>
          <div className="kpi-value mono" style={{ color: 'var(--red)' }}>&ge; {reviewCutoff}%</div>
          <div className="kpi-sub">Risk score at or above this cutoff</div>
        </div>

        <div className="kpi panel accent-cyan">
          <div className="kpi-accent" />
          <div className="kpi-label"><span>Processing time target</span><span className="kpi-chip" style={{ color: 'var(--text-3)' }}>CONFIG</span></div>
          <div className="kpi-value mono" style={{ color: 'var(--cyan)' }}>&lt; {config?.system_thresholds?.sla_max_latency_ms} ms</div>
          <div className="kpi-sub">Configured decision pipeline target</div>
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
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
                <td><code className="mono" style={{ fontWeight: 700, color: 'var(--cyan)' }}>{r.id}</code></td>
                <td style={{ fontWeight: 500 }}>{r.name}</td>
                <td><span className="tag tag-neutral">{r.type}</span></td>
                <td className="mono" style={{ fontSize: 11.5 }}>
                  {r.threshold || r.specification || (r.active_domains_count ? `${r.active_domains_count} domains` : '') || (r.high_threshold ? `Entropy > ${r.high_threshold}` : 'Default')}
                </td>
                <td>
                  <span className={`tag ${r.action === 'HARD_REJECT' ? 'reject' : r.action === 'FLAG_HIGH_RISK' ? 'review' : 'approve'}`}>
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
