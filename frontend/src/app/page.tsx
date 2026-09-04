"use client";
import React, { useState } from 'react';

interface TraceEvent {
  stage: string;
  action: string;
  status: string;
}

interface AnalysisResultData {
  analysis_id: string;
  task: string;
  status: string;
  summary: string;
  metrics: Record<string, number>;
  claims: string[];
  execution_trace: TraceEvent[];
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResultData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, asset_ids: ['mock_1'] }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data: AnalysisResultData = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-slate-900 text-white font-sans overflow-hidden">
      
      {/* LEFT PANE: Conversation & Execution Trace */}
      <div className="w-1/3 flex flex-col border-r border-slate-700 bg-slate-950">
        <div className="p-4 border-b border-slate-700 bg-slate-900 shadow-sm z-10">
          <h1 className="text-xl font-bold tracking-tight text-blue-400">SatQuery AI</h1>
          <p className="text-xs text-slate-400 mt-1">SIH 2026 Interactive Analysis</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Status / Result */}
          {loading && (
            <div className="p-3 bg-slate-800 rounded-lg border border-blue-700 animate-pulse">
              <p className="text-sm text-blue-300">⟳ Processing query...</p>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-900/30 rounded-lg border border-red-700">
              <p className="text-sm text-red-300">Error: {error}</p>
            </div>
          )}

          {result && (
            <>
              <div className="p-3 bg-slate-800 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-400 mb-1">Task: {result.task} — Status: <span className={result.status === 'SUCCESS' ? 'text-green-400' : 'text-yellow-400'}>{result.status}</span></p>
                <p className="text-sm">{result.summary}</p>
              </div>

              {Object.keys(result.metrics).length > 0 && (
                <div className="p-3 bg-slate-800 rounded-lg border border-slate-700">
                  <p className="text-xs font-semibold text-slate-300 mb-2">METRICS</p>
                  {Object.entries(result.metrics).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-sm">
                      <span className="text-slate-400">{k}</span>
                      <span className="font-mono text-green-300">{typeof v === 'number' ? v.toFixed(4) : v}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Execution Trace */}
          <div className="mt-4 border border-slate-700 rounded-lg overflow-hidden">
            <div className="bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-300 border-b border-slate-700">
              EXECUTION TRACE
            </div>
            <div className="p-3 bg-slate-900 text-xs font-mono text-slate-400 space-y-1 max-h-64 overflow-y-auto">
              {result?.execution_trace?.map((evt, i) => (
                <div key={i}>
                  <span className={evt.status === 'SUCCESS' ? 'text-green-400' : evt.status === 'FAILED' ? 'text-red-400' : 'text-blue-400'}>
                    {evt.status === 'SUCCESS' ? '✓' : evt.status === 'FAILED' ? '✗' : '⟳'}
                  </span>{' '}
                  [{evt.stage}] {evt.action}
                </div>
              )) || <div className="text-slate-500">No trace events yet.</div>}
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-700 bg-slate-900">
          <div className="flex gap-2">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              placeholder="Ask about the imagery..." 
              className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            />
            <button 
              onClick={handleSubmit}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT PANE: Geospatial Workspace */}
      <div className="flex-1 flex flex-col bg-slate-800 relative">
        <div className="absolute top-4 left-4 z-10 bg-slate-900/80 backdrop-blur border border-slate-700 p-2 rounded flex gap-2 shadow-lg">
          <button className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs font-medium border border-slate-600 transition-colors">Layers</button>
          <button className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs font-medium border border-slate-600 transition-colors">Analytics</button>
        </div>
        
        {/* Placeholder Map Viewport */}
        <div className="flex-1 flex items-center justify-center border-4 border-dashed border-slate-700 m-8 rounded-2xl bg-slate-900/50">
          <div className="text-center">
            <div className="text-4xl mb-4">🌍</div>
            <h2 className="text-lg font-medium text-slate-300 mb-2">Geospatial Workspace</h2>
            <p className="text-sm text-slate-500">Map view and visual artifacts will render here.</p>
          </div>
        </div>
      </div>
      
    </div>
  );
}
