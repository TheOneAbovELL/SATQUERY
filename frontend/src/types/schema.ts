export type AssetFormat = "GeoTIFF" | "TIFF" | "PNG" | "JPEG" | "UNKNOWN";
export type AssetModality = "Optical" | "Multispectral" | "SAR" | "UNKNOWN";

export interface BoundingBox {
  min_x: number;
  min_y: number;
  max_x: number;
  max_y: number;
}

export interface ImageAsset {
  asset_id: string;
  filename: string;
  mime_type: string;
  format: AssetFormat;
  dimensions?: [number, number];
  band_count?: number;
  modality: AssetModality;
  sensor?: string;
  acquisition_time?: string;
  crs?: string;
  geospatial_bounds?: BoundingBox;
  pixel_resolution?: [number, number];
  metadata: Record<string, any>;
  storage_location: string;
  validation_state: string;
}

export interface ExecutionTraceEvent {
  event_id: string;
  timestamp: string;
  stage: string;
  action: string;
  tool_or_model?: string;
  status: string;
  parameters: Record<string, any>;
  warnings: string[];
}

export interface AnalysisResult {
  analysis_id: string;
  task: string;
  status: string;
  summary: string;
  claims: string[];
  metrics: Record<string, number>;
  spatial_evidence: Record<string, any>[];
  visual_evidence: string[];
  model_evidence: string[];
  provenance: string[];
  confidence: Record<string, number>;
  warnings: string[];
  errors: string[];
  execution_trace: ExecutionTraceEvent[];
}
