import React from 'react';

export function EvidenceCard({
  evidence,
  index,
}: {
  evidence: Record<string, any>;
  index: number;
}) {
  return (
    <div
      className="flex flex-col p-4 rounded-xl sq-fade-in transition-colors"
      style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid var(--color-sq-border)',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-1.5 h-1.5 rounded-full"
          style={{ background: 'var(--color-in-saffron)', opacity: 0.8 }}
        />
        <span className="sq-label">Observation {index + 1}</span>
      </div>

      {/* Observation text */}
      {evidence.observation && (
        <p
          className="text-[13px] font-light leading-relaxed mb-4"
          style={{ color: 'var(--color-sq-text)', opacity: 0.85 }}
        >
          {evidence.observation}
        </p>
      )}

      {/* Metrics */}
      {evidence.metrics && Object.keys(evidence.metrics).length > 0 && (
        <div
          className="flex flex-col gap-2 p-3 rounded-lg"
          style={{
            background: 'var(--color-sq-surface-2)',
            border: '1px solid var(--color-sq-border)',
          }}
        >
          {Object.entries(evidence.metrics).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between">
              <span
                className="text-[10px] tracking-wider uppercase"
                style={{ color: 'var(--color-sq-subtle)' }}
              >
                {k}
              </span>
              <span
                className="sq-mono text-[13px] font-medium"
                style={{ color: 'var(--color-sq-text)' }}
              >
                {String(v)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
