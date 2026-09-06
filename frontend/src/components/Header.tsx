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
        borderBottom: '1px solid var(--color-sq-border)',
        background: 'rgba(5,5,7,0.95)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
      }}
    >
      {/* Tricolor top accent — 1px, 25% opacity */}
      <div
        className="absolute top-0 left-0 w-full h-[1px] sq-tricolor-line pointer-events-none"
        style={{ opacity: 0.22 }}
      />

      {/* Left: Wordmark */}
      <div className="flex items-center gap-2.5">
        {/* Tricolor logo mark */}
        <div
          className="w-2 h-2 rounded-sm"
          style={{ background: 'linear-gradient(135deg, #FF9933 0%, #F4F4F2 50%, #138808 100%)' }}
        />
        <span className="text-sm font-bold tracking-[0.22em]" style={{ color: 'var(--color-sq-text)' }}>
          SATQUERY
        </span>
        <span className="text-xs font-light tracking-[0.1em]" style={{ color: 'var(--color-sq-subtle)' }}>
          AI
        </span>
      </div>

      {/* Center: Workspace mode badge */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center">
        {modeLabel && (
          <div
            className="flex items-center gap-1.5 px-3 py-1 rounded-full border"
            style={{
              borderColor: 'var(--color-sq-border-2)',
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: modeColor }} />
            <span className="text-[10px] font-semibold tracking-[0.15em]" style={{ color: 'var(--color-sq-muted)' }}>
              {modeLabel}
            </span>
          </div>
        )}
      </div>

      {/* Right: System status */}
      <div className="flex items-center gap-2">
        <div
          className="w-1.5 h-1.5 rounded-full"
          style={{
            background: online ? 'var(--color-sq-ok)' : online === false ? 'var(--color-sq-error)' : 'var(--color-sq-subtle)',
            boxShadow: online ? '0 0 4px var(--color-sq-ok)' : 'none',
          }}
        />
        <span
          className="text-[10px] font-mono tracking-[0.12em]"
          style={{ color: online === false ? 'var(--color-sq-error)' : 'var(--color-sq-subtle)' }}
        >
          {online === null ? 'CHECKING' : online ? 'SYSTEM ONLINE' : 'BACKEND OFFLINE'}
        </span>
      </div>
    </div>
  );
}
