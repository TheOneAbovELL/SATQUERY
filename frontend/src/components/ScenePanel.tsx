"use client";
import React, { useRef, useState } from 'react';
import { useWorkspace } from '../lib/store';
import { uploadAsset, getThumbnailUrl } from '../lib/api';

const SIDEBAR_SECTIONS = [
  { id: 'workspace', label: 'WORKSPACE', icon: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect>
      <rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect>
    </svg>
  )},
  { id: 'data', label: 'DATA', icon: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
    </svg>
  )},
];

export function ScenePanel() {
  const { state, dispatch } = useWorkspace();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [activeSection, setActiveSection] = useState('data');

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
        width: '260px',
        background: 'var(--color-sq-surface)',
        borderRight: '1px solid var(--color-sq-border)',
      }}
    >
      {/* Sidebar nav icons */}
      <div
        className="flex items-center gap-1 px-4 py-3 border-b"
        style={{ borderColor: 'var(--color-sq-border)' }}
      >
        {SIDEBAR_SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveSection(s.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors"
            style={{
              background: activeSection === s.id ? 'rgba(255,255,255,0.06)' : 'transparent',
              border: activeSection === s.id ? '1px solid var(--color-sq-border-2)' : '1px solid transparent',
              color: activeSection === s.id ? 'var(--color-sq-text)' : 'var(--color-sq-subtle)',
              cursor: 'pointer',
            }}
          >
            {s.icon}
            <span style={{ fontSize: '9px', fontWeight: 600, letterSpacing: '0.12em' }}>{s.label}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-5">
        {/* Upload zone */}
        <div>
          <div className="sq-label mb-3">Upload Imagery</div>
          <div
            className="flex flex-col items-center justify-center p-6 rounded-xl cursor-pointer transition-all duration-300"
            style={{
              border: `1px dashed ${isDragging ? 'rgba(255,153,51,0.5)' : 'var(--color-sq-border-2)'}`,
              background: isDragging ? 'rgba(255,153,51,0.04)' : 'rgba(255,255,255,0.015)',
              transform: isDragging ? 'scale(0.98)' : 'scale(1)',
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
              <div className="flex flex-col items-center gap-3">
                <div
                  className="w-5 h-5 rounded-full border-2 border-t-transparent animate-spin"
                  style={{ borderColor: 'var(--color-in-saffron) transparent var(--color-in-saffron) var(--color-in-saffron)' }}
                />
                <span className="text-[10px] tracking-widest uppercase font-medium" style={{ color: 'var(--color-sq-muted)' }}>
                  Uploading
                </span>
              </div>
            ) : (
              <>
                <div
                  className="w-9 h-9 mb-3 rounded-full flex items-center justify-center"
                  style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--color-sq-subtle)' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                  </svg>
                </div>
                <div className="text-[12px] font-medium mb-1" style={{ color: 'var(--color-sq-text)' }}>
                  Drop or click
                </div>
                <div className="text-[10px] font-light" style={{ color: 'var(--color-sq-subtle)' }}>
                  GeoTIFF | TIFF | PNG | JPEG
                </div>
              </>
            )}
          </div>
        </div>

        {/* Scenes list */}
        {state.scenes.length > 0 && (
          <div>
            <div className="sq-label mb-3">
              Scenes &nbsp;
              <span
                className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px]"
                style={{ background: 'var(--color-sq-border-2)', color: 'var(--color-sq-text)' }}
              >
                {state.scenes.length}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              {state.scenes.map((s, i) => (
                <div
                  key={s.asset.asset_id}
                  className="flex gap-3 p-3 rounded-lg group transition-all hover:border-[var(--color-sq-border-2)]"
                  style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--color-sq-border)',
                  }}
                >
                  <div
                    className="w-12 h-12 shrink-0 rounded-md overflow-hidden"
                    style={{ background: 'var(--color-sq-surface-2)', border: '1px solid var(--color-sq-border)' }}
                  >
                    <img
                      src={s.thumbnailUrl || ''}
                      alt={`Scene ${i + 1}`}
                      className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  </div>
                  <div className="flex flex-col justify-center overflow-hidden flex-1 gap-1">
                    <div
                      className="text-[11px] font-medium truncate"
                      style={{ color: 'var(--color-sq-text)' }}
                      title={s.asset.filename}
                    >
                      {s.asset.filename}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span
                        className="text-[9px] px-1.5 py-0.5 rounded tracking-wider uppercase font-semibold"
                        style={{ background: 'var(--color-sq-surface-3)', color: 'var(--color-sq-muted)' }}
                      >
                        {s.asset.modality}
                      </span>
                      {s.asset.dimensions && (
                        <span className="text-[9px] font-mono" style={{ color: 'var(--color-sq-subtle)' }}>
                          {s.asset.dimensions[0]}x{s.asset.dimensions[1]}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tools section hint */}
        <div>
          <div className="sq-label mb-3">Analysis Tools</div>
          {[
            { label: 'Optical Analysis', color: 'var(--color-sq-optical)' },
            { label: 'SAR Analysis', color: 'var(--color-sq-sar)' },
            { label: 'Change Detection', color: 'var(--color-sq-change)' },
            { label: 'Multi-Modal', color: 'var(--color-sq-fusion)' },
          ].map((tool) => (
            <div
              key={tool.label}
              className="flex items-center gap-2.5 px-3 py-2 rounded-md mb-1"
              style={{ color: 'var(--color-sq-subtle)' }}
            >
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: tool.color, opacity: 0.7 }} />
              <span className="text-[11px] font-light">{tool.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
