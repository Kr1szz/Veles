import { useState } from 'react';
import LiveEventFeed from '../LiveEventFeed';
import VerificationSimulator from '../VerificationSimulator';

export default function OverviewWorkspace({ events, onSelectEvent, onVerificationComplete }) {
  const [harnessOpen, setHarnessOpen] = useState(false);

  return (
    <div className="stack">
      <LiveEventFeed events={events} onSelectEvent={onSelectEvent} />
      <section className="panel">
        <div className="panel-header">
          <span className="panel-title"><em>Test harness</em> — verification simulator</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setHarnessOpen((open) => !open)}>
            {harnessOpen ? 'Collapse' : 'Expand'}
          </button>
        </div>
        {harnessOpen && (
          <div className="panel-body">
            <VerificationSimulator onVerificationComplete={onVerificationComplete} />
          </div>
        )}
      </section>
    </div>
  );
}
