import React from 'react';
export default function Header({ metrics, onOpenLogin, user, onLogout }) {
  const p95 = metrics?.latency_percentiles?.p95_ms;
  const total = metrics?.total_evaluations ?? 0;
  const healthy = p95 == null || p95 <= 50;
  return (
    <header className="app-header">
      <a className="brand-section" href="/" aria-label="Veles Shield home">
        <span className="brand-mark">⌬</span>
        <span>
          <strong>Veles Shield</strong>
          <small>Anti-Fraud Engine</small>
        </span>
      </a>
      <div className="header-status-group">
        <span className={`status-pill ${healthy ? 'healthy' : 'degraded'}`}>
          API health: {p95 == null ? 'Awaiting session' : healthy ? `Operational · ${p95}ms` : `Degraded · ${p95}ms`}
        </span>
        <span className="status-pill">
          Throughput: <b>{total.toLocaleString()}</b> decisions
        </span>
        <span className="status-pill elevated">Threat level: Elevated</span>
      </div>
      <div className="profile-area">
        {user ? (
          <>
            <span className="environment">Production</span>
            <span className="profile-name">{user.username}</span>
            <button className="text-button" onClick={onLogout}>Sign out</button>
          </>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={onOpenLogin}>Analyst sign in</button>
        )}
      </div>
    </header>
  );
}