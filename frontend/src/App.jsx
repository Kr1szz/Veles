import { useState } from 'react';
import Header from './components/Header';
import MetricsOverview from './components/MetricsOverview';
import ReviewQueueView from './views/ReviewQueueView';
import DpdpaAuditView from './views/DpdpaAuditView';
import RulesConfigView from './views/RulesConfigView';
import SiteCrawlerView from './views/SiteCrawlerView';
import RiskInspector from './components/dashboard/RiskInspector';
import OverviewWorkspace from './components/dashboard/OverviewWorkspace';
import { DEFAULT_TAB, NAVIGATION } from './config/navigation';
import useDashboardData from './hooks/useDashboardData';

export default function App() {
  const [activeTab, setActiveTab] = useState(DEFAULT_TAB);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const user = { username: 'Local demo', role: 'admin' };

  const {
    metrics,
    loadingMetrics,
    events,
    pendingReviewsCount,
    eventStreamStatus,
    refreshMetrics,
    refreshReviewCount,
    onVerificationComplete,
  } = useDashboardData();

  const activeNavigation = NAVIGATION.find(({ id }) => id === activeTab) || NAVIGATION[0];
  const views = {
    stream: (
      <OverviewWorkspace
        events={events}
        onSelectEvent={setSelectedEvent}
        onVerificationComplete={onVerificationComplete}
      />
    ),
    crawler: <SiteCrawlerView />,
    reviews: (
      <ReviewQueueView
        onReviewSubmitted={() => { refreshMetrics(); refreshReviewCount(); }}
      />
    ),
    rules: <RulesConfigView />,
    dpdpa: <DpdpaAuditView />,
  };

  return (
    <div className="app-shell">
      <Header metrics={metrics} user={user} />
      <div className="workspace">
        <nav className="sidebar" aria-label="Primary navigation">
          <div className="sidebar-label">Operations</div>
          {NAVIGATION.map(({ id, label, icon }) => (
            <button
              key={id}
              type="button"
              className={`side-link ${activeTab === id ? 'active' : ''}`}
              aria-current={activeTab === id ? 'page' : undefined}
              onClick={() => setActiveTab(id)}
            >
              <span className="side-ico" aria-hidden="true">{icon}</span>
              <span className="side-label">{label}</span>
              {id === 'reviews' && pendingReviewsCount > 0 && <b>{pendingReviewsCount}</b>}
            </button>
          ))}
          <div className="sidebar-foot">
            <span className="status-dot" />
            <span>Process-local event stream</span>
          </div>
        </nav>

        <main className="main-panel">
          <MetricsOverview
            metrics={metrics}
            loading={loadingMetrics}
            events={events}
            eventStreamStatus={eventStreamStatus}
          />
          <div className="canvas-heading">
            <div>
              <span className="eyebrow">{activeTab === 'crawler' ? 'Data workspace' : 'Fraud operations'}</span>
              <h1>{activeTab === DEFAULT_TAB ? 'Real-time decision stream' : activeNavigation.label}</h1>
            </div>
            <span className="live-label">Live signal</span>
          </div>
          {views[activeTab] || views[DEFAULT_TAB]}
        </main>

        {activeTab === DEFAULT_TAB && <RiskInspector event={selectedEvent} />}
      </div>
    </div>
  );
}
