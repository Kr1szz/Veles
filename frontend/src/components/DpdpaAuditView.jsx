import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function DpdpaAuditView() {
  const [logs, setLogs] = useState([]);
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chainStatus, setChainStatus] = useState(null);
  const [verifyingChain, setVerifyingChain] = useState(false);

  // Erasure form
  const [erasureId, setErasureId] = useState('');
  const [erasureReason, setErasureReason] = useState('Data Principal requested Right to be Forgotten under DPDPA 2023 Sec 12');
  const [erasureResult, setErasureResult] = useState('');
  const [erasureLoading, setErasureLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ledgerData, consentData] = await Promise.all([
        api.getAuditLedger(25),
        api.getConsents()
      ]);
      setLogs(ledgerData.items || []);
      setConsents(consentData || []);
    } catch (err) {
      console.error('Failed to load DPDPA ledger data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleVerifyChain = async () => {
    setVerifyingChain(true);
    try {
      const res = await api.verifyAuditChain();
      setChainStatus(res);
    } catch (err) {
      setChainStatus({ chain_intact: false, error: err.message });
    } finally {
      setVerifyingChain(false);
    }
  };

  const handleExecuteErasure = async (e) => {
    e.preventDefault();
    if (!erasureId.trim()) return;

    setErasureLoading(true);
    setErasureResult('');
    try {
      const res = await api.requestErasure(erasureId, erasureReason);
      setErasureResult(`Success: Wiped encrypted PII across ${res.records_erased} record(s). Immutable cryptographic audit proof recorded.`);
      setErasureId('');
      fetchData();
    } catch (err) {
      setErasureResult(`Error: ${err.message}`);
    } finally {
      setErasureLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>DPDPA 2023 Compliance &amp; Cryptographic Audit Ledger</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Aligned with IDfy Privy: Column-level encryption, purpose limitation, tamper-evident SHA-256 hash chains, and right to erasure.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleVerifyChain}
            disabled={verifyingChain}
          >
            {verifyingChain ? 'Verifying SHA-256 Hashes...' : 'Verify Cryptographic Chain Integrity'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={fetchData} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {/* Chain Verification Result Card */}
      {chainStatus && (
        <div
          style={{
            padding: '0.85rem 1rem',
            marginBottom: '1.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: chainStatus.chain_intact ? 'rgba(16, 185, 129, 0.15)' : 'var(--color-danger-bg)',
            border: `1px solid ${chainStatus.chain_intact ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}
        >
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: chainStatus.chain_intact ? '#86efac' : '#fca5a5' }}>
              {chainStatus.chain_intact
                ? `✓ Cryptographic Chain Intact (${chainStatus.total_blocks_verified} Blocks Verified)`
                : `⚠ Chain Tamper Detected: ${chainStatus.error}`}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Every risk evaluation and decision override is SHA-256 chained to its predecessor block.
            </div>
          </div>

          {chainStatus.latest_hash && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Latest Merkle/Block Hash:</div>
              <code className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--color-info)' }}>
                {chainStatus.latest_hash.substring(0, 20)}...
              </code>
            </div>
          )}
        </div>
      )}

      {/* Grid: Audit Ledger and Right to Erasure */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Right to Erasure / Forgotten Card */}
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            DPDPA Right to Erasure (Sec 12)
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Data Principals can request erasure of their personal identifiers. Veles Shield scrubs encrypted PII while preserving anonymized cryptographic audit lineage for statutory AML compliance.
          </p>

          <form onSubmit={handleExecuteErasure}>
            <div className="form-group">
              <label className="form-label">Identifier (Email or PAN)</label>
              <input
                type="text"
                className="form-input font-mono"
                placeholder="e.g. user@example.com or ABCPE1234F"
                value={erasureId}
                onChange={(e) => setErasureId(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Legal Justification / Reason</label>
              <input
                type="text"
                className="form-input"
                value={erasureReason}
                onChange={(e) => setErasureReason(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-secondary btn-sm"
              disabled={erasureLoading}
              style={{ width: '100%' }}
            >
              {erasureLoading ? 'Scrubbing Encrypted PII...' : 'Execute Cryptographic Erasure'}
            </button>
          </form>

          {erasureResult && (
            <div
              style={{
                marginTop: '0.75rem',
                padding: '0.5rem 0.75rem',
                fontSize: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: erasureResult.startsWith('Success') ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
                color: erasureResult.startsWith('Success') ? '#86efac' : '#fca5a5'
              }}
            >
              {erasureResult}
            </div>
          )}
        </div>

        {/* Consent Ledger Card */}
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            Consent &amp; Purpose Limitation Ledger
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            DPDPA 2023 requires purpose limitation. All verifications record explicit user consent and statutory retention expiry.
          </p>

          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {consents.length === 0 ? (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
                No active consents recorded yet.
              </div>
            ) : (
              <table className="data-table" style={{ fontSize: '0.75rem' }}>
                <thead>
                  <tr>
                    <th>Data Principal Hash</th>
                    <th>Purpose</th>
                    <th>Status</th>
                    <th>Retention</th>
                  </tr>
                </thead>
                <tbody>
                  {consents.map((c) => (
                    <tr key={c.id}>
                      <td><code className="font-mono">{c.principal_hash}</code></td>
                      <td style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {c.purpose}
                      </td>
                      <td>
                        <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>{c.consent_status}</span>
                      </td>
                      <td>{c.retention_period_days} days</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {/* Immutable Hash-Chained Audit Ledger */}
      <div>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem' }}>
          Immutable Transactional Lineage Log (SHA-256 Chained)
        </h3>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Seq #</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Entity Reference</th>
                <th>Actor</th>
                <th>Predecessor Hash</th>
                <th>Block Entry Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.sequence_number}>
                  <td>
                    <span className="font-mono" style={{ fontWeight: 700, color: 'var(--color-info)' }}>
                      #{log.sequence_number}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, padding: '0.15rem 0.4rem', backgroundColor: '#1e293b', borderRadius: '3px' }}>
                      {log.event_type}
                    </span>
                  </td>
                  <td>
                    <code className="font-mono" style={{ fontSize: '0.75rem' }}>
                      {log.entity_id ? log.entity_id.substring(0, 8) + '...' : 'N/A'}
                    </code>
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{log.actor}</td>
                  <td>
                    <code className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {log.prev_hash.substring(0, 12)}...
                    </code>
                  </td>
                  <td>
                    <code className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--color-info)' }}>
                      {log.entry_hash.substring(0, 16)}...
                    </code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
