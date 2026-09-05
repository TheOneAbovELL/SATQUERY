import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import type { AnalysisResult } from '../types/schema';
import type { SceneState, WorkspaceMode, AnalysisPhase, ActiveLayer } from '../types/satquery';

interface ConversationItem {
  id: string;
  query: string;
  result: AnalysisResult | null;
  phase: AnalysisPhase;
  error: string | null;
}

interface WorkspaceState {
  scenes: SceneState[];
  workspaceMode: WorkspaceMode;
  query: string;
  phase: AnalysisPhase;
  history: ConversationItem[]; // NEW: Conversation history
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
  history: [], // Initialize history
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
    case 'SET_QUERY': {
      // When a new query is set, we also add a placeholder to history
      const newItem = { id: Date.now().toString(), query: action.payload, result: null, phase: 'submitting' as AnalysisPhase, error: null };
      return { ...state, query: action.payload, history: [...state.history, newItem] };
    }
    case 'SET_PHASE': {
      if (state.history.length > 0) {
        const h = [...state.history];
        h[h.length - 1].phase = action.payload;
        return { ...state, phase: action.payload, history: h };
      }
      return { ...state, phase: action.payload };
    }
    case 'SET_RESULT': {
      if (state.history.length > 0) {
        const h = [...state.history];
        h[h.length - 1].result = action.payload;
        h[h.length - 1].phase = 'done';
        return { ...state, result: action.payload, phase: 'done', error: null, history: h };
      }
      return { ...state, result: action.payload, phase: 'done', error: null };
    }
    case 'SET_ERROR': {
      if (state.history.length > 0) {
        const h = [...state.history];
        h[h.length - 1].error = action.payload;
        h[h.length - 1].phase = 'failed';
        return { ...state, error: action.payload, phase: 'failed', history: h };
      }
      return { ...state, error: action.payload, phase: 'failed' };
    }
    case 'SET_ACTIVE_LAYER': return { ...state, activeLayer: action.payload };
    case 'RESET_ANALYSIS': return { ...state, result: null, error: null, phase: 'idle', history: [] };
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
