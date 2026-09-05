"use client";
import React from "react";
import { Header } from "../components/Header";
import { ScenePanel } from "../components/ScenePanel";
import { ImageCanvas } from "../components/ImageCanvas";
import { QueryBar } from "../components/QueryBar";
import { AnalysisPanel } from "../components/AnalysisPanel";
import { WorkspaceProvider } from "../lib/store";

export default function SatQueryAI() {
  return (
    <WorkspaceProvider>
      <div className="flex flex-col w-full h-full overflow-hidden" style={{ background: "var(--color-sq-bg)" }}>
        <Header />
        <div className="flex flex-1 overflow-hidden">
          <ScenePanel />
          <div className="flex flex-col flex-1 overflow-hidden relative">
            <AnalysisPanel />
            <QueryBar />
          </div>
          <div className="w-[450px] shrink-0 border-l flex flex-col" style={{ borderColor: "var(--color-sq-border)" }}>
            <ImageCanvas />
          </div>
        </div>
      </div>
    </WorkspaceProvider>
  );
}
