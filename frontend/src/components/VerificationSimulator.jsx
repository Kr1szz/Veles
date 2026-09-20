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
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
      {/* Test Input & Presets */}
      <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Verification Simulator (Sub-50ms SLA)
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Test the real-time rule engine, C++ entropy calculations, and sliding-window rate limiting.
        </p>

        {/* Preset Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
          {Object.entries(PRESETS).map(([key, preset]) => (
            <button
              key={key}
              type="button"
              className={`btn ${selectedPreset === key ? 'btn-primary' : 'btn-secondary'}`}
              style={{ justifyContent: 'flex-start', textAlign: 'left', padding: '0.6rem 0.8rem' }}
              onClick={() => handleSelectPreset(key)}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{preset.label}</div>
                <div style={{ fontSize: '0.72rem', opacity: 0.8, marginTop: '0.1rem' }}>{preset.description}</div>
              </div>
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
          <button
            className="btn btn-primary"
            style={{ flex: 1 }}
            onClick={handleRunVerification}
            disabled={loading}
          >
            {loading ? 'Evaluating (sub-50ms)...' : `Evaluate ${activeType} Payload`}
          </button>

          <button
            className="btn btn-secondary"
            onClick={handleRunVelocityBurst}
            disabled={loading}
            title="Sends 7 rapid requests to trigger velocity limit (>5/min)"
          >
            Test Velocity Burst (7 reqs)
          </button>
        </div>

        {burstStatus && (
          <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', backgroundColor: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: '#fde68a' }}>
            {burstStatus}
          </div>
        )}

        {error && (
          <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', backgroundColor: 'var(--color-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', color: '#fca5a5' }}>
            {error}
          </div>
        )}
      </div>

      {/* Output & Audit Proof Panel */}
      <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Engine Decision &amp; Audit Lineage
        </h3>

        {!result ? (
          <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Select a preset and click &quot;Evaluate Payload&quot; to inspect real-time risk decisioning, sub-50ms latency metrics, and DPDPA audit proof.
          </div>
        ) : (
          <div>
            {/* Decision Banner */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                marginBottom: '1rem',
                backgroundColor:
                  result.decision === 'APPROVE'
                    ? 'var(--color-success-bg)'
                    : result.decision === 'REVIEW'
                    ? 'var(--color-warning-bg)'
                    : 'var(--color-danger-bg)',
                border: `1px solid ${
                  result.decision === 'APPROVE'
                    ? 'rgba(16, 185, 129, 0.4)'
                    : result.decision === 'REVIEW'
                    ? 'rgba(245, 158, 11, 0.4)'
                    : 'rgba(239, 68, 68, 0.4)'
                }`
              }}
            >
              <div>
                <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Decision</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{result.decision}</div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', textTransform: 'uppercase' }}>Risk Probability</div>
                <div className="font-mono" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                  {(result.risk_score * 100).toFixed(1)}%
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', textTransform: 'uppercase' }}>Engine Latency</div>
                <div
                  className="font-mono"
                  style={{
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    color: result.latency_ms <= 50 ? 'var(--color-success)' : 'var(--color-danger)'
                  }}
                >
                  {result.latency_ms} ms
                </div>
              </div>
            </div>

            {/* DPDPA Masked Data */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                DPDPA Masked Identifiers (Privy Aligned)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', fontSize: '0.8rem', backgroundColor: 'var(--bg-card)', padding: '0.6rem 0.75rem', borderRadius: 'var(--radius-sm)' }}>
                {Object.entries(result.masked_identifiers || {}).map(([k, v]) => (
                  <div key={k}>
                    <span style={{ color: 'var(--text-muted)' }}>{k}: </span>
                    <span className="font-mono" style={{ fontWeight: 600 }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Triggered Rules */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                Triggered Rules ({result.triggered_rules?.length || 0})
              </div>
              {result.triggered_rules?.length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-success)', padding: '0.4rem 0' }}>
                  ✓ Zero blacklist or format violations detected.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {result.triggered_rules.map((r, i) => (
                    <div
                      key={i}
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.4rem 0.6rem',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: 'var(--radius-sm)'
                      }}
                    >
                      <span style={{ fontWeight: 600, color: '#f87171' }}>[{r.rule}]</span> {r.detail}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Anomaly & Entropy Details */}
            {result.anomaly_breakdown && (
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                  C++ Anomaly &amp; Shannon Entropy Analysis
                </div>
                <div style={{ fontSize: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {result.anomaly_breakdown.name_entropy !== undefined && (
                    <div style={{ padding: '0.3rem 0.5rem', backgroundColor: 'var(--bg-card)', borderRadius: '3px' }}>
                      Name Entropy: <strong className="font-mono">{result.anomaly_breakdown.name_entropy}</strong>
                    </div>
                  )}
                  {result.anomaly_breakdown.composite_anomaly_score !== undefined && (
                    <div style={{ padding: '0.3rem 0.5rem', backgroundColor: 'var(--bg-card)', borderRadius: '3px' }}>
                      Composite Anomaly: <strong className="font-mono">{result.anomaly_breakdown.composite_anomaly_score}</strong>
                    </div>
                  )}
                  {result.anomaly_breakdown.ewma_risk_score !== undefined && (
                    <div style={{ padding: '0.3rem 0.5rem', backgroundColor: 'var(--bg-card)', borderRadius: '3px' }}>
                      EWMA Deviation Risk: <strong className="font-mono">{result.anomaly_breakdown.ewma_risk_score}</strong>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* SHA-256 Audit Hash */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cryptographic Audit Hash (SHA-256 Chained):</div>
              <code className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--color-info)', wordBreak: 'break-all' }}>
                {result.audit_hash}
              </code>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
