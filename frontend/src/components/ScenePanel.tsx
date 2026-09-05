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
      const asset = await uploadAsset(file, 'T1'); // Default to T1
      dispatch({ type: 'ADD_SCENE', payload: {
        asset,
        role: 'T1',
        thumbnailUrl: getThumbnailUrl(asset.asset_id),
        uploadStatus: 'ready',
        uploadError: null
      }});
    } catch (e) {
      console.error(e);
      alert('Upload failed: ' + String(e));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col w-[280px] h-full shrink-0" style={{ background: 'var(--color-sq-surface)', borderRight: '1px solid var(--color-sq-border)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--color-sq-border)' }}>
        <div className="text-[10px] font-bold tracking-widest" style={{ color: 'var(--color-sq-muted)' }}>SCENES</div>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        <div 
          className="flex flex-col items-center justify-center p-6 rounded-lg cursor-pointer transition-colors"
          style={{ 
            border: `2px dashed ${isDragging ? 'var(--color-sq-accent)' : 'var(--color-sq-border-2)' }`,
            background: 'var(--color-sq-surface-2)'
          }}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
              handleFile(e.dataTransfer.files[0]);
            }
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input type="file" ref={fileInputRef} className="hidden" onChange={(e) => e.target.files && handleFile(e.target.files[0])} />
          {uploading && <div className="text-xs animate-pulse" style={{ color: 'var(--color-sq-accent)' }}>Uploading...</div>}
          <div className="text-sm mb-1" style={{ color: 'var(--color-sq-text)' }}>Drop satellite imagery</div>
          <div className="text-[10px]" style={{ color: 'var(--color-sq-muted)' }}>GeoTIFF · TIFF · PNG · JPEG</div>
        </div>

        {state.scenes.map((s) => (
          <div key={s.asset.asset_id} className="flex gap-3 p-2 rounded border" style={{ background: 'var(--color-sq-surface-2)', borderColor: 'var(--color-sq-border-2)' }}>
            <div className="w-12 h-12 shrink-0 rounded overflow-hidden">
              <img src={s.thumbnailUrl || ''} alt="Thumbnail" className="w-full h-full object-cover" onError={(e) => {e.currentTarget.style.display='none'}} />
            </div>
            <div className="flex flex-col justify-center overflow-hidden">
              <div className="text-xs font-medium truncate">{s.asset.filename}</div>
              <div className="text-[10px] sq-mono truncate" style={{ color: 'var(--color-sq-muted)' }}>
                {s.asset.modality} | {(s.asset.dimensions ? `${s.asset.dimensions[0]}x${s.asset.dimensions[1]}` : '')}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
