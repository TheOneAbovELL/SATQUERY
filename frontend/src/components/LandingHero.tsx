"use client";
import React, { useEffect, useState } from 'react';

interface LandingHeroProps {
  onEnter: () => void;
  isExiting: boolean;
}

const FEATURES = [
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    title: 'Natural Language',
    subtitle: 'Queries',
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2" />
        <polyline points="2 17 12 22 22 17" />
        <polyline points="2 12 12 17 22 12" />
      </svg>
    ),
    title: 'Multi-Modal',
    subtitle: 'Analysis',
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    title: 'Change',
    subtitle: 'Detection',
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    title: 'Evidence-Backed',
    subtitle: 'Answers',
  },
];

export function LandingHero({ onEnter, isExiting }: LandingHeroProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  const fade = (delay: number): React.CSSProperties => ({
    opacity: mounted ? 1 : 0,
    transform: mounted ? 'none' : 'translateY(12px)',
    transition: `opacity 0.8s ease ${delay}ms, transform 0.8s ease ${delay}ms`,
  });

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col overflow-hidden ${
        isExiting ? 'sq-landing-exit' : mounted ? 'sq-landing' : 'opacity-0'
      }`}
    >
      {/* ── FULL-SCREEN CINEMATIC BACKGROUND (ref2 — Earth from space with India) ── */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: "url('/earth-hero.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center center',
          backgroundRepeat: 'no-repeat',
        }}
      />

      {/* Gradient overlay — dark at top (space), nearly transparent mid (Earth crisp), dark at bottom (text) */}
      <div
        className="absolute inset-0"
        style={{
          background: [
            'linear-gradient(to bottom,',
            '  rgba(0,0,0,0.55) 0%,',
            '  rgba(0,0,0,0.10) 20%,',
            '  rgba(0,0,0,0.04) 40%,',
            '  rgba(0,0,0,0.28) 60%,',
            '  rgba(0,0,0,0.75) 80%,',
            '  rgba(0,0,0,0.93) 100%',
            ')',
          ].join(' '),
        }}
      />

      {/* Very subtle edge vignette — only darkens extreme corners, not the center */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 110% 110% at 50% 50%, transparent 65%, rgba(0,0,0,0.35) 100%)',
        }}
      />

      {/* ── HEADER ── */}
      <header
        className="relative z-10 flex items-center justify-between px-8 md:px-14 pt-7"
        style={fade(100)}
      >
        {/* Wordmark */}
        <div className="flex items-center gap-2.5">
          <div
            className="w-2 h-2 rounded-sm"
            style={{
              background: 'linear-gradient(135deg, #FF9933 0%, #F4F4F2 50%, #138808 100%)',
            }}
          />
          <span className="text-sm font-bold tracking-[0.22em]" style={{ color: '#ffffff' }}>
            SATQUERY
          </span>
          <span className="text-xs font-light tracking-[0.1em]" style={{ color: 'rgba(255,255,255,0.38)' }}>
            AI
          </span>
        </div>

        {/* Status pill */}
        <div className="hidden md:flex items-center gap-2">
          <div
            className="w-1.5 h-1.5 rounded-full sq-glow-pulse"
            style={{ background: '#22c55e', boxShadow: '0 0 5px #22c55e' }}
          />
          <span className="text-[10px] font-mono tracking-[0.15em]" style={{ color: 'rgba(255,255,255,0.38)' }}>
            SYSTEM ONLINE
          </span>
        </div>
      </header>

      {/* ── HERO TEXT — sits in the lower center over the mountain landscape ── */}
      <main
        className="relative z-10 flex-1 flex flex-col items-center justify-end pb-[13%] px-6 text-center"
      >
        {/* Eyebrow */}
        <div className="mb-5" style={fade(220)}>
          <span
            className="text-[11px] tracking-[0.38em] font-medium"
            style={{ 
              color: 'rgba(255,255,255,0.85)',
              textShadow: '0 2px 12px rgba(0,0,0,0.8)'
            }}
          >
            FROM SPACE &nbsp;|&nbsp; FOR A BETTER TOMORROW
          </span>
        </div>

        {/* Main headline */}
        <div className="mb-5" style={fade(340)}>
          <h1
            className="text-5xl md:text-6xl lg:text-[74px] font-bold tracking-[-0.025em] leading-[1.05]"
            style={{
              color: '#ffffff',
              textShadow: '0 2px 30px rgba(0,0,0,0.6)',
            }}
          >
            Understand Earth
          </h1>
          <h1
            className="text-5xl md:text-6xl lg:text-[74px] font-bold tracking-[-0.025em] leading-[1.05]"
            style={{ textShadow: '0 2px 30px rgba(0,0,0,0.5)' }}
          >
            <span style={{ color: '#FF9933' }}>from</span>
            <span style={{ color: '#ffffff' }}> imagery.</span>
          </h1>
        </div>

        {/* Supporting copy */}
        <div className="max-w-xl mb-9" style={fade(450)}>
          <p
            className="text-base md:text-[17px] font-light leading-relaxed"
            style={{ 
              color: 'rgba(255,255,255,0.95)',
              textShadow: '0 2px 10px rgba(0,0,0,0.8)'
            }}
          >
            An AI-powered assistant for satellite imagery and geospatial intelligence.
          </p>
          <p
            className="text-sm font-light leading-relaxed mt-2"
            style={{ 
              color: 'rgba(255,255,255,0.75)',
              textShadow: '0 2px 8px rgba(0,0,0,0.8)'
            }}
          >
            Ask questions, detect changes, analyze optical and SAR imagery,<br />
            and get evidence-backed answers.
          </p>
        </div>

        {/* CTA button */}
        <div style={fade(560)}>
          <button
            onClick={onEnter}
            className="sq-cta-button group flex items-center gap-3 px-10 py-4 rounded-full"
            style={{
              background: 'rgba(255,255,255,0.07)',
              border: '1px solid rgba(255,255,255,0.38)',
              color: '#ffffff',
              fontSize: '15px',
              fontWeight: 500,
              letterSpacing: '0.05em',
              cursor: 'pointer',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)',
            }}
          >
            <span>Start Analyzing</span>
            <svg
              className="transition-transform duration-300 group-hover:translate-x-1"
              width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </main>

      {/* ── FEATURE STRIP ── */}
      <footer
        className="relative z-10 px-8 md:px-14 pb-8"
        style={fade(680)}
      >
        {/* Features row */}
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-5 mb-7">
          {FEATURES.map((f) => (
            <div key={f.title} className="flex items-center gap-3">
              <div className="shrink-0" style={{ color: 'rgba(255,255,255,0.48)' }}>
                {f.icon}
              </div>
              <div className="text-left">
                <div className="text-[11px] font-light leading-none mb-0.5" style={{ color: 'rgba(255,255,255,0.55)' }}>
                  {f.title}
                </div>
                <div className="text-[11px] font-light leading-none" style={{ color: 'rgba(255,255,255,0.3)' }}>
                  {f.subtitle}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom row */}
        <div className="flex items-end justify-between">
          {/* Left: saffron bar + tagline */}
          <div className="flex flex-col gap-2">
            <div className="h-[2px] w-10 rounded-full" style={{ background: '#FF9933' }} />
            <span className="text-[11px] font-light" style={{ color: 'rgba(255,255,255,0.42)' }}>
              Built for a clearer, more resilient tomorrow.
            </span>
          </div>

          {/* Right: stacked labels */}
          <div className="text-right hidden md:block">
            {['SATELLITE DATA', 'REAL INSIGHTS', 'GREATER IMPACT'].map((line) => (
              <div
                key={line}
                className="text-[10px] tracking-[0.2em] leading-loose"
                style={{ color: 'rgba(255,255,255,0.28)' }}
              >
                {line}
              </div>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
