const API_BASE = '/api/v1';

let authToken = '';

export const setAuthToken = (token) => {
  authToken = token;
};

export const getAuthToken = () => authToken;

const defaultHeaders = () => {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  return headers;
};

export const api = {
  // Authentication
  async login(username, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Login failed');
    const data = await res.json();
    return data;
  },

  async logout() {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'same-origin' });
    setAuthToken('');
  },

  async getProfile() {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: defaultHeaders(), credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  },

  // Telemetry & Metrics
  async getMetrics() {
    const res = await fetch(`${API_BASE}/metrics`, { headers: defaultHeaders(), credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  },

  // Verification Pipeline (Sub-50ms SLA)
  async verifyKYC(payload) {
    const start = performance.now();
    const res = await fetch(`${API_BASE}/verify/kyc`, {
      method: 'POST',
      headers: defaultHeaders(),
      body: JSON.stringify(payload),
    });
    const clientLatency = performance.now() - start;
    if (!res.ok) throw new Error((await res.json()).detail || 'KYC verification failed');
    const data = await res.json();
    data.client_measured_latency_ms = Math.round(clientLatency * 10) / 10;
    return data;
  },

  async verifyTransaction(payload) {
    const start = performance.now();
    const res = await fetch(`${API_BASE}/verify/transaction`, {
      method: 'POST',
      headers: defaultHeaders(),
      body: JSON.stringify(payload),
    });
    const clientLatency = performance.now() - start;
    if (!res.ok) throw new Error((await res.json()).detail || 'Transaction verification failed');
    const data = await res.json();
    data.client_measured_latency_ms = Math.round(clientLatency * 10) / 10;
    return data;
  },

  async getVerificationRecords(limit = 20, offset = 0, decision = '', entityType = '') {
    let url = `${API_BASE}/verify/records?limit=${limit}&offset=${offset}`;
    if (decision) url += `&decision=${encodeURIComponent(decision)}`;
    if (entityType) url += `&entity_type=${encodeURIComponent(entityType)}`;
    const res = await fetch(url, { headers: defaultHeaders() });
    if (!res.ok) throw new Error('Failed to fetch records');
    return res.json();
  },

  // Analyst Review Queue
  async getReviewQueue(limit = 50) {
    const res = await fetch(`${API_BASE}/reviews/queue?limit=${limit}`, { headers: defaultHeaders(), credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to fetch review queue');
    return res.json();
  },

  async overrideDecision(verificationId, overrideDecision, reviewNotes) {
    const res = await fetch(`${API_BASE}/reviews/${verificationId}/override`, {
      method: 'POST',
      headers: defaultHeaders(),
      body: JSON.stringify({
        override_decision: overrideDecision,
        review_notes: reviewNotes,
      }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Decision override failed');
    return res.json();
  },

  // DPDPA & Cryptographic Audit Ledger
  async getAuditLedger(limit = 50) {
    const res = await fetch(`${API_BASE}/dpdpa/audit-ledger?limit=${limit}`, { headers: defaultHeaders() });
    if (!res.ok) throw new Error('Failed to fetch audit ledger');
    return res.json();
  },

  async verifyAuditChain() {
    const res = await fetch(`${API_BASE}/dpdpa/audit-ledger/verify`, {
      method: 'POST',
      headers: defaultHeaders(),
    });
    if (!res.ok) throw new Error('Audit chain verification request failed');
    return res.json();
  },

  async getConsents() {
    const res = await fetch(`${API_BASE}/dpdpa/consents`, { headers: defaultHeaders() });
    if (!res.ok) throw new Error('Failed to fetch consent ledger');
    return res.json();
  },

  async requestErasure(identifier, reason) {
    const res = await fetch(`${API_BASE}/dpdpa/erasure`, {
      method: 'POST',
      headers: defaultHeaders(),
      body: JSON.stringify({ identifier, reason }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || 'Erasure request failed');
    return res.json();
  },

  // Rule Engine
  async getRules() {
    const res = await fetch(`${API_BASE}/rules`, { headers: defaultHeaders() });
    if (!res.ok) throw new Error('Failed to fetch rules');
    return res.json();
  },

  // Real-time Event Stream (SSE)
  connectEventStream(onEvent, onError) {
    const eventSource = new EventSource(`${API_BASE}/events/stream`, { withCredentials: true });
    eventSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        onEvent(parsed);
      } catch (err) {
        onError?.(err);
      }
    };
    eventSource.onerror = (err) => {
      if (onError) onError(err);
      eventSource.close();
    };
    return () => eventSource.close();
  },

  async getRecentEvents() {
    const res = await fetch(`${API_BASE}/events/recent`, { credentials: 'same-origin' });
    if (!res.ok) return [];
    return res.json();
  }
};
