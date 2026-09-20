import React, { useCallback, useEffect, useState } from 'react';
import Header from './components/Header';
import MetricsOverview from './components/MetricsOverview';
import LiveEventFeed from './components/LiveEventFeed';
import ReviewQueueModal from './components/ReviewQueueModal';
import DpdpaAuditView from './components/DpdpaAuditView';
import RulesConfigModal from './components/RulesConfigModal';
import LoginModal from './components/LoginModal';
import VerificationSimulator from './components/VerificationSimulator';
import { api } from './services/api';

const NAVIGATION = [
  ['stream', 'Overview', '◈'],
  ['reviews', 'Review queue', '◉'],
  ['rules', 'Rule engine', '◇'],
  ['dpdpa', 'DPDPA ledger', '▤'],
];

function RiskInspector({ event }) {
  if (!event) {
    return (
      <aside className="inspector">
        <span className="eyebrow">Risk inspector</span>
        <h2>No request selected</h2>
        <p className="muted" style={{ marginTop: 9 }}>Select an entry in the live stream to examine masked telemetry and rule outcomes.</p>
      </aside>
    );
  }
  const score = Math.round((event.risk_score || 0) * 100);
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
        <span className="section-label">User & device telemetry</span>
        <dl className="telemetry-list">
          <div><dt>Session</dt><dd>{event.name || 'Masked subject'}</dd></div>
          <div><dt>Type</dt><dd>{event.type || 'Verification'}</dd></div>
          <div><dt>Observed</dt><dd>{event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : 'Live'}</dd></div>
        </dl>
      </section>

      <section className="inspector-section">
        <span className="section-label">Entropy & risk</span>
        <div className="gauge-wrap">
          <div className="gauge" style={{ '--val': `${score * 3.6}deg` }}>
            <div className="gauge-inner">
              <strong>{score}</strong>
              <small>/100</small>
            </div>
          </div>
          <div>
            <div className="gauge-scale"><i className="scale-bar" /><span>low → high</span></div>
            <div className="gauge-hi" style={{ marginTop: 6 }}>{score >= 70 ? 'HIGH RISK' : score >= 30 ? 'MEDIUM RISK' : 'LOW RISK'}</div>
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

      <div className="inspector-actions">
        <button className="btn btn-secondary" disabled={event.decision !== 'REVIEW'}>Override & approve</button>
        <button className="btn btn-danger" disabled={event.decision !== 'REVIEW'}>Confirm fraud</button>
      </div>
    </aside>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState('stream');
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [pendingReviewsCount, setPendingReviewsCount] = useState(0);
  const [harnessOpen, setHarnessOpen] = useState(false);

  const refreshMetrics = useCallback(async () => {
    try { setMetrics(await api.getMetrics()); } finally { setLoadingMetrics(false); }
  }, []);
  const refreshReviewCount = useCallback(async () => {
    try { setPendingReviewsCount((await api.getReviewQueue(1)).total_pending || 0); } catch { setPendingReviewsCount(0); }
  }, []);

  useEffect(() => {
    api.getProfile().then(setUser).catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!user) { setMetrics(null); setEvents([]); return undefined; }
    setLoadingMetrics(true);
    refreshMetrics().catch(() => {});
    refreshReviewCount();
    api.getRecentEvents().then(setEvents).catch(() => setEvents([]));
    const stop = api.connectEventStream((event) => {
      setEvents((prev) => [event, ...prev.filter((item) => item.id !== event.id)].slice(0, 50));
      refreshMetrics().catch(() => {});
      refreshReviewCount();
    });
    const interval = window.setInterval(() => {
      refreshMetrics().catch(() => {});
      refreshReviewCount();
    }, 15000);
    return () => { stop(); window.clearInterval(interval); };
  }, [user, refreshMetrics, refreshReviewCount]);

  const signOut = async () => {
    await api.logout();
    setUser(null);
    setSelectedEvent(null);
  };

  const onVerificationComplete = (result) => {
    setEvents((prev) => [result, ...prev.filter((item) => item.id !== result.id)].slice(0, 50));
    refreshMetrics().catch(() => {});
    refreshReviewCount();
  };

  const content = !user ? (
    <div className="access-state">
      <span className="eyebrow">Analyst workspace</span>
      <h1>Sign in to monitor live verification traffic.</h1>
      <p>Operational telemetry and customer data are visible only to authorized Veles Shield operators.</p>
      <button className="btn btn-primary" onClick={() => setLoginOpen(true)}>Sign in securely</button>
    </div>
  ) : activeTab === 'stream' ? (
    <div className="stack">
      <LiveEventFeed events={events} onSelectEvent={setSelectedEvent} />
      <div className="panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '0 14px', borderBottom: '1px solid var(--line)' }}>
          <span className="panel-title"><em>Test harness</em> — verification simulator</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setHarnessOpen((v) => !v)}>
            {harnessOpen ? 'Collapse' : 'Expand'}
          </button>
        </div>
        {harnessOpen && (
          <div className="panel-body">
            <VerificationSimulator onVerificationComplete={onVerificationComplete} />
          </div>
        )}
      </div>
    </div>
  ) : activeTab === 'reviews' ? (
    <ReviewQueueModal user={user} onReviewSubmitted={() => { refreshMetrics(); refreshReviewCount(); }} />
  ) : activeTab === 'rules' ? (
    <RulesConfigModal />
  ) : (
    <DpdpaAuditView />
  );

  return (
    <div className="app-shell">
      <Header metrics={metrics} onOpenLogin={() => setLoginOpen(true)} user={user} onLogout={signOut} />
      <div className="workspace">
        <nav className="sidebar" aria-label="Primary navigation">
          <div className="sidebar-label">Operations</div>
          {NAVIGATION.map(([id, label, ico]) => (
            <button key={id} className={`side-link ${activeTab === id ? 'active' : ''}`} onClick={() => setActiveTab(id)}>
              <span className="side-ico" aria-hidden="true">{ico}</span>
              <span className="side-label">{label}</span>
              {id === 'reviews' && pendingReviewsCount > 0 && <b>{pendingReviewsCount}</b>}
            </button>
          ))}
          <div className="sidebar-foot">
            <span className="status-dot" />
            <span>Event stream secured</span>
          </div>
        </nav>
        <main className="main-panel">
          <MetricsOverview metrics={metrics} loading={loadingMetrics} events={events} />
          <div className="canvas-heading">
            <div>
              <span className="eyebrow">Fraud operations</span>
              <h1>{activeTab === 'stream' ? 'Real-time decision stream' : NAVIGATION.find(([id]) => id === activeTab)?.[1]}</h1>
            </div>
            {user && <span className="live-label">Live signal</span>}
          </div>
          {content}
        </main>
        {user && activeTab === 'stream' && <RiskInspector event={selectedEvent} />}
      </div>
      <LoginModal isOpen={loginOpen} onClose={() => setLoginOpen(false)} onLoginSuccess={(data) => setUser({ username: data.username, role: data.role })} />
    </div>
  );
}