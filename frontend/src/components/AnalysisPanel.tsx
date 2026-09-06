"use client";
import React, { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useWorkspace } from "../lib/store";
import { ExecutionTimeline } from "./ExecutionTimeline";
import { EvidenceCard } from "./EvidenceCard";
import { ErrorState } from "./ErrorState";

/**
 * Strips internal chain-of-thought preamble that the model sometimes emits
 * before the actual analysis. Display-layer only — backend is untouched.
 *
 * Patterns stripped:
 *   "The user wants..."  |  "I need to act as..."  |  "I must avoid..."
 *
 * The function looks for the first clearly analytical section marker and
 * returns everything from there. If no preamble is detected it returns the
 * original string unchanged.
 */
function sanitizeAISummary(raw: string): string {
  if (!raw) return raw;

  // List of known preamble openers (case-insensitive)
  const preambleRe = /^(the user wants|i need to act|i must avoid|i am acting|as satquery ai|i will now)/i;
  const firstLine = raw.split('\n')[0].trim();
  if (!preambleRe.test(firstLine)) return raw; // no preamble detected

  // Strategy 1: find an explicit section marker like "Image Analysis:" or "**Overview**"
  const markerPatterns = [
    /\n\n(?=Image Analysis:|Overview:|Scene Description:|Analysis:|##\s|\*\*[A-Z])/,
    /\n\nImage Analysis:/i,
    /\n\nOverview:/i,
    /\n\nScene:/i,
  ];
  for (const pat of markerPatterns) {
    const m = raw.search(pat);
    if (m !== -1) {
      // Skip two newlines at the boundary
      const startIdx = raw.indexOf('\n\n', m) + 2;
      return raw.slice(startIdx).trim();
    }
  }

  // Strategy 2: skip every leading paragraph that starts with a preamble opener,
  // then return the rest
  const paragraphs = raw.split(/\n\n+/);
  let firstContentIdx = 0;
  for (let i = 0; i < paragraphs.length; i++) {
    const p = paragraphs[i].trim();
    if (preambleRe.test(p) || /^(I need|I must|I will|I am|The output|The user)/i.test(p)) {
      firstContentIdx = i + 1;
    } else {
      break;
    }
  }
  if (firstContentIdx > 0 && firstContentIdx < paragraphs.length) {
    return paragraphs.slice(firstContentIdx).join('\n\n').trim();
  }

  return raw; // fallback — return as-is
}

/**
 * SAR Plain-Language Enricher — display layer only, backend untouched.
 *
 * Detects SAR technical metrics (backscatter dB values, percentiles) in the
 * raw summary and prepends a human-readable "What this means" callout so that
 * any user (not just radar experts) can understand the result.
 */
function enrichSARSummary(raw: string): string {
  if (!raw) return raw;

  // Check if this looks like a SAR result
  const hasSARTerms = /backscatter|dB|decibel|percentile|sigma.?nought|coherence|polarisation|polarization/i.test(raw);
  if (!hasSARTerms) return raw;

  // Extract dB numbers from the text to build context
  const dbMatches = [...raw.matchAll(/([-\d.]+)\s*dB/gi)];
  if (dbMatches.length === 0) return raw;

  const dbValues = dbMatches.map(m => parseFloat(m[1])).filter(v => !isNaN(v));
  const avgDb = dbValues.find((_, i) => /average|mean/i.test(dbMatches[i]?.input?.slice(Math.max(0, (dbMatches[i]?.index ?? 0) - 30), dbMatches[i]?.index ?? 0) ?? ''));
  const peakDb = dbValues.find((_, i) => /peak|percentile|max/i.test(dbMatches[i]?.input?.slice(Math.max(0, (dbMatches[i]?.index ?? 0) - 30), dbMatches[i]?.index ?? 0) ?? ''));

  // Interpret average backscatter
  function interpretAvgDb(db: number): string {
    if (db < -20) return 'very smooth surfaces like calm water or bare flat ground — almost no radar signal reflected back';
    if (db < -10) return 'smooth or lightly textured surfaces such as agricultural fields, grasslands, or roads';
    if (db < 0)  return 'moderately rough surfaces typical of vegetation, shrubland, or mixed land cover';
    if (db < 10) return 'rough terrain, dense vegetation, or urban areas with significant radar reflection';
    return 'highly reflective surfaces — likely dense urban areas, metal structures, or very rough terrain';
  }

  // Interpret peak backscatter
  function interpretPeakDb(db: number): string {
    if (db < 0)   return 'moderate peak reflections — no unusually bright targets detected';
    if (db < 15)  return 'some bright targets, possibly vehicles, small buildings, or exposed rock faces';
    if (db < 30)  return 'strong bright targets — likely metallic structures, rooftops, or corner reflectors';
    return 'very strong bright targets — likely large metal structures, ships, infrastructure, or man-made corner reflections';
  }

  const avgLine  = avgDb  !== undefined ? `**Average signal:** ${avgDb.toFixed(1)} dB — ${interpretAvgDb(avgDb)}` : '';
  const peakLine = peakDb !== undefined ? `**Brightest point:** ${peakDb.toFixed(1)} dB — ${interpretPeakDb(peakDb)}` : '';

  const lines = [avgLine, peakLine].filter(Boolean).join('\n\n');

  const plainBlock = `> **📡 In plain language:**\n>\n${lines.split('\n').map(l => `> ${l}`).join('\n')}\n\n---\n\n`;

  return plainBlock + raw;
}

export function AnalysisPanel() {
  const { state, dispatch } = useWorkspace();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [state.history]);

  return (
    <div
      className="flex flex-col flex-1 h-full overflow-hidden"
      style={{ background: "var(--color-sq-bg)", position: "relative" }}
    >
      {/* Chat ambient background — opacity increased directly by 15% as requested */}
      <div
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          backgroundImage: "url('/chat-bg.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center bottom',
          backgroundRepeat: 'no-repeat',
          opacity: 0.24,
          mixBlendMode: 'screen',
        }}
      />
      <div className="relative z-10 flex-1 overflow-y-auto">
        {state.history.length === 0 ? (
          /* ── Empty / Hero State ── */
          <div className="h-full flex flex-col items-center justify-center p-10 text-center">
            {/* Top decoration */}
            <div className="flex items-center gap-1.5 mb-8">
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--color-in-saffron)", opacity: 0.7 }} />
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--color-in-white)", opacity: 0.7 }} />
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--color-in-green)", opacity: 0.7 }} />
            </div>

            <div
              className="text-[10px] font-semibold tracking-[0.25em] mb-8 px-4 py-1.5 rounded-full border"
              style={{
                color: "var(--color-sq-muted)",
                borderColor: "var(--color-sq-border)",
                background: "rgba(255,255,255,0.015)",
              }}
            >
              SATQUERY AI
            </div>

            <h2
              className="text-4xl md:text-5xl lg:text-6xl font-medium tracking-[-0.02em] leading-[1.06] mb-6"
              style={{ color: "var(--color-sq-text)" }}
            >
              Welcome to<br />SatQuery AI
            </h2>

            <p className="max-w-md text-base font-light leading-relaxed mb-4" style={{ color: "var(--color-sq-muted)" }}>
              Ask. Analyze. Understand Earth.
            </p>

            <p className="max-w-sm text-sm font-light leading-relaxed mb-12" style={{ color: "var(--color-sq-subtle)" }}>
              Upload satellite imagery on the left, then ask any question about your scene.
            </p>

            {/* Example query chips */}
            <div className="flex flex-wrap justify-center gap-2.5 max-w-lg">
              {[
                "What changed between these images?",
                "Identify new structures.",
                "Analyze this SAR image.",
                "Compare optical and SAR observations.",
              ].map((q) => (
                <div
                  key={q}
                  className="text-[11px] px-4 py-2 rounded-full"
                  style={{
                    background: "rgba(255,255,255,0.025)",
                    border: "1px solid var(--color-sq-border)",
                    color: "var(--color-sq-subtle)",
                  }}
                >
                  {q}
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* ── Conversation ── */
          <div className="flex flex-col h-full">
            {/* Sticky action bar */}
            <div
              className="flex items-center justify-between px-5 py-2 shrink-0"
              style={{
                background: 'rgba(5,5,7,0.80)',
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                borderBottom: '1px solid rgba(255,255,255,0.045)',
              }}
            >
              <span
                className="text-[9px] font-semibold tracking-[0.24em] uppercase"
                style={{ color: 'rgba(255,255,255,0.2)' }}
              >
                Conversation
              </span>
              <div className="flex items-center gap-1.5">
                {/* Clear chat — keeps scenes loaded */}
                <button
                  onClick={() => dispatch({ type: 'RESET_ANALYSIS' })}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-medium transition-all duration-200"
                  style={{
                    border: '1px solid rgba(255,255,255,0.07)',
                    color: 'rgba(255,255,255,0.35)',
                    cursor: 'pointer',
                    background: 'transparent',
                  }}
                  title="Clear chat history but keep uploaded images"
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.05)';
                    (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.65)';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
                    (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.35)';
                  }}
                >
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="1 4 1 10 7 10"></polyline>
                    <path d="M3.51 15a9 9 0 1 0 .49-3.51"></path>
                  </svg>
                  Clear
                </button>
                {/* New Analysis — clears everything */}
                <button
                  onClick={() => dispatch({ type: 'FULL_RESET' })}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-medium transition-all duration-200"
                  style={{
                    border: '1px solid rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.55)',
                    cursor: 'pointer',
                    background: 'rgba(255,255,255,0.03)',
                  }}
                  title="Start fresh — removes all uploaded images and conversation"
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.07)';
                    (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.85)';
                    (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.15)';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.03)';
                    (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.55)';
                    (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(255,255,255,0.1)';
                  }}
                >
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  New Analysis
                </button>
              </div>
            </div>
          <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8">
            {state.history.map((item) => (
              <div key={item.id} className="flex flex-col gap-5 sq-fade-in">
                {/* User query bubble — pill-style */}
                <div className="flex justify-end">
                  <div
                    className="max-w-[78%] px-5 py-3.5 rounded-3xl"
                    style={{
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.09)",
                      backdropFilter: 'blur(4px)',
                    }}
                  >
                    <p className="text-[14px] font-light leading-relaxed" style={{ color: "rgba(255,255,255,0.85)" }}>
                      {item.query}
                    </p>
                  </div>
                </div>

                {/* Error */}
                {item.error && (
                  <ErrorState error={item.error} onReset={() => dispatch({ type: "RESET_ANALYSIS" })} />
                )}

                {/* Processing */}
                {item.phase !== "idle" && item.phase !== "done" && item.phase !== "failed" && (
                  <div className="flex justify-start max-w-[88%]">
                    <ExecutionTimeline phase={item.phase} events={item.result?.execution_trace || []} />
                  </div>
                )}

                {/* AI response */}
                {item.result && (
                  <div className="flex justify-start">
                    <div className="flex flex-col gap-5 w-full max-w-[90%]">
                      {/* Response bubble — frosted glass */}
                      <div
                        className="relative p-6 md:p-7 rounded-3xl overflow-hidden"
                        style={{
                          background: "rgba(255,255,255,0.025)",
                          border: "1px solid rgba(255,255,255,0.07)",
                          backdropFilter: 'blur(8px)',
                          WebkitBackdropFilter: 'blur(8px)',
                        }}
                      >
                        {/* Subtle top left glow */}
                        <div
                          className="absolute -top-8 -left-8 w-24 h-24 rounded-full pointer-events-none blur-3xl"
                          style={{ background: "rgba(255,153,51,0.06)" }}
                        />

                        {/* AI label */}
                        <div className="flex items-center gap-2 mb-5">
                          <div
                            className="w-2.5 h-2.5 rounded-sm"
                            style={{
                              background: "linear-gradient(135deg, #FF9933 0%, #F4F4F2 50%, #138808 100%)",
                              boxShadow: "0 0 6px rgba(255,255,255,0.15)",
                            }}
                          />
                          <span
                            className="text-[10px] font-semibold tracking-[0.2em]"
                            style={{ color: "var(--color-sq-muted)" }}
                          >
                            SATQUERY AI
                          </span>
                        </div>

                        {/* Markdown content */}
                        <div
                          className="prose prose-invert max-w-none text-[14px] font-light"
                          style={{ color: "var(--color-sq-text)" }}
                        >
                          <ReactMarkdown
                            components={{
                              p: ({ node, ...props }) => (
                                <p className="mb-4 leading-[1.8] opacity-90" {...props} />
                              ),
                              strong: ({ node, ...props }) => (
                                <strong className="font-medium text-white" {...props} />
                              ),
                              ul: ({ node, ...props }) => (
                                <ul className="list-disc pl-5 mb-4 space-y-1.5 opacity-90" {...props} />
                              ),
                              li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                              h1: ({ node, ...props }) => (
                                <h1 className="text-xl font-medium mt-6 mb-3 text-white tracking-tight" {...props} />
                              ),
                              h2: ({ node, ...props }) => (
                                <h2 className="text-lg font-medium mt-5 mb-2.5 text-white tracking-tight" {...props} />
                              ),
                              h3: ({ node, ...props }) => (
                                <h3 className="text-base font-medium mt-4 mb-2 text-white tracking-tight" {...props} />
                              ),
                            }}
                          >
                            {enrichSARSummary(sanitizeAISummary(item.result.summary))}
                          </ReactMarkdown>
                        </div>
                      </div>

                      {/* Evidence section */}
                      {item.result.spatial_evidence && item.result.spatial_evidence.length > 0 && (
                        <div className="flex flex-col gap-3 pl-1">
                          <div className="flex items-center gap-3">
                            <div className="h-px flex-1" style={{ background: "var(--color-sq-border)" }} />
                            <span
                              className="text-[10px] font-semibold tracking-[0.2em]"
                              style={{ color: "var(--color-sq-subtle)" }}
                            >
                              SUPPORTING EVIDENCE
                            </span>
                            <div className="h-px flex-1" style={{ background: "var(--color-sq-border)" }} />
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {item.result.spatial_evidence.map((ev, i) => (
                              <EvidenceCard key={i} evidence={ev} index={i} />
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
          </div>
        )}
      </div>
    </div>
  );
}
