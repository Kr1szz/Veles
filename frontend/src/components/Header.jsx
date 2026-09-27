import React from 'react';
export default function Header({ metrics, user }) {
  const p95 = metrics?.latency_percentiles?.p95_ms;
  const target = metrics?.latency_percentiles?.sla_target_ms ?? 50;
  const total = metrics?.total_evaluations ?? 0;
  const healthy = p95 == null || p95 <= target;
  return (
    <header className="app-header">
      <a className="brand-section" href="/" aria-label="Veles Shield home">
        <span className="brand-mark">⌬</span>
        <span>
          <strong>Veles Shield</strong>
          <small>Risk Operations Demo</small>
        </span>
      </a>
      <div className="header-status-group">
        <span className={`status-pill ${healthy ? 'healthy' : 'degraded'}`}>
          Processing target: {p95 == null ? 'No decisions yet' : healthy ? `Under · ${p95}ms` : `Over · ${p95}ms`}
        </span>
        <span className="status-pill">
          Throughput: <b>{total.toLocaleString()}</b> decisions
        </span>
        <span className="status-pill">Synthetic demo data</span>
      </div>
      <div className="profile-area">
        <span className="environment">Demo workspace</span>
        <span className="profile-name">{user.username}</span>
      </div>
    </header>
  );
}
