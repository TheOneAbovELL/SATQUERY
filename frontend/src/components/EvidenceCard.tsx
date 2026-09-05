import React from 'react';

export function EvidenceCard({ evidence }: { evidence: Record<string, any>; index: number }) {
  return (
    <div className="flex flex-col p-3 rounded sq-fade-in" style={{ background: 'var(--color-sq-surface-2)', border: '1px solid var(--color-sq-border)' }}>
      <p className="text-sm mb-3" style={{ color: 'var(--color-sq-text)' }}>{evidence.observation}</p>
      {evidence.metrics && Object.keys(evidence.metrics).length > 0 && (
        <div className="flex flex-col gap-1 p-2 rounded" style={{ background: 'var(--color-sq-surface-3)' }}>
          {Object.entries(evidence.metrics).map(([k, v]) => (
            <div key={k} className="flex justify-between text-xs">
              <span style={{ color: 'var(--color-sq-muted)' }}>{k}</span>
              <span className="sq-mono" style={{ color: 'var(--color-sq-accent)' }}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
