"use client";
import React from "react";
import { useWorkspace } from "../lib/store";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { EvidenceCard } from "./EvidenceCard";
import { ErrorState } from "./ErrorState";

export function AnalysisPanel() {
  const { state, dispatch } = useWorkspace();

  return (
    <div className="flex flex-col w-[350px] h-full shrink-0" style={{ background: "var(--color-sq-surface)", borderLeft: "1px solid var(--color-sq-border)" }}>
      <div className="p-4 border-b" style={{ borderColor: "var(--color-sq-border)" }}>
        <div className="text-[10px] font-bold tracking-widest" style={{ color: "var(--color-sq-muted)" }}>ANALYSIS</div>
      </div>
      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        {state.error && <ErrorState error={state.error} onReset={() => dispatch({ type: "RESET_ANALYSIS" })} />}
        
        {state.phase !== "idle" && (
          <ExecutionTimeline phase={state.phase} events={state.result?.execution_trace || []} />
        )}

        {state.result && (
          <div className="flex flex-col gap-4">
            <div className="p-4 rounded-lg" style={{ background: "var(--color-sq-surface-2)", border: "1px solid var(--color-sq-border)" }}>
              <div className="text-[10px] font-bold tracking-widest mb-2" style={{ color: "var(--color-sq-muted)" }}>ANSWER</div>
              <p className="text-sm" style={{ color: "var(--color-sq-text)" }}>{state.result.summary}</p>
            </div>
            
            {state.result.spatial_evidence && state.result.spatial_evidence.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="text-[10px] font-bold tracking-widest mt-2" style={{ color: "var(--color-sq-muted)" }}>EVIDENCE</div>
                {state.result.spatial_evidence.map((ev, i) => <EvidenceCard key={i} evidence={ev} index={i} />)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
