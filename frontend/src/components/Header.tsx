"use client";
import React, { useEffect, useState } from "react";
import { useWorkspace } from "../lib/store";
import { checkHealth } from "../lib/api";

export function Header() {
  const { state } = useWorkspace();
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth().then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  return (
    <div className="flex items-center justify-between px-4 w-full h-[44px] shrink-0" style={{ borderBottom: "1px solid var(--color-sq-border)", background: "var(--color-sq-bg)" }}>
      <div className="flex items-center gap-2">
        <span className="font-bold tracking-widest text-sm" style={{ color: "var(--color-sq-accent)" }}>SATQUERY</span>
        <span style={{ color: "var(--color-sq-subtle)" }}>|</span>
        <span className="text-xs tracking-wider" style={{ color: "var(--color-sq-muted)" }}>AI</span>
      </div>
      <div className="flex items-center justify-center flex-1">
        {state.workspaceMode !== "EMPTY" && (
          <div className="px-2 py-0.5 text-[10px] font-semibold tracking-wider rounded border" style={{ borderColor: "var(--color-sq-border)", color: "var(--color-sq-text)" }}>
            {state.workspaceMode.replace("_", " ")}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 text-[10px] tracking-wider">
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: online ? "var(--color-sq-ok)" : "var(--color-sq-error)" }} />
        <span style={{ color: online ? "var(--color-sq-ok)" : "var(--color-sq-error)" }}>
          {online === null ? "CHECKING..." : online ? "BACKEND ONLINE" : "BACKEND OFFLINE"}
        </span>
      </div>
    </div>
  );
}
