import React from 'react';

function donutStyle(approve, review, reject) {
  const total = Math.max(1, approve + review + reject);
  const a = (approve / total) * 360;
  const b = a + (review / total) * 360;
  const stops = [
    `var(--green) 0deg`,
    `var(--green) ${a}deg`,
    `var(--amber) ${a}deg`,
    `var(--amber) ${b}deg`,
    `var(--red) ${b}deg`,
    `var(--red) 360deg`,
  ];
  return {
    background: `conic-gradient(${stops.join(',')})`,
    WebkitMask: 'radial-gradient(circle, transparent 55%, #000 56%)',
    mask: 'radial-gradient(circle, transparent 55%, #000 56%)',
  };
}

function Radar({ events }) {
  const RADIUS = 76;
  const blips = (events || []).slice(0, 16).map((evt, idx, arr) => {
    const angle = (idx / Math.max(1, arr.length)) * Math.PI * 2 - Math.PI / 2;
    const score = Number(evt.risk_score) || 0;
    const radius = 10 + (Math.min(1, Math.max(0, score)) * 0.82) * RADIUS;
    const x = Math.cos(angle) * radius;
    const y = Math.sin(angle) * radius;
    const kind = evt.decision === 'APPROVE' ? 'is-approve' : evt.decision === 'REVIEW' ? 'is-review' : evt.decision === 'REJECT' ? 'is-reject' : 'is-risk';
    return { x, y, kind, key: evt.id ?? idx };
  });

  return (
    <div className="radar-wrap">
      <div className="radar" aria-label="Risk proximity map">
        <div className="radar-ring r1" />
        <div className="radar-ring r2" />
        <div className="radar-ring r3" />
        <div className="radar-cross-h" />
        <div className="radar-cross-v" />
        <div className="radar-sweep" />
        <div className="radar-core" />
        {blips.map((b) => (
            <span key={b.key} className={`radar-blip ${b.kind} ${b.key === events?.[0]?.id ? 'is-latest' : ''}`} style={{ left: `calc(50% + ${b.x}px)`, top: `calc(50% + ${b.y}px)` }} />
        ))}
        <span className="radar-label">Risk proximity</span>
      </div>
    </div>
  );
}

function Sparkline({ events, target }) {
  const lats = (events || []).slice(0, 14).map((e) => e.latency_ms ?? 0);
  const max = Math.max(50, ...lats, 1);
  const bars = lats.length ? lats : [0, 0, 0, 0, 0, 0];
  return (
    <div>
      <div className="sparkline">
        {bars.map((v, i) => {
          const over = v > target;
          return (
            <span
              key={i}
              className="bar"
              style={{
                height: `${Math.max(3, (v / max) * 100)}%`,
                background: over
                  ? 'linear-gradient(180deg, var(--red), rgba(251, 77, 109, 0.15))'
                  : undefined,
                boxShadow: over ? '0 0 12px -2px rgba(251, 77, 109, 0.5)' : undefined,
              }}
            />
          );
        })}
      </div>
      <div className="spark-grid">
        <span>{lats.length ? new Date(events[0]?.timestamp).toLocaleTimeString() : '—'}</span>
        <span>window 14</span>
        <span>live</span>
      </div>
    </div>
  );
}

export default function MetricsOverview({ metrics, loading, events, eventStreamStatus }) {
  if (loading && !metrics) {
    return (
      <div className="kpis">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="kpi panel" style={{ opacity: 0.55 }}>
            <div className="kpi-label">Loading</div>
            <div className="kpi-value">--</div>
            <div className="kpi-sub">Fetching telemetry</div>
          </div>
        ))}
      </div>
    );
  }

  const p50 = metrics?.latency_percentiles?.p50_ms ?? 0;
  const p95 = metrics?.latency_percentiles?.p95_ms ?? 0;
  const p99 = metrics?.latency_percentiles?.p99_ms ?? 0;
  const target = metrics?.latency_percentiles?.sla_target_ms ?? 50;
  const latencySampleSize = metrics?.latency_percentiles?.sample_size ?? 0;
  const total = metrics?.total_evaluations ?? 0;
  const approvals = metrics?.decision_distribution?.approve ?? 0;
  const reviews = metrics?.decision_distribution?.review ?? 0;
  const rejects = metrics?.decision_distribution?.reject ?? 0;
  const activeKeys = metrics?.infrastructure?.active_velocity_keys ?? 0;
  const hasData = total > 0;
  const slaOk = p95 <= target;
  const latestEventTime = events?.[0]?.timestamp
    ? new Date(events[0].timestamp).toLocaleTimeString()
    : 'waiting for first decision';
  const streamConnected = eventStreamStatus === 'connected';

  return (
    <>
      <div className="kpis">
        <div className={`kpi panel accent-${slaOk ? 'cyan' : 'red'}`}>
          <div className="kpi-accent" />
          <div className="kpi-label">
            <span>Decision processing P95</span>
            <span className="kpi-chip" style={{ color: slaOk ? 'var(--green)' : 'var(--red)', border: `1px solid ${slaOk ? 'rgba(52,211,153,.4)' : 'rgba(251,77,109,.4)'}`, background: slaOk ? 'var(--green-dim)' : 'var(--red-dim)' }}>
              {hasData ? (slaOk ? 'UNDER TARGET' : 'OVER TARGET') : 'NO DATA'}
            </span>
          </div>
          <div className="kpi-value">
            {hasData ? p95 : '—'} <small>{hasData ? 'ms' : ''}</small>
          </div>
          <div className="kpi-sub font-mono">{hasData ? `P50 ${p50}ms · P99 ${p99}ms · n=${latencySampleSize}` : 'No processing samples yet'} · target {target}ms</div>
        </div>

        <div className="kpi panel accent-violet">
          <div className="kpi-accent" />
          <div className="kpi-label">
            <span>Pipeline volume</span>
            <span className="kpi-chip" style={{ color: 'var(--green)', border: '1px solid rgba(52,211,153,.4)', background: 'var(--green-dim)' }}>LIVE</span>
          </div>
          <div className="kpi-value">{total.toLocaleString()}</div>
          <div className="kpi-sub">Real-time KYC &amp; transaction evaluations</div>
        </div>

        <div className="kpi panel accent-green">
          <div className="kpi-accent" />
          <div className="kpi-label">
            <span>Decision distribution</span>
            <span className="kpi-chip" style={{ color: 'var(--text-3)' }}>PASS · REVIEW · BLOCK</span>
          </div>
          <div className="kpi-value">
            <span style={{ color: 'var(--green)' }}>{approvals.toLocaleString()}</span>
            <small> / </small>
            <span style={{ color: 'var(--amber)' }}>{reviews.toLocaleString()}</span>
            <small> / </small>
            <span style={{ color: 'var(--red)' }}>{rejects.toLocaleString()}</span>
          </div>
          <div className="kpi-sub">Approve / manual review / hard reject</div>
        </div>

        <div className="kpi panel accent-amber">
          <div className="kpi-accent" />
          <div className="kpi-label">
            <span>Velocity windows</span>
            <span className="kpi-chip" style={{ color: 'var(--violet)', border: '1px solid rgba(139,92,246,.4)', background: 'var(--violet-dim)' }}>SLIDING</span>
          </div>
          <div className="kpi-value font-mono">{activeKeys.toLocaleString()}</div>
          <div className="kpi-sub">Active IP / device rate-limit windows</div>
        </div>
      </div>

      <div className="signal-row">
        <div className="panel" style={{ padding: '14px' }}>
          <div className="stat-title signal-heading">
            <span>Risk proximity map</span>
            <span className={`signal-status ${streamConnected ? 'connected' : ''}`} aria-live="polite">
              <i className="signal-status-dot" />
              {streamConnected ? 'Live stream' : '5s refresh'}
              <span className="signal-updated">{latestEventTime}</span>
            </span>
          </div>
          <div className="radar-grid">
            <Radar events={events} />
            <div className="radar-legend">
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--green)' }} />Approve</span>
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--amber)' }} />Manual review</span>
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--red)' }} />Hard reject</span>
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--violet)' }} />Flagged</span>
            </div>
          </div>
        </div>

        <div className="panel" style={{ padding: '14px' }}>
          <div className="stat-title">Decision split</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '92px', height: '92px', borderRadius: '50%', flex: 'none', ...donutStyle(approvals, reviews, rejects), boxShadow: '0 0 24px -8px rgba(42,228,255,.35)' }} />
            <div className="donut-legend grow">
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--green)' }} />Approved<b>{approvals.toLocaleString()}</b></span>
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--amber)' }} />Review<b>{reviews.toLocaleString()}</b></span>
              <span className="legend-row"><span className="legend-swatch" style={{ background: 'var(--red)' }} />Blocked<b>{rejects.toLocaleString()}</b></span>
            </div>
          </div>
        </div>

        <div className="panel" style={{ padding: '14px' }}>
          <div className="stat-title">Pipeline latency <span className="hash">— configured 50ms target</span></div>
          <Sparkline events={events} target={target} />
        </div>
      </div>
    </>
  );
}
