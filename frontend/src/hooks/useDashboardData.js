import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api';

const EVENT_WINDOW_SIZE = 50;
const REFRESH_INTERVAL_MS = 15000;
const RECENT_EVENTS_POLL_INTERVAL_MS = 5000;

function normalizeVerificationResult(result) {
  return {
    ...result,
    id: result.id || result.verification_id,
    type: result.type || result.entity_type,
    name: result.name || result.masked_identifiers?.name || result.masked_identifiers?.user_id || 'Synthetic subject',
    rules_count: result.rules_count ?? result.triggered_rules?.length ?? 0,
  };
}

function prependEvent(events, event) {
  const normalized = normalizeVerificationResult(event);
  return [normalized, ...events.filter((item) => item.id !== normalized.id)].slice(0, EVENT_WINDOW_SIZE);
}

function mergeRecentEvents(current, incoming) {
  const seen = new Set();
  return [...incoming, ...current]
    .filter((event) => {
      const key = event.id || `${event.timestamp}:${event.type}:${event.decision}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0))
    .slice(0, EVENT_WINDOW_SIZE);
}

export default function useDashboardData() {
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [events, setEvents] = useState([]);
  const [pendingReviewsCount, setPendingReviewsCount] = useState(0);
  const [eventStreamStatus, setEventStreamStatus] = useState('connecting');

  const refreshMetrics = useCallback(async () => {
    try {
      setMetrics(await api.getMetrics());
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  const refreshReviewCount = useCallback(async () => {
    try {
      setPendingReviewsCount((await api.getReviewQueue(1)).total_pending || 0);
    } catch {
      setPendingReviewsCount(0);
    }
  }, []);

  const refreshRecentEvents = useCallback(async () => {
    try {
      const recentEvents = await api.getRecentEvents();
      setEvents((current) => mergeRecentEvents(current, recentEvents));
    } catch {
      // Keep the last known event window while the stream or API recovers.
    }
  }, []);

  const onVerificationComplete = useCallback((event) => {
    setEvents((current) => prependEvent(current, event));
    refreshMetrics().catch(() => {});
    refreshReviewCount();
  }, [refreshMetrics, refreshReviewCount]);

  useEffect(() => {
    setLoadingMetrics(true);
    refreshMetrics().catch(() => {});
    refreshReviewCount();
    refreshRecentEvents();

    const stopEventStream = api.connectEventStream((event) => {
      setEvents((current) => prependEvent(current, event));
      refreshMetrics().catch(() => {});
      refreshReviewCount();
    }, setEventStreamStatus);
    const refreshInterval = window.setInterval(() => {
      refreshMetrics().catch(() => {});
      refreshReviewCount();
    }, REFRESH_INTERVAL_MS);
    const eventPollInterval = window.setInterval(refreshRecentEvents, RECENT_EVENTS_POLL_INTERVAL_MS);

    return () => {
      stopEventStream();
      window.clearInterval(refreshInterval);
      window.clearInterval(eventPollInterval);
    };
  }, [refreshMetrics, refreshRecentEvents, refreshReviewCount]);

  return {
    metrics,
    loadingMetrics,
    events,
    pendingReviewsCount,
    eventStreamStatus,
    refreshMetrics,
    refreshReviewCount,
    onVerificationComplete,
  };
}
