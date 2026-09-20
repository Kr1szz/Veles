import React from 'react';

export default function MetricsOverview({ metrics, loading }) {
  if (loading && !metrics) {
    return (
      <div className="metrics-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card" style={{ opacity: 0.6 }}>
            <div className="metric-header">Loading...</div>
            <div className="metric-value">--</div>
            <div className="metric-sub">Fetching telemetry</div>
          </div>
        ))}
      </div>
    );
  }

  const p50 = metrics?.latency_percentiles?.p50_ms ?? 0;
  const p95 = metrics?.latency_percentiles?.p95_ms ?? 0;
  const p99 = metrics?.latency_percentiles?.p99_ms ?? 0;
  const total = metrics?.total_evaluations ?? 0;
  const approvals = metrics?.decision_distribution?.approve ?? 0;
  const reviews = metrics?.decision_distribution?.review ?? 0;
  const rejects = metrics?.decision_distribution?.reject ?? 0;
  const activeKeys = metrics?.infrastructure?.active_velocity_keys ?? 0;

  const p95Color = p95 <= 50 ? 'var(--color-success)' : 'var(--color-danger)';

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <div className="metric-header">
          <span>Latency Telemetry</span>
          <span style={{ color: p95Color, fontSize: '0.75rem', fontWeight: 600 }}>
            {p95 <= 50 ? 'SLA Compliant' : 'Breach'}
          </span>
        </div>
        <div className="metric-value" style={{ color: p95Color }}>
          {p95} <span style={{ fontSize: '1rem', fontWeight: 500 }}>ms P95</span>
        </div>
        <div className="metric-sub font-mono">
          P50: {p50}ms · P99: {p99}ms (Target: &lt;50ms)
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span>Total Pipeline Volume</span>
          <span>Live</span>
        </div>
        <div className="metric-value">{total.toLocaleString()}</div>
        <div className="metric-sub">
          Real-time KYC &amp; Transaction Evaluations
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span>Decision Distribution</span>
          <span>Ratio</span>
        </div>
        <div className="metric-value" style={{ display: 'flex', gap: '0.75rem', alignItems: 'baseline' }}>
          <span style={{ color: 'var(--color-success)', fontSize: '1.4rem' }}>{approvals}</span>
          <span style={{ color: 'var(--color-warning)', fontSize: '1.2rem' }}>{reviews}</span>
          <span style={{ color: 'var(--color-danger)', fontSize: '1.2rem' }}>{rejects}</span>
        </div>
        <div className="metric-sub">
          Pass / Manual Review / Blocked
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">
          <span>Velocity &amp; Cache</span>
          <span>Sliding Window</span>
        </div>
        <div className="metric-value font-mono">{activeKeys}</div>
        <div className="metric-sub">
          Active IP/Device rate limit windows tracked
        </div>
      </div>
    </div>
  );
}
