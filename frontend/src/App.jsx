import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import MetricsOverview from './components/MetricsOverview';
import LiveEventFeed from './components/LiveEventFeed';
import VerificationSimulator from './components/VerificationSimulator';
import ReviewQueueModal from './components/ReviewQueueModal';
import DpdpaAuditView from './components/DpdpaAuditView';
import RulesConfigModal from './components/RulesConfigModal';
import LoginModal from './components/LoginModal';
import EventDetailModal from './components/EventDetailModal';
import { api, setAuthToken } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('stream'); // stream, reviews, dpdpa, rules
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [pendingReviewsCount, setPendingReviewsCount] = useState(0);

  // Fetch telemetry metrics
  const refreshMetrics = useCallback(async () => {
    try {
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  // Fetch review queue count
  const refreshReviewCount = useCallback(async () => {
    try {
      const data = await api.getReviewQueue(1);
      setPendingReviewsCount(data.total_pending || 0);
    } catch (err) {
      console.error('Failed to fetch review count:', err);
    }
  }, []);

  // Load initial profile if token exists
  useEffect(() => {
    api.getProfile()
      .then(u => setUser(u))
      .catch(() => setUser(null));
  }, []);

  // Telemetry poll
  useEffect(() => {
    refreshMetrics();
    refreshReviewCount();
    const interval = setInterval(() => {
      refreshMetrics();
      refreshReviewCount();
    }, 4000);
    return () => clearInterval(interval);
  }, [refreshMetrics, refreshReviewCount]);

  // Initial event history & SSE connection
  useEffect(() => {
    api.getRecentEvents().then(recent => {
      if (recent && recent.length > 0) {
        setEvents(recent);
      }
    });

    const cleanupSSE = api.connectEventStream(
      (newEvent) => {
        setEvents(prev => [newEvent, ...prev.slice(0, 49)]);
        refreshMetrics();
        refreshReviewCount();
      },
      () => {
        // Error fallback: fetch recent events periodically
      }
    );

    return () => cleanupSSE();
  }, [refreshMetrics, refreshReviewCount]);

  const handleLogout = () => {
    setAuthToken('');
    setUser(null);
  };

  return (
    <div className="app-container">
      <Header
        metrics={metrics}
        onOpenLogin={() => setLoginOpen(true)}
        user={user}
        onLogout={handleLogout}
      />

      <main className="main-content">
        {/* Top-Level Real-Time Telemetry Cards */}
        <MetricsOverview metrics={metrics} loading={loadingMetrics} />

        {/* Navigation Tabs */}
        <div className="nav-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === 'stream'}
            className={`nav-tab-btn ${activeTab === 'stream' ? 'active' : ''}`}
            onClick={() => setActiveTab('stream')}
          >
            Real-Time Stream &amp; Simulator
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'reviews'}
            className={`nav-tab-btn ${activeTab === 'reviews' ? 'active' : ''}`}
            onClick={() => setActiveTab('reviews')}
          >
            Analyst Review Queue
            {pendingReviewsCount > 0 && (
              <span className="tab-badge" style={{ backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)' }}>
                {pendingReviewsCount}
              </span>
            )}
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'dpdpa'}
            className={`nav-tab-btn ${activeTab === 'dpdpa' ? 'active' : ''}`}
            onClick={() => setActiveTab('dpdpa')}
          >
            DPDPA Ledger &amp; Privacy
          </button>

          <button
            role="tab"
            aria-selected={activeTab === 'rules'}
            className={`nav-tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
            onClick={() => setActiveTab('rules')}
          >
            Active Rule Engine
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'stream' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <VerificationSimulator
              onVerificationComplete={() => {
                refreshMetrics();
                refreshReviewCount();
              }}
            />
            <LiveEventFeed
              events={events}
              onSelectEvent={(e) => setSelectedEvent(e)}
            />
          </div>
        )}

        {activeTab === 'reviews' && (
          <ReviewQueueModal
            user={user}
            onReviewSubmitted={() => {
              refreshMetrics();
              refreshReviewCount();
            }}
          />
        )}

        {activeTab === 'dpdpa' && (
          <DpdpaAuditView />
        )}

        {activeTab === 'rules' && (
          <RulesConfigModal />
        )}
      </main>

      {/* Modals */}
      <LoginModal
        isOpen={loginOpen}
        onClose={() => setLoginOpen(false)}
        onLoginSuccess={(data) => {
          setUser({ username: data.username, role: data.role });
        }}
      />

      <EventDetailModal
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-inner">
          <div>
            <strong>AEGIS-Trust</strong> — Production-Grade Real-Time Verification Pipeline.
            Built with FastAPI, C++ SIMD, Redis &amp; PostgreSQL. Aligned with IDfy OnboardIQ, OneRisk, and Privy.
          </div>
          <div>
            <a href="/docs" target="_blank" rel="noopener noreferrer" style={{ marginRight: '1rem' }}>
              API Documentation (Swagger)
            </a>
            <span style={{ color: 'var(--text-muted)' }}>DPDPA 2023 Compliant</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
