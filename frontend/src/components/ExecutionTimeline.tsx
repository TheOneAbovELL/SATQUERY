import React from 'react';
import type { ExecutionTraceEvent } from '../types/schema';
import type { AnalysisPhase } from '../types/satquery';

export function ExecutionTimeline({ phase, events }: { phase: AnalysisPhase; events: ExecutionTraceEvent[] }) {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-lg sq-fade-in" style={{ background: 'var(--color-sq-surface)', border: '1px solid var(--color-sq-border)' }}>
      <div className="text-[10px] font-bold tracking-widest" style={{ color: 'var(--color-sq-muted)' }}>EXECUTION TRACE</div>
      {events.length === 0 ? (
        <div className="text-xs animate-pulse" style={{ color: 'var(--color-sq-accent)' }}>Awaiting execution data...</div>
      ) : (
        <div className="flex flex-col gap-2">
          {events.map((evt, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <div className="sq-mono" style={{ color: 'var(--color-sq-text)' }}>[{evt.stage}] {evt.action}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
