import type { ImageAsset } from './schema';

export type SceneRole = 'T1' | 'T2' | 'SAR' | 'OPTICAL' | 'UNKNOWN';
export type UploadStatus = 'idle' | 'uploading' | 'validating' | 'ready' | 'error';
export type AnalysisPhase = 'idle' | 'submitting' | 'validating' | 'planning' | 'analyzing' | 'synthesizing' | 'done' | 'failed';
export type WorkspaceMode = 'SINGLE' | 'BITEMPORAL' | 'CROSS_MODAL' | 'SAR_ONLY' | 'EMPTY';
export type ActiveLayer = 'T1' | 'T2' | 'CHANGE' | 'SAR' | 'OPTICAL' | 'FUSION' | 'IMAGE';

export interface SceneState {
  asset: ImageAsset;
  role: SceneRole;
  thumbnailUrl: string | null;
  uploadStatus: UploadStatus;
  uploadError: string | null;
}
