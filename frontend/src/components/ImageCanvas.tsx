"use client";
import React, { useState } from 'react';
import { useWorkspace } from '../lib/store';

export function ImageCanvas() {
  const { state } = useWorkspace();
  const [zoom, setZoom] = useState(1);

  const MODALITY_COLOR: Record<string, string> = {
    SAR: 'var(--color-sq-sar)',
    Optical: 'var(--color-sq-optical)',
    RGB: 'var(--color-sq-optical)',
    Multispectral: 'var(--color-sq-fusion)',
  };

  if (state.workspaceMode === 'EMPTY') {
    return (
      <div
        className="flex-1 flex flex-col items-center justify-center sq-scanlines relative"
        style={{ background: 'var(--color-sq-bg)' }}
      >
        {/* Subtle radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage:
              'radial-gradient(ellipse 60% 40% at 50% 60%, rgba(255,255,255,0.03) 0%, transparent 70%)',
          }}
        />
        <div className="relative flex flex-col items-center gap-5 text-center px-6">
          {/* Tricolor dots */}
          <div className="flex gap-1.5 mb-1">
            <div className="w-1.5 h-1.5 rounded-full sq-glow-pulse" style={{ background: 'var(--color-in-saffron)', opacity: 0.5 }} />
            <div className="w-1.5 h-1.5 rounded-full sq-glow-pulse sq-delay-300" style={{ background: 'var(--color-in-white)', opacity: 0.5 }} />
            <div className="w-1.5 h-1.5 rounded-full sq-glow-pulse sq-delay-600" style={{ background: 'var(--color-in-green)', opacity: 0.5 }} />
          </div>
          <div
            className="text-[10px] tracking-[0.3em] font-medium uppercase"
            style={{ color: 'var(--color-sq-subtle)' }}
          >
            Awaiting Imagery
          </div>
          <div className="text-[11px] font-light" style={{ color: 'var(--color-sq-border-2)' }}>
            Upload imagery on the left panel
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex-1 relative overflow-hidden sq-scanlines group"
      style={{ background: 'var(--color-sq-bg)' }}
    >
      {/* Top bar overlay */}
      <div
        className="absolute top-0 left-0 w-full z-10 pointer-events-none"
        style={{
          padding: '16px 20px 40px',
          background: 'linear-gradient(to bottom, rgba(5,5,7,0.8) 0%, transparent 100%)',
        }}
      >
        <div className="pointer-events-auto inline-flex">
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full backdrop-blur-md"
            style={{
              background: 'rgba(0,0,0,0.5)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: MODALITY_COLOR[state.scenes[0]?.asset.modality] || 'var(--color-sq-muted)' }}
            />
            <span
              className="text-[10px] font-semibold tracking-[0.18em]"
              style={{ color: 'rgba(255,255,255,0.7)' }}
            >
              {state.workspaceMode.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>

      {/* Imagery */}
      <div className="absolute inset-0 flex items-center justify-center p-10">
        <div
          style={{
            transform: `scale(${zoom})`,
            transition: 'transform 0.35s cubic-bezier(0.2, 0, 0, 1)',
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}
        >
          {state.scenes.map((scene, i) => (
            <div
              key={scene.asset.asset_id}
              className="relative shadow-2xl overflow-hidden"
              style={{
                flex: state.scenes.length > 1 ? 1 : 'none',
                minWidth: 0,
                maxWidth: '100%',
                maxHeight: '100%',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '4px',
              }}
            >
              {/* T1 / T2 badge */}
              <div
                className="absolute top-2.5 left-2.5 z-10 px-2 py-0.5 rounded text-[9px] tracking-widest font-bold"
                style={{
                  background: 'rgba(0,0,0,0.55)',
                  color: 'rgba(255,255,255,0.7)',
                  backdropFilter: 'blur(4px)',
                }}
              >
                {scene.role}
              </div>
              <img
                src={scene.thumbnailUrl || ''}
                className="w-full h-full object-contain"
                style={{ background: 'var(--color-sq-surface-2)', display: 'block' }}
                alt={`Scene ${i + 1}`}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Zoom controls — appear on hover */}
      <div
        className="absolute bottom-6 right-6 flex flex-col gap-0.5 shadow-2xl backdrop-blur-lg overflow-hidden opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: 'rgba(0,0,0,0.55)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '8px',
        }}
      >
        <button
          onClick={() => setZoom((z) => z * 1.25)}
          className="w-8 h-8 flex items-center justify-center hover:bg-white/10 transition-colors"
          style={{ color: 'rgba(255,255,255,0.6)' }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>
        <div className="h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
        <button
          onClick={() => setZoom((z) => z / 1.25)}
          className="w-8 h-8 flex items-center justify-center hover:bg-white/10 transition-colors"
          style={{ color: 'rgba(255,255,255,0.6)' }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
        </button>
        <div className="h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
        <button
          onClick={() => setZoom(1)}
          className="w-8 h-7 flex items-center justify-center text-[8px] font-bold tracking-widest hover:bg-white/10 transition-colors"
          style={{ color: 'rgba(255,255,255,0.5)' }}
        >
          FIT
        </button>
      </div>
    </div>
  );
}
