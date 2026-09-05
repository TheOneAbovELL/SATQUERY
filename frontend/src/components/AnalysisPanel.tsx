"use client";
import React, { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useWorkspace } from "../lib/store";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { EvidenceCard } from "./EvidenceCard";
import { ErrorState } from "./ErrorState";

export function AnalysisPanel() {
  const { state, dispatch } = useWorkspace();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [state.history]);

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden" style={{ background: "var(--color-sq-bg)", position: "relative" }}>
      <div className="p-4 border-b shrink-0 backdrop-blur-md z-10" style={{ borderColor: "var(--color-sq-border)", background: "rgba(0,0,0,0.7)" }}>
        <div className="text-xs font-bold tracking-widest text-center" style={{ color: "var(--color-sq-muted)" }}>CONVERSATION</div>
      </div>
      
      <div className="p-6 flex-1 overflow-y-auto space-y-6">
        {state.history.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center opacity-50">
            <p className="text-sm" style={{ color: "var(--color-sq-muted)" }}>Ask a question to start the analysis.</p>
          </div>
        )}

        {state.history.map((item, index) => (
          <div key={item.id} className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* User Query */}
            <div className="flex justify-end">
              <div className="max-w-[85%] p-4 rounded-2xl rounded-tr-sm shadow-md" style={{ background: "var(--color-sq-surface-2)", border: "1px solid var(--color-sq-border)" }}>
                <p className="text-sm" style={{ color: "var(--color-sq-text)" }}>{item.query}</p>
              </div>
            </div>

            {/* Error State */}
            {item.error && <ErrorState error={item.error} onReset={() => dispatch({ type: "RESET_ANALYSIS" })} />}

            {/* Processing State */}
            {item.phase !== "idle" && item.phase !== "done" && item.phase !== "failed" && (
              <div className="flex justify-start max-w-[90%]">
                <ExecutionTimeline phase={item.phase} events={item.result?.execution_trace || []} />
              </div>
            )}

            {/* AI Response */}
            {item.result && (
              <div className="flex justify-start">
                <div className="flex flex-col gap-4 w-full max-w-[95%]">
                  <div className="p-6 rounded-2xl rounded-tl-sm shadow-xl" style={{ background: "var(--color-sq-surface)", border: "1px solid var(--color-sq-border-2)" }}>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-2 h-2 rounded-full" style={{ background: "var(--color-sq-accent)" }}></div>
                      <div className="text-[10px] font-bold tracking-widest" style={{ color: "var(--color-sq-accent)" }}>SATQUERY AI</div>
                    </div>
                    <div className="text-sm prose prose-invert max-w-none space-y-3" style={{ color: "var(--color-sq-text)" }}>
                      <ReactMarkdown
                        components={{
                          p: ({node, ...props}) => <p className="mb-2 leading-relaxed" {...props} />,
                          strong: ({node, ...props}) => <strong className="text-white font-semibold" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                          li: ({node, ...props}) => <li {...props} />,
                          h1: ({node, ...props}) => <h1 className="text-lg font-bold mt-4 mb-2 text-white" {...props} />,
                          h2: ({node, ...props}) => <h2 className="text-base font-bold mt-4 mb-2 text-white" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-3 mb-1 text-white" {...props} />
                        }}
                      >
                        {item.result.summary}
                      </ReactMarkdown>
                    </div>
                  </div>
                  
                  {item.result.spatial_evidence && item.result.spatial_evidence.length > 0 && (
                    <div className="flex flex-col gap-2">
                      <div className="text-[10px] font-bold tracking-widest mt-2" style={{ color: "var(--color-sq-muted)" }}>EVIDENCE MAPS</div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {item.result.spatial_evidence.map((ev, i) => <EvidenceCard key={i} evidence={ev} index={i} />)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
