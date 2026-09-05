import React from 'react';

export function ErrorState({ error, onReset }: { error: string; onReset?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 rounded-lg text-center sq-fade-in" style={{ background: 'var(--color-sq-surface-2)', border: '1px solid var(--color-sq-error)' }}>
      <div className="text-3xl mb-2" style={{ color: 'var(--color-sq-error)' }}>⚢</div>
      <div className="text-xs font-bold tracking-widest uppercase mb-4" style={{ color: 'var(--color-sq-error)' }}>ANALYSIS FAILED</div>
      <p className="text-sm mb-2" style={{ color: 'var(--color-sq-text)' }}>{error}</p>
      {onReset && (
        <button onClick={onReset} className="px-4 py-1.5 text-xs font-medium rounded mt-4" style={{ background: 'var(--color-sq-surface-3)', color: 'var(--color-sq-text)', border: '1px solid var(--color-sq-border)' }}>
          Reset workspace
        </button>
      )}
    </div>
  );
}
