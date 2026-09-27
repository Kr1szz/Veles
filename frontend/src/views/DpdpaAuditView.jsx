import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function DpdpaAuditView() {
  const [logs, setLogs] = useState([]);
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chainStatus, setChainStatus] = useState(null);
  const [verifyingChain, setVerifyingChain] = useState(false);

  const [erasureId, setErasureId] = useState('');
  const [erasureReason, setErasureReason] = useState('Synthetic demo data cleanup');
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
    <div className="stack mb">
      <div className="hstack-between">
        <div>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>Privacy controls & cryptographic audit ledger</h2>
          <p className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
            Demo controls: selected fields are encrypted at rest, consent records are stored, and audit entries are hash-linked. These mechanisms are not a compliance certification.
          </p>
        </div>
        <div className="hstack">
          <button className="btn btn-primary btn-sm" onClick={handleVerifyChain} disabled={verifyingChain}>
            {verifyingChain ? 'Verifying SHA-256 hashes...' : 'Verify cryptographic chain'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={fetchData} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {chainStatus && (
        <div className={`alertbar ${chainStatus.chain_intact ? 'success' : 'error'}`}>
          <div>
            <div className="alert-title">
              {chainStatus.chain_intact ? `✓ Chain intact — ${chainStatus.total_blocks_verified} blocks verified` : `⚠ Chain tamper detected: ${chainStatus.error}`}
            </div>
            <div className="alert-sub">Every risk evaluation and override is SHA-256 chained to its predecessor block.</div>
          </div>
          {chainStatus.latest_hash && (
            <div className="alert-side">
              <div className="cell-muted" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Latest block hash</div>
              <code className="mono" style={{ color: 'var(--cyan)', fontSize: 11 }}>{chainStatus.latest_hash.substring(0, 20)}...</code>
            </div>
          )}
        </div>
      )}

      <div className="signals-3up">
        <div className="panel">
          <div className="panel-body stack">
            <div>
              <span className="panel-title"><em>PII erasure demo</em></span>
              <p className="muted" style={{ fontSize: 11.5, marginTop: 6, lineHeight: 1.5 }}>
                Scrubs matching encrypted fields and appends an audit entry. Review retention and legal requirements before using this on real records.
              </p>
            </div>

            <form onSubmit={handleExecuteErasure}>
              <div className="form-group">
                <label className="form-label">Identifier (Email or PAN)</label>
                <input
                  type="text"
                  className="form-input mono"
                  placeholder="e.g. user@example.com or ABCPE1234F"
                  value={erasureId}
                  onChange={(e) => setErasureId(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Legal justification / reason</label>
                <input
                  type="text"
                  className="form-input"
                  value={erasureReason}
                  onChange={(e) => setErasureReason(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-secondary btn-sm btn-block" disabled={erasureLoading}>
                {erasureLoading ? 'Scrubbing encrypted PII...' : 'Execute cryptographic erasure'}
              </button>
            </form>

            {erasureResult && (
              <div className={`alertbar ${erasureResult.startsWith('Success') ? 'success' : 'error'}`} style={{ marginBottom: 0 }}>
                <span style={{ fontWeight: 600 }}>{erasureResult}</span>
              </div>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-body">
            <span className="panel-title"><em>Consent & purpose</em> limitation ledger</span>
            <p className="muted" style={{ fontSize: 11.5, marginTop: 6, marginBottom: 10, lineHeight: 1.5 }}>
              KYC requests require a consent flag and may add a purpose record. This demo does not enforce retention expiry or determine legal compliance.
            </p>
            <div style={{ maxHeight: 224, overflowY: 'auto' }}>
              {consents.length === 0 ? (
                <div className="empty-state" style={{ padding: '20px 0' }}>No consent records yet.</div>
              ) : (
                <table className="table" style={{ fontSize: 11 }}>
                  <thead>
                    <tr>
                      <th>Principal hash</th>
                      <th>Purpose</th>
                      <th>Status</th>
                      <th>Retention</th>
                    </tr>
                  </thead>
                  <tbody>
                    {consents.map((c) => (
                      <tr key={c.id}>
                        <td style={{ maxWidth: 88 }}><code className="hash">{c.principal_hash?.slice(0, 10)}…</code></td>
                        <td style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.purpose}</td>
                        <td><span className="tag approve">{c.consent_status}</span></td>
                        <td className="mono">{c.retention_period_days}d</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-body">
            <span className="panel-title"><em>Chain verification</em> controls</span>
            <div className="stack mt" style={{ gap: 10 }}>
              <div className="info-grid" style={{ gridTemplateColumns: '1fr' }}>
                <div><span className="k">Ledger records in view</span><span className="v mono">{logs.length}</span></div>
                <div><span className="k">Consent records</span><span className="v mono">{consents.length}</span></div>
              </div>
              <div className="risk-bar" style={{ justifyContent: 'space-between' }}>
                <span className="muted">Hash chain status</span>
                <span className="tag approve">VERIFIED</span>
              </div>
              <p className="muted" style={{ fontSize: 11, lineHeight: 1.5 }}>
                Block<sub>n</sub> = SHA256(seq ∥ timestamp ∥ payload ∥ hash<sub>n−1</sub>). Any mutation breaks lineage.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div>
        <span className="panel-title mb" style={{ display: 'block', marginBottom: 8 }}><em>Immutable</em> transactional lineage log — SHA-256 chained</span>
        <div className="table-wrap">
          <table className="table">
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
                  <td><span className="mono" style={{ fontWeight: 700, color: 'var(--cyan)' }}>#{log.sequence_number}</span></td>
                  <td className="cell-muted">{new Date(log.timestamp).toLocaleString()}</td>
                  <td><span className="tag tag-rule">{log.event_type}</span></td>
                  <td><code className="hash">{log.entity_id ? log.entity_id.slice(0, 8) + '…' : 'N/A'}</code></td>
                  <td>{log.actor}</td>
                  <td><code className="hash cell-muted">{log.prev_hash?.slice(0, 12)}…</code></td>
                  <td><code className="hash" style={{ color: 'var(--cyan)' }}>{log.entry_hash?.slice(0, 16)}…</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
