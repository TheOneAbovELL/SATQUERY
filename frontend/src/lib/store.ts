import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import type { AnalysisResult } from '../types/schema';
import type { SceneState, WorkspaceMode, AnalysisPhase, ActiveLayer } from '../types/satquery';

interface WorkspaceState {
  scenes: SceneState[];
  workspaceMode: WorkspaceMode;
  query: string;
  phase: AnalysisPhase;
  result: AnalysisResult | null;
  error: string | null;
  activeLayer: ActiveLayer;
  sidebarOpen: boolean;
  traceDrawerOpen: boolean;
}

type Action =
  | { type: 'ADD_SCENE'; payload: SceneState }
  | { type: 'REMOVE_SCENE'; payload: string }
  | { type: 'SET_QUERY'; payload: string }
  | { type: 'SET_PHASE'; payload: AnalysisPhase }
  | { type: 'SET_RESULT'; payload: AnalysisResult }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SET_ACTIVE_LAYER'; payload: ActiveLayer }
  | { type: 'RESET_ANALYSIS' };

const initialState: WorkspaceState = {
  scenes: [],
  workspaceMode: 'EMPTY',
  query: '',
  phase: 'idle',
  result: null,
  error: null,
  activeLayer: 'IMAGE',
  sidebarOpen: true,
  traceDrawerOpen: false
};

function deriveWorkspaceMode(scenes: SceneState[]): WorkspaceMode {
  if (scenes.length === 0) return 'EMPTY';
  if (scenes.length === 1) return scenes[0].asset.modality === 'SAR' ? 'SAR_ONLY' : 'SINGLE';
  
  const modalities = scenes.map(s => s.asset.modality as string);
  const hasSar = modalities.includes('SAR');
  const hasOptical = modalities.includes('Optical') || modalities.includes('RGB') || modalities.includes('Multispectral');
  
  if (scenes.length >= 2) {
    if (hasSar && hasOptical) return 'CROSS_MODAL';
    return 'BITEMPORAL';
  }
  return 'SINGLE';
}

function workspaceReducer(state: WorkspaceState, action: Action): WorkspaceState {
  switch (action.type) {
    case 'ADD_SCENE': {
      const newScenes = [...state.scenes, action.payload];
      return { ...state, scenes: newScenes, workspaceMode: deriveWorkspaceMode(newScenes) };
    }
    case 'REMOVE_SCENE': {
      const newScenes = state.scenes.filter(s => s.asset.asset_id !== action.payload);
      return { ...state, scenes: newScenes, workspaceMode: deriveWorkspaceMode(newScenes) };
    }
    case 'SET_QUERY': return { ...state, query: action.payload };
    case 'SET_PHASE': return { ...state, phase: action.payload };
    case 'SET_RESULT': return { ...state, result: action.payload, phase: 'done', error: null };
    case 'SET_ERROR': return { ...state, error: action.payload, phase: 'failed' };
    case 'SET_ACTIVE_LAYER': return { ...state, activeLayer: action.payload };
    case 'RESET_ANALYSIS': return { ...state, result: null, error: null, phase: 'idle' };
    default: return state;
  }
}

const WorkspaceContext = createContext<{state: WorkspaceState, dispatch: React.Dispatch<Action>} | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(workspaceReducer, initialState);
  return React.createElement(WorkspaceContext.Provider, { value: { state, dispatch } }, children);
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error('useWorkspace must be used within a WorkspaceProvider');
  return context;
}
