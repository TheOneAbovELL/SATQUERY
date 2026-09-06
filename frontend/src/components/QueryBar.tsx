"use client";
import React, { useState } from "react";
import { useWorkspace } from "../lib/store";
import { analyze } from "../lib/api";

const EXAMPLE_QUERIES = [
  "What changed between these two images?",
  "Identify new structures or buildings.",
  "Analyze this SAR scene.",
  "Detect water body changes.",
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
    <div
      className="relative w-full shrink-0 px-6 pb-6 pt-3"
      style={{ background: "transparent" }}
    >
      {/* Gradient fade-up from background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "linear-gradient(to top, var(--color-sq-bg) 60%, transparent 100%)",
        }}
      />

      <div className="relative max-w-3xl mx-auto flex flex-col gap-2.5">
        {/* Example queries (only shown when empty history and not busy) */}
        {state.history.length === 0 && !isBusy && (
          <div className="flex flex-wrap gap-2 justify-center">
            {EXAMPLE_QUERIES.slice(0, 2).map((q) => (
              <button
                key={q}
                onClick={() => setInput(q)}
                className="text-[11px] px-3 py-1.5 rounded-full transition-all hover:border-[var(--color-sq-border-2)]"
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--color-sq-border)",
                  color: "var(--color-sq-subtle)",
                  cursor: "pointer",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Main input row */}
        <div
          className="flex items-center gap-2 p-1.5 rounded-xl transition-all duration-200"
          style={{
            background: "var(--color-sq-surface-2)",
            border: `1px solid ${focused ? "var(--color-sq-border-2)" : "var(--color-sq-border)"}`,
            boxShadow: focused ? "0 0 0 1px rgba(255,255,255,0.05)" : "none",
          }}
        >
          {/* Upload icon */}
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ml-1"
            style={{ color: "var(--color-sq-subtle)" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
          </div>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Ask anything about your satellite imagery..."
            className="flex-1 bg-transparent outline-none text-[14px] font-light placeholder-[var(--color-sq-subtle)]"
            style={{ color: "var(--color-sq-text)", caretColor: "var(--color-in-saffron)" }}
            disabled={isBusy}
          />

          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-[12px] font-semibold tracking-[0.08em] transition-all duration-200 shrink-0"
            style={{
              background: isBusy
                ? "var(--color-sq-surface-3)"
                : canSubmit
                ? "rgba(255,255,255,0.9)"
                : "rgba(255,255,255,0.06)",
              color: isBusy || !canSubmit ? "var(--color-sq-subtle)" : "var(--color-sq-bg)",
              cursor: canSubmit ? "pointer" : "default",
              boxShadow: canSubmit && !isBusy ? "0 2px 12px rgba(255,255,255,0.12)" : "none",
            }}
          >
            {isBusy ? (
              <>
                <div
                  className="w-3 h-3 rounded-full border border-t-transparent animate-spin"
                  style={{ borderColor: "var(--color-sq-subtle) transparent var(--color-sq-subtle) var(--color-sq-subtle)" }}
                />
                <span>Analyzing</span>
              </>
            ) : (
              <>
                <span>Analyze</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </>
            )}
          </button>
        </div>

        {/* Footer note */}
        <div className="text-center">
          <span className="text-[10px] tracking-widest opacity-25 font-light" style={{ color: "var(--color-sq-text)" }}>
            SatQuery AI · Geospatial Intelligence Engine
          </span>
        </div>
      </div>
    </div>
  );
}
