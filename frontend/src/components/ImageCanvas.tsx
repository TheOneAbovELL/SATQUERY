"use client";
import React, { useState } from 'react';
import { useWorkspace } from '../lib/store';

const MODALITY_COLOR: Record<string, string> = {
  SAR: 'var(--color-sq-sar)',
  Optical: 'var(--color-sq-optical)',
  RGB: 'var(--color-sq-optical)',
  Multispectral: 'var(--color-sq-fusion)',
};

export function ImageCanvas() {
  const { state } = useWorkspace();
  const [zoom, setZoom] = useState(1);

  if (state.workspaceMode === 'EMPTY') {
    return (
      <div
        className="flex-1 flex flex-col items-center justify-center relative sq-scanlines"
        style={{ background: 'var(--color-sq-bg)' }}
      >
        {/* Subtle radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 60% 50% at 50% 65%, rgba(255,255,255,0.018) 0%, transparent 70%)',
          }}
        />
        <div className="relative flex flex-col items-center gap-4 text-center px-8">
          <div className="flex gap-2 mb-1">
            {[
              { c: 'var(--color-in-saffron)', d: '0ms' },
              { c: 'var(--color-in-white)', d: '350ms' },
              { c: 'var(--color-in-green)', d: '700ms' },
            ].map((dot, i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full sq-glow-pulse"
                style={{ background: dot.c, opacity: 0.4, animationDelay: dot.d }}
              />
            ))}
          </div>
          <div className="text-[10px] tracking-[0.3em] uppercase font-medium" style={{ color: 'rgba(255,255,255,0.2)' }}>
            Awaiting Imagery
          </div>
          <div className="text-[11px] font-light" style={{ color: 'rgba(255,255,255,0.1)' }}>
            Upload via the left panel
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
      {/* Modality badge */}
      <div
        className="absolute top-4 left-4 z-10"
        style={{ pointerEvents: 'none' }}
      >
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full"
          style={{
            background: 'rgba(0,0,0,0.45)',
            border: '1px solid rgba(255,255,255,0.07)',
            backdropFilter: 'blur(8px)',
          }}
        >
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: MODALITY_COLOR[state.scenes[0]?.asset.modality] || 'rgba(255,255,255,0.3)' }}
          />
          <span className="text-[10px] font-semibold tracking-[0.14em]" style={{ color: 'rgba(255,255,255,0.6)' }}>
            {state.workspaceMode.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Image(s) */}
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
            gap: '10px',
          }}
        >
          {state.scenes.map((scene, i) => (
            <div
              key={scene.asset.asset_id}
              className="relative overflow-hidden"
              style={{
                flex: state.scenes.length > 1 ? 1 : 'none',
                minWidth: 0,
                maxWidth: '100%',
                maxHeight: '100%',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '12px',
                boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
              }}
            >
              {/* Role badge */}
              <div
                className="absolute top-2.5 left-2.5 z-10 px-2 py-0.5 rounded-full text-[9px] tracking-widest font-bold"
                style={{
                  background: 'rgba(0,0,0,0.55)',
                  color: 'rgba(255,255,255,0.65)',
                  backdropFilter: 'blur(4px)',
                }}
              >
                {scene.role}
              </div>
              <img
                src={scene.thumbnailUrl || ''}
                className="w-full h-full object-contain block"
                style={{ background: 'var(--color-sq-surface-2)', borderRadius: '11px' }}
                alt={`Scene ${i + 1}`}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Zoom controls — reveal on hover */}
      <div
        className="absolute bottom-5 right-5 overflow-hidden opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col gap-px"
        style={{
          background: 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '12px',
          backdropFilter: 'blur(12px)',
        }}
      >
        {[
          {
            label: '+',
            title: 'Zoom in',
            onClick: () => setZoom(z => z * 1.25),
            icon: (
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            ),
          },
          {
            label: '−',
            title: 'Zoom out',
            onClick: () => setZoom(z => z / 1.25),
            icon: (
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            ),
          },
        ].map((btn, i, arr) => (
          <button
            key={btn.label}
            onClick={btn.onClick}
            title={btn.title}
            className="w-8 h-8 flex items-center justify-center transition-colors duration-150"
            style={{
              color: 'rgba(255,255,255,0.55)',
              background: 'transparent',
              border: 'none',
              borderBottom: i < arr.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
              cursor: 'pointer',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.08)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            {btn.icon}
          </button>
        ))}
        <button
          onClick={() => setZoom(1)}
          className="w-8 h-7 flex items-center justify-center transition-colors duration-150"
          style={{
            color: 'rgba(255,255,255,0.35)',
            fontSize: '8px',
            letterSpacing: '0.1em',
            fontWeight: 700,
            background: 'transparent',
            border: 'none',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            cursor: 'pointer',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          FIT
        </button>
      </div>
    </div>
  );
}
