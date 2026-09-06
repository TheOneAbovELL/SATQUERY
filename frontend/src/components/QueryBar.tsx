"use client";
import React, { useState } from "react";
import { useWorkspace } from "../lib/store";
import { analyze } from "../lib/api";

const EXAMPLE_QUERIES = [
  "What changed between these images?",
  "Identify new structures or buildings.",
  "Analyse this SAR scene.",
  "Describe land use patterns.",
];

export function QueryBar() {
  const { state, dispatch } = useWorkspace();
  const [input, setInput] = useState("");
  const [focused, setFocused] = useState(false);

  const isBusy = ["submitting", "validating", "planning", "analyzing", "synthesizing"].includes(state.phase);
  const canSubmit = !isBusy && input.trim().length > 0;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    const query = input.trim();
    dispatch({ type: "SET_QUERY", payload: query });
    dispatch({ type: "SET_PHASE", payload: "submitting" });
    setInput("");
    try {
      const assetIds = state.scenes.map((s) => s.asset.asset_id);
      const result = await analyze(query, assetIds);
      dispatch({ type: "SET_RESULT", payload: result });
    } catch (e) {
      dispatch({ type: "SET_ERROR", payload: String(e) });
    }
  };

  return (
    <div className="relative w-full shrink-0 px-5 pb-5 pt-2">
      {/* Gradient fade from background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "linear-gradient(to top, var(--color-sq-bg) 55%, transparent 100%)",
        }}
      />

      <div className="relative max-w-2xl mx-auto flex flex-col gap-2">

        {/* Example chips — only when no history */}
        {state.history.length === 0 && !isBusy && (
          <div className="flex flex-wrap gap-1.5 justify-center">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => setInput(q)}
                className="text-[11px] px-3 py-1.5 rounded-full transition-all duration-200"
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.07)',
                  color: 'rgba(255,255,255,0.35)',
                  cursor: 'pointer',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.06)';
                  (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.6)';
                  (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.12)';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.03)';
                  (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.35)';
                  (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.07)';
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input row */}
        <div
          className="flex items-center gap-2 p-1.5 rounded-2xl transition-all duration-300"
          style={{
            background: focused ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.025)',
            border: `1px solid ${focused ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.06)'}`,
            boxShadow: focused ? '0 0 0 3px rgba(255,255,255,0.03), 0 8px 32px rgba(0,0,0,0.4)' : '0 4px 16px rgba(0,0,0,0.2)',
          }}
        >
          {/* Satellite icon */}
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{ color: 'rgba(255,255,255,0.2)' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
          </div>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSubmit()}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Ask anything about your satellite imagery…"
            className="flex-1 bg-transparent outline-none text-[14px] font-light"
            style={{
              color: 'rgba(255,255,255,0.85)',
              caretColor: 'var(--color-in-saffron)',
            }}
            disabled={isBusy}
          />

          {/* Submit button */}
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-[12px] font-semibold tracking-[0.06em] transition-all duration-250 shrink-0"
            style={{
              background: isBusy
                ? 'rgba(255,255,255,0.04)'
                : canSubmit
                ? 'rgba(255,255,255,0.92)'
                : 'rgba(255,255,255,0.05)',
              color: isBusy || !canSubmit ? 'rgba(255,255,255,0.25)' : '#050507',
              cursor: canSubmit ? 'pointer' : 'default',
              boxShadow: canSubmit && !isBusy ? '0 2px 16px rgba(255,255,255,0.15)' : 'none',
              transform: canSubmit && !isBusy ? 'none' : 'none',
              border: 'none',
            }}
            onMouseEnter={e => {
              if (canSubmit && !isBusy) {
                (e.currentTarget as HTMLButtonElement).style.background = '#ffffff';
                (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-1px)';
                (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 4px 20px rgba(255,255,255,0.2)';
              }
            }}
            onMouseLeave={e => {
              if (canSubmit && !isBusy) {
                (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.92)';
                (e.currentTarget as HTMLButtonElement).style.transform = 'none';
                (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 2px 16px rgba(255,255,255,0.15)';
              }
            }}
          >
            {isBusy ? (
              <>
                <div
                  className="w-3 h-3 rounded-full border border-t-transparent animate-spin"
                  style={{ borderColor: 'rgba(255,255,255,0.3) transparent rgba(255,255,255,0.3) rgba(255,255,255,0.3)' }}
                />
                <span>Analyzing</span>
              </>
            ) : (
              <>
                <span>Analyze</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </>
            )}
          </button>
        </div>

        {/* Footer */}
        <div className="text-center">
          <span className="text-[10px] tracking-widest font-light" style={{ color: 'rgba(255,255,255,0.1)' }}>
            SatQuery AI · Geospatial Intelligence
          </span>
        </div>
      </div>
    </div>
  );
}
