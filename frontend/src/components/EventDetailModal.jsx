import React from 'react';

export default function EventDetailModal({ event, onClose }) {
  if (!event) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Verification Details</h3>
            <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.4rem', backgroundColor: '#1e293b', borderRadius: '3px' }}>
              {event.type || 'KYC'}
            </span>
          </div>
          <button
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius-sm)' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Decision</div>
              <span className={`badge ${event.decision === 'APPROVE' ? 'badge-approve' : event.decision === 'REVIEW' ? 'badge-review' : 'badge-reject'}`}>
                {event.decision}
              </span>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Risk Score</div>
              <strong className="font-mono">{((event.risk_score || 0) * 100).toFixed(1)}%</strong>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Engine Latency</div>
              <strong className="font-mono" style={{ color: event.latency_ms <= 50 ? 'var(--color-success)' : 'var(--color-danger)' }}>
                {event.latency_ms} ms
              </strong>
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
              Subject Identifiers (Masked)
            </div>
            <div style={{ padding: '0.6rem 0.75rem', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius-sm)' }}>
              <div><strong>Name / Identifier:</strong> {event.name || event.amount || 'N/A'}</div>
              {event.email && <div><strong>Email:</strong> {event.email}</div>}
              {event.id_masked && <div><strong>ID Number:</strong> {event.id_masked}</div>}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
              Cryptographic Audit Proof (SHA-256 Chained)
            </div>
            <code className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--color-info)', wordBreak: 'break-all', display: 'block', backgroundColor: 'var(--bg-card)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
              {event.audit_hash}
            </code>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button className="btn btn-secondary btn-sm" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
