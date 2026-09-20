import React from 'react';

export default function Header({ metrics, onOpenLogin, user, onLogout }) {
  const isCppActive = metrics?.infrastructure?.cpp_engine_accelerated;

  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand-section">
          <div className="brand-logo-icon" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="brand-title">AEGIS-Trust</span>
              <span className="brand-badge">IDfy Aligned</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              OnboardIQ · OneRisk · Privy Engine
            </div>
          </div>
        </div>

        <div className="header-status-group">
          <div className="status-pill online">
            <span className="pulse-dot"></span>
            <span>Sub-50ms SLA Active</span>
          </div>

          <div className="status-pill cpp">
            <span>{isCppActive ? 'C++20 Native Core' : 'Python Core'}</span>
          </div>

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {user.username} ({user.role})
              </span>
              <button className="btn btn-secondary btn-sm" onClick={onLogout}>
                Logout
              </button>
            </div>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={onOpenLogin}>
              Analyst Login
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
