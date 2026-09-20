import React, { useState } from 'react';
import { api } from '../services/api';

const PRESETS = {
  legit_kyc: {
    type: 'KYC',
    label: 'Clean Identity (Aadhaar / PAN)',
    description: 'Legitimate applicant with valid PAN and natural name entropy. Expects instant APPROVE (<5ms).',
    payload: {
      full_name: 'Ananya Deshmukh',
      email: 'ananya.deshmukh@gmail.com',
      phone: '+919820112233',
      id_type: 'PAN',
      id_number: 'ABCPE1234F',
      country_code: 'IN',
      device_fingerprint: 'dev_chrome_mac_m3',
      ip_address: '103.21.244.15',
      consent_given: true,
      consent_purpose: 'RBI KYC Verification & Onboarding'
    }
  },
  synthetic_identity: {
    type: 'KYC',
    label: 'Synthetic Identity (High Entropy Smash)',
    description: 'Bot-generated keyboard smash name with high Shannon entropy & unnatural consonants. Triggers C++ Anomaly Engine.',
    payload: {
      full_name: 'zkqjxpbv wqmnzxlk',
      email: 'x98q7w6e5r4t3y@domain.net',
      phone: '+919876543210',
      id_type: 'PAN',
      id_number: 'ABCPE1234F',
      country_code: 'IN',
      device_fingerprint: 'dev_puppeteer_node',
      ip_address: '103.21.244.18',
      consent_given: true,
      consent_purpose: 'KYC Verification'
    }
  },
  disposable_email: {
    type: 'KYC',
    label: 'Burner / Disposable Email',
    description: 'Fraudster attempting onboarding using mailinator.com. Triggers deterministic blacklist HARD REJECT.',
    payload: {
      full_name: 'Vikram Mehta',
      email: 'fraudster99@mailinator.com',
      phone: '+919876543210',
      id_type: 'PAN',
      id_number: 'ABCPE1234F',
      country_code: 'IN',
      device_fingerprint: 'dev_android_safe',
      ip_address: '103.21.244.20',
      consent_given: true,
      consent_purpose: 'KYC Verification'
    }
  },
  transaction_spike: {
    type: 'TRANSACTION',
    label: 'Transaction EWMA Anomaly',
    description: 'User with average 2,000 INR transactions suddenly attempts 450,000 INR transfer. Triggers EWMA statistical anomaly.',
    payload: {
      user_id: 'usr_premium_789',
      amount: 450000.0,
      currency: 'INR',
      device_fingerprint: 'dev_iphone_15_pro',
      ip_address: '103.21.244.25',
      user_historical_mean: 2200.0,
      user_historical_var: 150000.0,
      user_history_count: 24
    }
  }
};

export default function VerificationSimulator({ onVerificationComplete }) {
  const [selectedPreset, setSelectedPreset] = useState('legit_kyc');
  const [activeType, setActiveType] = useState('KYC');
  const [loading, setLoading] = useState(false);
  const [burstStatus, setBurstStatus] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState(PRESETS.legit_kyc.payload);

  const handleSelectPreset = (key) => {
    setSelectedPreset(key);
    setActiveType(PRESETS[key].type);
    setFormData(PRESETS[key].payload);
    setResult(null);
    setError('');
  };

  const handleRunVerification = async () => {
    setLoading(true);
    setError('');
    setBurstStatus('');
    try {
      let res;
      if (activeType === 'KYC') {
        res = await api.verifyKYC(formData);
      } else {
        res = await api.verifyTransaction(formData);
      }
      setResult(res);
      if (onVerificationComplete) onVerificationComplete(res);
    } catch (err) {
      setError(err.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRunVelocityBurst = async () => {
    setLoading(true);
    setResult(null);
    setError('');
    setBurstStatus('Executing burst of 7 rapid requests from IP 198.51.100.99...');

    try {
      const burstPayload = {
        ...PRESETS.legit_kyc.payload,
        ip_address: '198.51.100.99',
        full_name: 'Rapid Burst User'
      };

      const results = [];
      for (let i = 0; i < 7; i++) {
        const r = await api.verifyKYC({
          ...burstPayload,
          email: `burst_user_${i}@example.com`
        });
        results.push(r);
      }

      const blocked = results.filter((r) => r.decision === 'REJECT' || r.triggered_rules.some(tr => tr.rule.includes('VELOCITY')));
      setBurstStatus(`Burst complete: ${results.length} requests sent. ${blocked.length} rate-limited / flagged by sliding window velocity engine!`);
      setResult(results[results.length - 1]);
      if (onVerificationComplete) onVerificationComplete(results[results.length - 1]);
    } catch (err) {
      setError(err.message || 'Burst execution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '14px' }}>
      <div>
        <h3 style={{ fontSize: 13, fontWeight: 700, marginBottom: 4 }}>Verification simulator (sub-50ms SLA)</h3>
        <p className="muted" style={{ fontSize: 12, marginBottom: 12 }}>
          Fire real payloads through the rule engine, C++ entropy scorer, and sliding-window rate limiter.
        </p>

        <div className="preset-list mb">
          {Object.entries(PRESETS).map(([key, preset]) => (
            <button
              key={key}
              type="button"
              className={`btn preset-item ${selectedPreset === key ? 'btn-primary active' : 'btn-secondary'}`}
              onClick={() => handleSelectPreset(key)}
            >
              <b><span className="preset-dot">{selectedPreset === key ? '◉' : '○'}</span> {preset.label}</b>
              <span>{preset.description}</span>
            </button>
          ))}
        </div>

        <div className="hstack">
          <button className="btn btn-primary grow" onClick={handleRunVerification} disabled={loading}>
            {loading ? 'Evaluating (sub-50ms)...' : `Evaluate ${activeType} payload`}
          </button>
          <button className="btn btn-secondary" onClick={handleRunVelocityBurst} disabled={loading} title="Sends 7 rapid requests to trigger velocity limit (>5/min)">
            Velocity burst
          </button>
        </div>

        {burstStatus && <div className="alertbar info mt"><span className="alert-title">Burst</span><span style={{ fontWeight: 600 }}>{burstStatus}</span></div>}
        {error && <div className="alertbar error mt"><span className="alert-title">Error</span><span style={{ fontWeight: 600 }}>{error}</span></div>}
      </div>

      <div>
        <h3 style={{ fontSize: 13, fontWeight: 700, marginBottom: 12 }}>Engine decision & audit lineage</h3>

        {!result ? (
          <div className="empty-state" style={{ border: '1px dashed var(--line-strong)', borderRadius: 'var(--radius)' }}>
            Select a preset and run an evaluation to inspect real-time risk decisioning, latency, and DPDPA audit proof.
          </div>
        ) : (
          <div>
            <div className={`decision-banner ${(result.decision || '').toLowerCase()}`}>
              <div>
                <div className="lbl">Decision</div>
                <div className="val">{result.decision}</div>
              </div>
              <div>
                <div className="lbl">Risk probability</div>
                <div className="val">{((result.risk_score || 0) * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="lbl">Engine latency</div>
                <div className="val" style={{ color: (result.latency_ms ?? 0) <= 50 ? 'var(--green)' : 'var(--red)' }}>
                  {result.latency_ms} ms
                </div>
              </div>
            </div>

            {result.masked_identifiers && (
              <div className="mb">
                <div className="section-label mb" style={{ display: 'block', margin: '0 0 6px' }}>DPDPA masked identifiers (Privy aligned)</div>
                <div className="info-grid">
                  {Object.entries(result.masked_identifiers).map(([k, v]) => (
                    <div key={k}>
                      <span className="k">{k}</span>
                      <span className="v mono">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb">
              <div className="section-label" style={{ marginBottom: 6 }}>Triggered rules ({result.triggered_rules?.length || 0})</div>
              {result.triggered_rules?.length === 0 ? (
                <div style={{ fontSize: 12, color: 'var(--green)' }}>✓ Zero blacklist or format violations detected.</div>
              ) : (
                <div className="chip-list">
                  {result.triggered_rules.map((r, i) => (
                    <div key={i}>
                      <span className="tag tag-rule rule-tag">[{r.rule}]</span>
                      {r.detail}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {result.anomaly_breakdown && (
              <div className="mb">
                <div className="section-label" style={{ marginBottom: 6 }}>C++ anomaly & Shannon entropy analysis</div>
                <div className="hstack" style={{ flexWrap: 'wrap' }}>
                  {result.anomaly_breakdown.name_entropy !== undefined && (
                    <span className="mono stat-chip">Name entropy <strong>{result.anomaly_breakdown.name_entropy}</strong></span>
                  )}
                  {result.anomaly_breakdown.composite_anomaly_score !== undefined && (
                    <span className="mono stat-chip">Composite anomaly <strong>{result.anomaly_breakdown.composite_anomaly_score}</strong></span>
                  )}
                  {result.anomaly_breakdown.ewma_risk_score !== undefined && (
                    <span className="mono stat-chip">EWMA deviation <strong>{result.anomaly_breakdown.ewma_risk_score}</strong></span>
                  )}
                </div>
              </div>
            )}

            <div>
              <div className="section-label" style={{ color: 'var(--text-3)', marginBottom: 6 }}>Cryptographic audit hash (SHA-256 chained)</div>
              <code className="code-block">{result.audit_hash}</code>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}