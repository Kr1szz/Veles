import React from 'react';

export default function EventDetailModal({ event, onClose }) {
  if (!event) return null;

  const decision = event.decision === 'APPROVE' || event.decision === 'REVIEW' ? event.decision : 'REJECT';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="hstack">
            <h3>Verification details</h3>
            <span className={`tag ${event.type === 'KYC' ? 'tag-kyc' : 'tag-transaction'}`}>{event.type || 'KYC'}</span>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="stack">
          <div className="decision-banner" style={{ marginBottom: 0 }}>
            <div>
              <div className="lbl">Decision</div>
              <span className={`tag ${decision.toLowerCase()}`} style={{ fontSize: 13, marginTop: 4 }}>{event.decision}</span>
            </div>
            <div>
              <div className="lbl">Risk score</div>
              <div className="val">{((event.risk_score || 0) * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div className="lbl">Engine latency</div>
              <div className="val" style={{ color: (event.latency_ms ?? 0) <= 50 ? 'var(--green)' : 'var(--red)' }}>
                {event.latency_ms} ms
              </div>
            </div>
          </div>

          <div>
            <div className="section-label mb" style={{ display: 'block', marginBottom: 6 }}>Subject identifiers (masked)</div>
            <div className="info-grid">
              <div><span className="k">Name / identifier</span><span className="v">{event.name || event.amount || 'N/A'}</span></div>
              {event.email && <div><span className="k">Email</span><span className="v mono">{event.email}</span></div>}
              {event.id_masked && <div><span className="k">ID number</span><span className="v mono">{event.id_masked}</span></div>}
            </div>
          </div>

          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Cryptographic audit proof (SHA-256 chained)</div>
            <code className="code-block">{event.audit_hash}</code>
          </div>

          <div className="form-actions">
            <button className="btn btn-secondary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  );
}