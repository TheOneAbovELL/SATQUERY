"use client";
import React, { useState } from 'react';
import { useWorkspace } from '../lib/store';

export function ImageCanvas() {
  const { state } = useWorkspace();
  const [zoom, setZoom] = useState(1);

  if (state.workspaceMode === 'EMPTY') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center sq-scanlines" 	           style={{ background: 'var(--color-sq-bg)' }}>
        <div className="text-4xl mb-4">✐</div>
        <div className="text-lg font-medium mb-2" style={{ color: 'var(--color-sq-text)' }}>SATQUERY WORKSPACE</div>
        <div className="text-sm" style={{ color: 'var(--color-sq-muted)' }}>Upload imagery to begin analysis</div>
      </div>
    );
  }

  const activeScene = state.scenes[0];

  return (
    <div className="flex-1 relative overflow-hidden sq-scanlines" style={{ background: 'var(--color-sq-bg)' }}>
      <div className="absolute top-0 w-full h-12 flex items-center justify-center z-10">
        <div className="flex gap-2 p-1 rounded-mg backdrop-blur-sm" style={{ background: 'rgba(13, 22, 38, 0.8)', border: '1px solid var(--color-sq-border)' }}>
          <button className="px-4 py-1 rounded text-xs font-bold tracking-widest" style={{ background: 'var(--color-sq-accent)', color: 'var(--color-sq-bg)' }}>IMAGE</button>
        </div>
      </div>

      <div className="absolute inset-0 flex items-center justify-center">
        <div style={{ transform: `scale(${zoom})`, transition: 'transform 0.2s ease-out' }}>
          <img src={activeScene?.thumbnailUrl || ''} className="max-w-full max-h-full object-contain" alt="Scene" />
        </div>
      </div>

      <div className="absolute bottom-4 right-4 flex flex-col gap-1">
        <button onClick={() => setZoom(z => z * 1.2)} className="w-8 h-8 rounded font-bold" style={{ background: 'var(--color-sq-surface-2)', border: '1px solid var(--color-sq-border)', color: 'var(--color-sq-text)' }}>+</button>
        <button onClick={() => setZoom(z => z / 1.2)} className="w-8 h-8 rounded font-bold" style={{ background: 'var(--color-sq-surface-2)', border: '1px solid var(--color-sq-border)', color: 'var(--color-sq-text)' }}>-</button>
        <button onClick={() => setZoom(1)} className="w-8 h-8 rounded font-bold" style={{ background: 'var(--color-sq-surface-2)', border: '1px solid var(--color-sq-border)', color: 'var(--color-sq-text)' }}>▣</button>
      </div>
    </div>
  );
}
