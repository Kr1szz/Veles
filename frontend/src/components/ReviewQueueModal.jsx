import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function ReviewQueueModal({ user, onReviewSubmitted }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  const [overrideDecision, setOverrideDecision] = useState('APPROVE');
  const [reviewNotes, setReviewNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const data = await api.getReviewQueue();
      setQueue(data.items || []);
    } catch (err) {
      console.error('Failed to load review queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleSubmitOverride = async (e) => {
    e.preventDefault();
    if (!selectedCase) return;
    if (!reviewNotes || reviewNotes.trim().length < 5) {
      setStatusMsg('Audit requirement: Review notes must be at least 5 characters.');
      return;
    }

    setSubmitting(true);
    setStatusMsg('');
    try {
      const res = await api.overrideDecision(
        selectedCase.id,
        overrideDecision,
        reviewNotes
      );
      setStatusMsg(`Successfully recorded override to ${res.new_decision}. Audit hash: ${res.audit_hash.substring(0, 16)}...`);
      setSelectedCase(null);
      setReviewNotes('');
      fetchQueue();
      if (onReviewSubmitted) onReviewSubmitted();
    } catch (err) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Human-in-the-Loop Analyst Review Queue</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Review flagged high-risk verifications requiring manual oversight under RBI KYC / Fraud Guidelines.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchQueue} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Queue'}
        </button>
      </div>

      {statusMsg && (
        <div
          style={{
            padding: '0.6rem 0.85rem',
            marginBottom: '1rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
            backgroundColor: statusMsg.startsWith('Error') ? 'var(--color-danger-bg)' : 'var(--color-success-bg)',
            color: statusMsg.startsWith('Error') ? '#fca5a5' : '#86efac',
            border: '1px solid rgba(255,255,255,0.1)'
          }}
        >
          {statusMsg}
        </div>
      )}

      {queue.length === 0 ? (
        <div className="data-table-container" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          ✓ All verification queues clear! Zero pending manual reviews.
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Masked Identifier</th>
                <th>Risk Score</th>
                <th>Flagged Factors</th>
                <th>Latency</th>
                <th>Time</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item) => (
                <tr key={item.id}>
                  <td>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, padding: '0.15rem 0.4rem', backgroundColor: '#1e293b', borderRadius: '3px' }}>
                      {item.entity_type}
                    </span>
                  </td>
                  <td>
                    <strong>{item.name_masked || item.id_masked || 'N/A'}</strong>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {item.email_masked || item.id_type || ''}
                    </div>
                  </td>
                  <td>
                    <span className="font-mono" style={{ color: 'var(--color-warning)', fontWeight: 600 }}>
                      {(item.risk_score * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.78rem', color: 'var(--color-warning)' }}>
                      {item.rules_triggered?.length || 0} rule(s)
                    </span>
                  </td>
                  <td className="font-mono" style={{ fontSize: '0.8rem' }}>
                    {item.latency_ms} ms
                  </td>
                  <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(item.created_at).toLocaleTimeString()}
                  </td>
                  <td>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => {
                        setSelectedCase(item);
                        setOverrideDecision('APPROVE');
                        setReviewNotes('');
                        setStatusMsg('');
                      }}
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Review Modal Dialog */}
      {selectedCase && (
        <div className="modal-overlay" onClick={() => setSelectedCase(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>
                Review Case: {selectedCase.name_masked || selectedCase.id_masked}
              </h3>
              <button
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}
                onClick={() => setSelectedCase(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
              <div style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                <strong>Verification ID:</strong> <code className="font-mono">{selectedCase.id}</code>
              </div>
              <div style={{ marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                <strong>Current Risk Score:</strong>{' '}
                <span className="font-mono" style={{ color: 'var(--color-warning)', fontWeight: 600 }}>
                  {(selectedCase.risk_score * 100).toFixed(1)}%
                </span>
              </div>

              {/* Triggered rules in review case */}
              {selectedCase.rules_triggered && selectedCase.rules_triggered.length > 0 && (
                <div style={{ marginTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                    Triggered Warning Rules
                  </div>
                  {selectedCase.rules_triggered.map((r, i) => (
                    <div key={i} style={{ fontSize: '0.75rem', padding: '0.35rem 0.5rem', backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '3px', marginBottom: '0.25rem' }}>
                      <strong>{r.rule}:</strong> {r.detail}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <form onSubmit={handleSubmitOverride}>
              <div className="form-group">
                <label className="form-label">Analyst Decision Override</label>
                <select
                  className="form-select"
                  value={overrideDecision}
                  onChange={(e) => setOverrideDecision(e.target.value)}
                >
                  <option value="APPROVE">APPROVE (Accept identity / transaction)</option>
                  <option value="REJECT">REJECT (Decline / block identity)</option>
                  <option value="ESCALATE">ESCALATE (Refer to Compliance Officer)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">
                  Audit Notes &amp; Justification <span style={{ color: 'var(--color-danger)' }}>*</span>
                </label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="State justification (e.g., 'Verified customer identity documents via biometric verification')."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.25rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setSelectedCase(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Committing to Ledger...' : 'Commit Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
