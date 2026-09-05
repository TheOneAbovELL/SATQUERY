"use client";
import React, { useState } from 'react';
import { useWorkspace } from '../lib/store';

export function ImageCanvas() {
  const { state } = useWorkspace();
  const [zoom, setZoom] = useState(1);

  if (state.workspaceMode === 'EMPTY') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center sq-scanlines" 	           style={{ background: 'var(--color-sq-bg)' }}>
        <div className="text-4xl mb-4">🌍</div>
        <div className="text-lg font-medium mb-2" style={{ color: 'var(--color-sq-text)' }}>SATQUERY WORKSPACE</div>
        <div className="text-sm" style={{ color: 'var(--color-sq-muted)' }}>Upload imagery to begin analysis</div>
      </div>
    );
  }

  const activeScene = state.scenes[0];

  return (
    <div className="flex-1 relative overflow-hidden sq-scanlines" style={{ background: 'var(--color-sq-bg)' }}>
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <div className="flex gap-2 p-1 rounded-md backdrop-blur-md shadow-lg" style={{ background: 'rgba(13, 22, 38, 0.7)', border: '1px solid var(--color-sq-border)' }}>
          <button className="px-4 py-1.5 rounded text-xs font-bold tracking-widest shadow" style={{ background: 'var(--color-sq-accent)', color: 'var(--color-sq-bg)' }}>
            {state.workspaceMode.replace('_', ' ')}
          </button>
        </div>
      </div>

      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div style={{ transform: `scale(${zoom})`, transition: 'transform 0.2s ease-out', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          {state.scenes.map((scene, i) => (
            <img 
              key={scene.asset.asset_id} 
              src={scene.thumbnailUrl || ''} 
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl border border-[var(--color-sq-border)]" 
              style={{ background: 'var(--color-sq-surface-2)', flex: state.scenes.length > 1 ? 1 : 'none', minWidth: 0 }} 
              alt={`Scene ${i + 1}`} 
            />
          ))}
        </div>
      </div>

      <div className="absolute bottom-6 right-6 flex flex-col gap-2 shadow-lg backdrop-blur-md rounded-lg p-1" style={{ background: 'rgba(13, 22, 38, 0.7)', border: '1px solid var(--color-sq-border)' }}>
        <button onClick={() => setZoom(z => z * 1.2)} className="w-10 h-10 rounded font-bold hover:bg-white/10 transition-colors" style={{ color: 'var(--color-sq-text)' }}>+</button>
        <button onClick={() => setZoom(z => z / 1.2)} className="w-10 h-10 rounded font-bold hover:bg-white/10 transition-colors" style={{ color: 'var(--color-sq-text)' }}>-</button>
        <button onClick={() => setZoom(1)} className="w-10 h-10 rounded font-bold hover:bg-white/10 transition-colors text-xs" style={{ color: 'var(--color-sq-text)' }}>FIT</button>
      </div>
    </div>
  );
}
