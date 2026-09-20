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
    <div className="stack mb">
      <div className="hstack-between">
        <div>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>Human-in-the-loop analyst review queue</h2>
          <p className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
            Review flagged high-risk verifications requiring manual oversight under RBI KYC / Fraud Guidelines.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchQueue} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh queue'}
        </button>
      </div>

      {statusMsg && (
        <div className={`alertbar ${statusMsg.startsWith('Error') ? 'error' : 'success'}`}>
          <span className="alert-title">{statusMsg.startsWith('Error') ? '✕' : '✓'} {statusMsg.startsWith('Error') ? 'Failed' : 'Committed to ledger'}</span>
          <span style={{ fontWeight: 600 }}>{statusMsg}</span>
        </div>
      )}

      {queue.length === 0 ? (
        <div className="panel">
          <div className="empty-state">
            <div className="hstack" style={{ justifyContent: 'center', color: 'var(--green)', fontWeight: 700 }}>
              <span style={{ color: 'var(--green)' }}>✓</span> All verification queues clear — zero pending manual reviews.
            </div>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="table">
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
                  <td><span className="tag tag-kyc">{item.entity_type}</span></td>
                  <td>
                    <strong>{item.name_masked || item.id_masked || 'N/A'}</strong>
                    <div className="cell-sub">{item.email_masked || item.id_type || ''}</div>
                  </td>
                  <td>
                    <span className="mono" style={{ color: 'var(--amber)', fontWeight: 700 }}>
                      {(item.risk_score * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ color: 'var(--amber)' }}>
                    {item.rules_triggered?.length || 0} rule(s)
                  </td>
                  <td className="mono">{item.latency_ms} ms</td>
                  <td className="cell-muted">{new Date(item.created_at).toLocaleTimeString()}</td>
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

      {selectedCase && (
        <div className="modal-overlay" onClick={() => setSelectedCase(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Review case: {selectedCase.name_masked || selectedCase.id_masked}</h3>
              <button className="modal-close" onClick={() => setSelectedCase(null)}>✕</button>
            </div>

            <div className="mb" style={{ fontSize: 12.5 }}>
              <div className="info-grid mb">
                <div><span className="k">Verification ID</span><span className="v mono">{selectedCase.id}</span></div>
                <div>
                  <span className="k">Risk score</span>
                  <span className="v mono" style={{ color: 'var(--amber)' }}>{(selectedCase.risk_score * 100).toFixed(1)}%</span>
                </div>
              </div>

              {selectedCase.rules_triggered?.length > 0 && (
                <div>
                  <div className="section-label mb" style={{ marginBottom: 6 }}>Triggered warning rules</div>
                  <div className="chip-list">
                    {selectedCase.rules_triggered.map((r, i) => (
                      <div key={i}>
                        <span className="tag tag-rule rule-tag">{r.rule}</span>
                        {r.detail}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmitOverride}>
              <div className="form-group">
                <label className="form-label">Analyst decision override</label>
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
                  Audit notes & justification <span style={{ color: 'var(--red)' }}>*</span>
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

              <div className="form-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedCase(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Committing to ledger...' : 'Commit decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}