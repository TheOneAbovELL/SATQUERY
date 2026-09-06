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
    // After exit animation (500ms), show workspace
    setTimeout(() => {
      setAppState("workspace");
    }, 480);
  }, []);

  return (
    <WorkspaceProvider>
      {/* Landing overlay — rendered on top until dismissed */}
      {appState !== "workspace" && (
        <LandingHero onEnter={handleEnter} isExiting={appState === "exiting"} />
      )}

      {/* Workspace — always mounted, revealed after transition */}
      <div
        className={`flex flex-col w-full h-full overflow-hidden ${
          appState === "workspace" ? "sq-workspace-enter" : "opacity-0 pointer-events-none"
        }`}
        style={{ background: "var(--color-sq-bg)" }}
      >
        <Header />
        <div className="flex flex-1 overflow-hidden">
          <ScenePanel />
          <div className="flex flex-col flex-1 overflow-hidden relative">
            <AnalysisPanel />
            <QueryBar />
          </div>
          <div
            className="w-[440px] shrink-0 border-l flex flex-col"
            style={{ borderColor: "var(--color-sq-border)" }}
          >
            <ImageCanvas />
          </div>
        </div>
      </div>
    </WorkspaceProvider>
  );
}
