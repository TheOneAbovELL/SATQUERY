import React, { useEffect, useState } from 'react';
import type { ExecutionTraceEvent } from '../types/schema';
import type { AnalysisPhase } from '../types/satquery';

const PIPELINE_STAGES = [
  { id: 'understanding', label: 'Understanding Query' },
  { id: 'validating',    label: 'Validating Imagery' },
  { id: 'selecting',     label: 'Selecting Analysis' },
  { id: 'running',       label: 'Running Geospatial Analysis' },
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
      className="flex flex-col gap-4 p-5 rounded-xl w-full max-w-md sq-fade-in"
      style={{
        background: 'var(--color-sq-surface-2)',
        border: '1px solid var(--color-sq-border)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="sq-label">Analysis Pipeline</span>
        {isProcessing && (
          <div className="flex items-center gap-1">
            <div
              className="w-1.5 h-1.5 rounded-full sq-glow-pulse"
              style={{ background: 'var(--color-in-saffron)' }}
            />
            <div
              className="w-1.5 h-1.5 rounded-full sq-glow-pulse sq-delay-200"
              style={{ background: 'var(--color-in-white)' }}
            />
            <div
              className="w-1.5 h-1.5 rounded-full sq-glow-pulse sq-delay-400"
              style={{ background: 'var(--color-in-green)' }}
            />
          </div>
        )}
      </div>

      {/* Pipeline stages — shown while processing */}
      {isProcessing && events.length === 0 && (
        <div className="flex flex-col gap-2">
          {PIPELINE_STAGES.map((s, idx) => {
            const isPast    = idx < activeStage;
            const isCurrent = idx === activeStage;
            return (
              <div
                key={s.id}
                className="flex items-center gap-2.5 transition-all duration-500"
                style={{
                  opacity: isPast ? 0.3 : isCurrent ? 1 : 0.1,
                  transform: isCurrent ? 'translateX(3px)' : 'none',
                }}
              >
                <div
                  className="w-1.5 h-1.5 rounded-full shrink-0 transition-all duration-300"
                  style={{
                    background: isCurrent
                      ? 'var(--color-sq-text)'
                      : isPast
                      ? 'var(--color-sq-border-2)'
                      : 'var(--color-sq-border)',
                    boxShadow: isCurrent ? '0 0 4px rgba(255,255,255,0.4)' : 'none',
                  }}
                />
                <span
                  className="text-[11px] font-mono"
                  style={{ color: isCurrent ? 'var(--color-sq-text)' : 'var(--color-sq-muted)' }}
                >
                  {s.label}{isCurrent ? '...' : ''}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Actual execution events (from backend) */}
      {events.length > 0 && (
        <div className="flex flex-col gap-2">
          {events.map((evt, i) => (
            <div key={i} className="flex items-start gap-2.5 sq-trace-appear text-[11px]">
              <div
                className="w-1.5 h-1.5 mt-1 rounded-full shrink-0"
                style={{
                  background:
                    evt.status === 'FAILED'
                      ? 'var(--color-sq-error)'
                      : 'var(--color-sq-subtle)',
                }}
              />
              <div className="flex flex-col">
                <span
                  className="font-semibold tracking-widest text-[9px] mb-0.5"
                  style={{ color: 'var(--color-sq-subtle)' }}
                >
                  {evt.stage}
                </span>
                <span
                  className="font-mono leading-snug"
                  style={{
                    color:
                      evt.status === 'FAILED'
                        ? 'var(--color-sq-error)'
                        : 'var(--color-sq-muted)',
                  }}
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
