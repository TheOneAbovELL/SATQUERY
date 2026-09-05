import type { ImageAsset, AnalysisResult } from '../types/schema';

const getApiBase = () => process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${getApiBase()}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function uploadAsset(file: File, role: string): Promise<ImageAsset> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('role', role);
  
  const res = await fetch(`${getApiBase()}/api/v1/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ? JSON.stringify(err.detail) : `Upload failed: ${res.status}`);
  }
  return res.json();
}

export function getThumbnailUrl(assetId: string): string {
  return `${getApiBase()}/api/v1/assets/${assetId}/thumbnail`;
}

export async function analyze(query: string, assetIds: string[]): Promise<AnalysisResult> {
  const res = await fetch(`${getApiBase()}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, asset_ids: assetIds })
  });
  
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ? JSON.stringify(err.detail) : `Analysis failed: ${res.status}`);
  }
  return res.json();
}
