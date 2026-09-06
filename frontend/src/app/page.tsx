"use client";
import React, { useState, useCallback } from "react";
import { Header } from "../components/Header";
import { ScenePanel } from "../components/ScenePanel";
import { ImageCanvas } from "../components/ImageCanvas";
import { QueryBar } from "../components/QueryBar";
import { AnalysisPanel } from "../components/AnalysisPanel";
import { LandingHero } from "../components/LandingHero";
import { WorkspaceProvider } from "../lib/store";

export default function SatQueryAI() {
  const [appState, setAppState] = useState<"landing" | "exiting" | "workspace">("landing");

  const handleEnter = useCallback(() => {
    setAppState("exiting");
    setTimeout(() => setAppState("workspace"), 480);
  }, []);

  return (
    <WorkspaceProvider>
      {appState !== "workspace" && (
        <LandingHero onEnter={handleEnter} isExiting={appState === "exiting"} />
      )}

      <div
        className={`flex flex-col w-full h-full overflow-hidden ${
          appState === "workspace" ? "sq-workspace-enter" : "opacity-0 pointer-events-none"
        }`}
        style={{ background: "var(--color-sq-bg)" }}
      >
        <Header />

        {/* Main workspace — no hard grid borders, panels float with subtle separators */}
        <div className="flex flex-1 overflow-hidden">
          <ScenePanel />

          {/* Centre column */}
          <div
            className="flex flex-col flex-1 overflow-hidden relative"
            style={{
              borderLeft: "1px solid rgba(255,255,255,0.04)",
              borderRight: "1px solid rgba(255,255,255,0.04)",
            }}
          >
            <AnalysisPanel />
            <QueryBar />
          </div>

          {/* Right imagery column */}
          <div className="w-[420px] shrink-0 flex flex-col">
            <ImageCanvas />
          </div>
        </div>
      </div>
    </WorkspaceProvider>
  );
}
