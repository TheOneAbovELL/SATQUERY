"use client";
import React, { useEffect, useState } from "react";
import { useWorkspace } from "../lib/store";
import { checkHealth } from "../lib/api";

const MODE_LABELS: Record<string, string> = {
  EMPTY: '',
  SINGLE: 'SINGLE IMAGE',
  BITEMPORAL: 'BI-TEMPORAL',
  SAR_ONLY: 'SAR MODE',
  CROSS_MODAL: 'CROSS-MODAL',
};

const MODE_COLORS: Record<string, string> = {
  SINGLE: 'var(--color-sq-optical)',
  BITEMPORAL: 'var(--color-sq-change)',
  SAR_ONLY: 'var(--color-sq-sar)',
  CROSS_MODAL: 'var(--color-sq-fusion)',
};

export function Header() {
  const { state } = useWorkspace();
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
  }, []);

  const mode = state.workspaceMode;
  const modeLabel = MODE_LABELS[mode] || '';
  const modeColor = MODE_COLORS[mode] || 'var(--color-sq-muted)';

  return (
    <div
      className="relative flex items-center justify-between px-6 w-full shrink-0"
      style={{
        height: '48px',
        background: 'rgba(5,5,7,0.92)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {/* Tricolor top accent — 1px, soft */}
      <div
        className="absolute top-0 left-0 w-full h-[1px] sq-tricolor-line pointer-events-none"
        style={{ opacity: 0.18 }}
      />

      {/* Left: Wordmark */}
      <div className="flex items-center gap-2.5">
        <div
          className="w-2 h-2 rounded-sm"
          style={{ background: 'linear-gradient(135deg, #FF9933 0%, #F4F4F2 50%, #138808 100%)' }}
        />
        <span className="text-[13px] font-bold tracking-[0.2em]" style={{ color: 'var(--color-sq-text)' }}>
          SATQUERY
        </span>
        <span className="text-[11px] font-light tracking-[0.1em]" style={{ color: 'rgba(255,255,255,0.2)' }}>
          AI
        </span>
      </div>

      {/* Center: Mode badge */}
      <div className="absolute left-1/2 -translate-x-1/2">
        {modeLabel && (
          <div
            className="flex items-center gap-2 px-4 py-1 rounded-full"
            style={{
              background: 'rgba(255,255,255,0.035)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: modeColor, boxShadow: `0 0 6px ${modeColor}` }}
            />
            <span className="text-[10px] font-semibold tracking-[0.14em]" style={{ color: 'rgba(255,255,255,0.6)' }}>
              {modeLabel}
            </span>
          </div>
        )}
      </div>

      {/* Right: System status */}
      <div className="flex items-center gap-2">
        <div
          className="w-1.5 h-1.5 rounded-full transition-all duration-500"
          style={{
            background: online ? '#22c55e' : online === false ? '#ef4444' : '#484855',
            boxShadow: online ? '0 0 5px rgba(34,197,94,0.6)' : 'none',
          }}
        />
        <span className="text-[10px] font-mono tracking-[0.1em]" style={{ color: 'rgba(255,255,255,0.25)' }}>
          {online === null ? 'CHECKING' : online ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>
    </div>
  );
}
