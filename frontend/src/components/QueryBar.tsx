"use client";
import React, { useState } from "react";
import { useWorkspace } from "../lib/store";
import { analyze } from "../lib/api";

export function QueryBar() {
  const { state, dispatch } = useWorkspace();
  const [input, setInput] = useState("");

  const handleSubmit = async () => {
    if (!input.trim() || state.phase !== "idle") return;
    dispatch({ type: "SET_QUERY", payload: input });
    dispatch({ type: "SET_PHASE", payload: "submitting" });
    try {
      const assetIds = state.scenes.map(s => s.asset.asset_id);
      const result = await analyze(input, assetIds);
      dispatch({ type: "SET_RESULT", payload: result });
    } catch (e) {
      dispatch({ type: "SET_ERROR", payload: String(e) });
    }
  };

  return (
    <div className="w-full p-4 shrink-0" style={{ background: "var(--color-sq-surface)", borderTop: "1px solid var(--color-sq-border)" }}>
      <div className="max-w-4xl mx-auto flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Ask SatQuery anything about this scene..."
          className="flex-1 px-4 py-3 rounded-lg text-sm outline-none"
          style={{ background: "var(--color-sq-surface-2)", border: "1px solid var(--color-sq-border)", color: "var(--color-sq-text)" }}
          disabled={state.phase !== "idle"}
        />
        <button
          onClick={handleSubmit}
          disabled={state.phase !== "idle"}
          className="px-6 py-3 rounded-lg text-sm font-bold transition-colors"
          style={{ background: state.phase !== "idle" ? "var(--color-sq-border-2)" : "var(--color-sq-accent)", color: "var(--color-sq-bg)" }}
        >
          {state.phase !== "idle" ? "ANALYZING..." : "ANALYZE"}
        </button>
      </div>
    </div>
  );
}
