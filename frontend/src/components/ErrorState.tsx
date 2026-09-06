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
      className="flex flex-col p-5 rounded-2xl sq-fade-in"
      style={{
        background: 'rgba(239,68,68,0.04)',
        border: '1px solid rgba(239,68,68,0.15)',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-5 h-5 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)' }}
        >
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#ef4444' }} />
        </div>
        <span className="text-[10px] font-semibold tracking-[0.18em]" style={{ color: 'rgba(239,68,68,0.8)' }}>
          ANALYSIS FAILED
        </span>
      </div>
      <p className="text-[13px] font-light mb-4 leading-relaxed" style={{ color: 'rgba(255,255,255,0.5)' }}>
        {error}
      </p>
      {onReset && (
        <button
          onClick={onReset}
          className="self-start px-4 py-2 text-[11px] font-medium rounded-xl transition-all duration-200"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: 'rgba(255,255,255,0.55)',
            cursor: 'pointer',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.07)';
            (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.8)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.04)';
            (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.55)';
          }}
        >
          Reset workspace
        </button>
      )}
    </div>
  );
}
