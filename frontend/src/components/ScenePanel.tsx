"use client";
import React, { useRef, useState } from 'react';
import { useWorkspace } from '../lib/store';
import { uploadAsset, getThumbnailUrl } from '../lib/api';

export function ScenePanel() {
  const { state, dispatch } = useWorkspace();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleFile = async (file: File) => {
    setUploading(true);
    try {
      const asset = await uploadAsset(file, 'T1');
      dispatch({
        type: 'ADD_SCENE',
        payload: {
          asset,
          role: 'T1',
          thumbnailUrl: getThumbnailUrl(asset.asset_id),
          uploadStatus: 'ready',
          uploadError: null,
        },
      });
    } catch (e) {
      console.error(e);
      alert('Upload failed: ' + String(e));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      className="flex flex-col h-full shrink-0"
      style={{
        width: '252px',
        background: 'rgba(10,10,13,0.7)',
      }}
    >
      {/* Panel title */}
      <div
        className="flex items-center px-5 py-4"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.045)' }}
      >
        <span className="sq-label">Imagery</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-5">

        {/* Upload zone */}
        <div
          className="flex flex-col items-center justify-center p-5 rounded-2xl cursor-pointer transition-all duration-400"
          style={{
            border: `1.5px dashed ${isDragging ? 'rgba(255,153,51,0.55)' : 'rgba(255,255,255,0.1)'}`,
            background: isDragging
              ? 'rgba(255,153,51,0.04)'
              : 'rgba(255,255,255,0.02)',
            transform: isDragging ? 'scale(0.985)' : 'scale(1)',
          }}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files?.length) handleFile(e.dataTransfer.files[0]);
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={(e) => e.target.files && handleFile(e.target.files[0])}
          />
          {uploading ? (
            <div className="flex flex-col items-center gap-3 py-3">
              <div
                className="w-4 h-4 rounded-full border-[1.5px] border-t-transparent animate-spin"
                style={{ borderColor: 'rgba(255,153,51,0.8) transparent rgba(255,153,51,0.8) rgba(255,153,51,0.8)' }}
              />
              <span className="text-[10px] tracking-widest uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
                Uploading…
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2.5 py-2 text-center">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center mb-1"
                style={{ background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.3)' }}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <div className="text-[12px] font-medium" style={{ color: 'rgba(255,255,255,0.65)' }}>
                Drop or click to upload
              </div>
              <div className="text-[10px] font-light" style={{ color: 'rgba(255,255,255,0.22)' }}>
                GeoTIFF · PNG · JPEG
              </div>
            </div>
          )}
        </div>

        {/* Loaded scenes */}
        {state.scenes.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="sq-label mb-1">
              Loaded &nbsp;
              <span
                className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px]"
                style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.6)' }}
              >
                {state.scenes.length}
              </span>
            </div>
            {state.scenes.map((s, i) => (
              <div
                key={s.asset.asset_id}
                className="group flex gap-3 p-3 rounded-xl transition-all duration-200"
                style={{
                  background: 'rgba(255,255,255,0.025)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.025)')}
              >
                {/* Thumbnail */}
                <div
                  className="w-12 h-12 shrink-0 rounded-lg overflow-hidden"
                  style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
                >
                  <img
                    src={s.thumbnailUrl || ''}
                    alt={`Scene ${i + 1}`}
                    className="w-full h-full object-cover opacity-75 group-hover:opacity-100 transition-opacity duration-200"
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                </div>
                <div className="flex flex-col justify-center gap-1.5 overflow-hidden flex-1 min-w-0">
                  <div
                    className="text-[11px] font-medium truncate"
                    style={{ color: 'rgba(255,255,255,0.75)' }}
                    title={s.asset.filename}
                  >
                    {s.asset.filename}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span
                      className="text-[9px] px-1.5 py-0.5 rounded-full tracking-wider uppercase font-semibold"
                      style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }}
                    >
                      {s.asset.modality}
                    </span>
                    <button
                      onClick={() => dispatch({ type: 'REMOVE_SCENE', payload: s.asset.asset_id })}
                      className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-[10px] px-1.5 py-0.5 rounded-md"
                      style={{ color: 'rgba(239,68,68,0.7)', background: 'rgba(239,68,68,0.08)', border: 'none', cursor: 'pointer' }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Mode indicator */}
        {state.workspaceMode !== 'EMPTY' && (
          <div
            className="p-3 rounded-xl"
            style={{
              background: 'rgba(255,255,255,0.015)',
              border: '1px solid rgba(255,255,255,0.05)',
            }}
          >
            <div className="sq-label mb-2">Active Mode</div>
            <div className="flex items-center gap-2">
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: state.workspaceMode === 'BITEMPORAL' ? 'var(--color-sq-change)'
                    : state.workspaceMode === 'SAR_ONLY' ? 'var(--color-sq-sar)'
                    : state.workspaceMode === 'CROSS_MODAL' ? 'var(--color-sq-fusion)'
                    : 'var(--color-sq-optical)',
                }}
              />
              <span className="text-[11px] font-light" style={{ color: 'rgba(255,255,255,0.5)' }}>
                {state.workspaceMode === 'BITEMPORAL' ? 'Bi-temporal comparison ready'
                  : state.workspaceMode === 'SAR_ONLY' ? 'SAR analysis ready'
                  : state.workspaceMode === 'CROSS_MODAL' ? 'Cross-modal fusion ready'
                  : 'Single scene analysis ready'}
              </span>
            </div>
          </div>
        )}

        {/* Tools list */}
        <div>
          <div className="sq-label mb-2.5">Capabilities</div>
          <div className="flex flex-col gap-1">
            {[
              { label: 'Optical Analysis', color: 'var(--color-sq-optical)' },
              { label: 'SAR Backscatter', color: 'var(--color-sq-sar)' },
              { label: 'Change Detection', color: 'var(--color-sq-change)' },
              { label: 'Multi-Modal Fusion', color: 'var(--color-sq-fusion)' },
            ].map((tool) => (
              <div
                key={tool.label}
                className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg"
                style={{ color: 'rgba(255,255,255,0.3)' }}
              >
                <div className="w-1 h-1 rounded-full" style={{ background: tool.color, opacity: 0.6 }} />
                <span className="text-[11px] font-light">{tool.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
