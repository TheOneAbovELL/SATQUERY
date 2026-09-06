import React, { useEffect, useState } from 'react';
import type { ExecutionTraceEvent } from '../types/schema';
import type { AnalysisPhase } from '../types/satquery';

const PIPELINE_STAGES = [
  { id: 'understanding', label: 'Understanding Query' },
  { id: 'validating',    label: 'Validating Imagery' },
  { id: 'selecting',     label: 'Selecting Analysis' },
  { id: 'running',       label: 'Running Analysis' },
  { id: 'interpreting',  label: 'Interpreting Results' },
  { id: 'finalizing',    label: 'Finalizing Answer' },
];

export function ExecutionTimeline({
  phase,
  events,
}: {
  phase: AnalysisPhase;
  events: ExecutionTraceEvent[];
}) {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    if (phase === 'done' || phase === 'failed' || phase === 'idle') return;
    const timer = setInterval(() => {
      setActiveStage((prev) => (prev < PIPELINE_STAGES.length - 1 ? prev + 1 : prev));
    }, 1400);
    return () => clearInterval(timer);
  }, [phase]);

  const isProcessing = phase !== 'done' && phase !== 'failed' && phase !== 'idle';

  return (
    <div
      className="flex flex-col gap-4 p-5 rounded-2xl w-full max-w-md sq-fade-in"
      style={{
        background: 'rgba(255,255,255,0.025)',
        border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="sq-label">Processing</span>
        {isProcessing && (
          <div className="flex items-center gap-1.5">
            {[
              { color: 'var(--color-in-saffron)', delay: '0ms' },
              { color: 'var(--color-in-white)',   delay: '250ms' },
              { color: 'var(--color-in-green)',    delay: '500ms' },
            ].map((d, i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full sq-glow-pulse"
                style={{ background: d.color, animationDelay: d.delay }}
              />
            ))}
          </div>
        )}
      </div>

      {/* Animated stages */}
      {isProcessing && events.length === 0 && (
        <div className="flex flex-col gap-1.5">
          {PIPELINE_STAGES.map((s, idx) => {
            const isPast    = idx < activeStage;
            const isCurrent = idx === activeStage;
            return (
              <div
                key={s.id}
                className="flex items-center gap-3 transition-all duration-500"
                style={{
                  opacity: isPast ? 0.22 : isCurrent ? 1 : 0.1,
                  transform: isCurrent ? 'translateX(4px)' : 'none',
                }}
              >
                <div
                  className="w-1.5 h-1.5 rounded-full shrink-0 transition-all duration-300"
                  style={{
                    background: isCurrent ? '#ffffff' : isPast ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.08)',
                    boxShadow: isCurrent ? '0 0 6px rgba(255,255,255,0.5)' : 'none',
                  }}
                />
                <span
                  className="text-[11px] font-mono"
                  style={{ color: isCurrent ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.35)' }}
                >
                  {s.label}{isCurrent ? ' …' : ''}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Backend trace events */}
      {events.length > 0 && (
        <div className="flex flex-col gap-2">
          {events.map((evt, i) => (
            <div key={i} className="flex items-start gap-3 sq-trace-appear text-[11px]">
              <div
                className="w-1.5 h-1.5 mt-1 rounded-full shrink-0"
                style={{
                  background: evt.status === 'FAILED' ? '#ef4444' : 'rgba(255,255,255,0.25)',
                }}
              />
              <div className="flex flex-col gap-0.5">
                <span className="text-[9px] font-semibold tracking-widest uppercase" style={{ color: 'rgba(255,255,255,0.25)' }}>
                  {evt.stage}
                </span>
                <span
                  className="font-mono leading-snug"
                  style={{ color: evt.status === 'FAILED' ? '#ef4444' : 'rgba(255,255,255,0.55)' }}
                >
                  {evt.action}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
