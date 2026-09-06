import React from 'react';

export function ErrorState({
  error,
  onReset,
}: {
  error: string;
  onReset?: () => void;
}) {
  return (
    <div
      className="flex flex-col p-6 rounded-xl sq-fade-in"
      style={{
        background: 'rgba(239,68,68,0.05)',
        border: '1px solid rgba(239,68,68,0.2)',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-sq-error)' }} />
        <span className="text-[10px] font-semibold tracking-[0.2em]" style={{ color: 'var(--color-sq-error)' }}>
          ANALYSIS FAILED
        </span>
      </div>
      <p className="text-[13px] font-light mb-4" style={{ color: 'var(--color-sq-muted)' }}>
        {error}
      </p>
      {onReset && (
        <button
          onClick={onReset}
          className="self-start px-4 py-2 text-[11px] font-medium rounded-lg transition-colors"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--color-sq-border-2)',
            color: 'var(--color-sq-text)',
            cursor: 'pointer',
          }}
        >
          Reset workspace
        </button>
      )}
    </div>
  );
}
