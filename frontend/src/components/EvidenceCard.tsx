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
      className="flex flex-col p-4 rounded-2xl transition-all duration-200 sq-fade-in"
      style={{
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-5 h-5 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(255,153,51,0.1)', border: '1px solid rgba(255,153,51,0.2)' }}
        >
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#FF9933' }} />
        </div>
        <span className="sq-label">Observation {index + 1}</span>
      </div>

      {/* Observation text */}
      {evidence.observation && (
        <p
          className="text-[13px] font-light leading-relaxed mb-3"
          style={{ color: 'rgba(255,255,255,0.75)' }}
        >
          {evidence.observation}
        </p>
      )}

      {/* Metrics */}
      {evidence.metrics && Object.keys(evidence.metrics).length > 0 && (
        <div
          className="rounded-xl overflow-hidden"
          style={{ border: '1px solid rgba(255,255,255,0.05)' }}
        >
          {Object.entries(evidence.metrics).map(([k, v], i, arr) => (
            <div
              key={k}
              className="flex items-center justify-between px-3 py-2"
              style={{
                background: i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
                borderBottom: i < arr.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
              }}
            >
              <span className="text-[10px] tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.3)' }}>
                {k}
              </span>
              <span className="sq-mono text-[12px] font-medium" style={{ color: 'rgba(255,255,255,0.75)' }}>
                {String(v)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
