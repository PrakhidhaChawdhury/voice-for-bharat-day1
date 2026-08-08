'use client';

import React, { useState } from 'react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  ref?: React.Ref<HTMLDivElement>;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [micError, setMicError] = useState<string | null>(null);

  const handleStartCall = async () => {
    try {
      setMicError(null);
      await navigator.mediaDevices.getUserMedia({ audio: true });
      onStartCall();
    } catch (err: any) {
      if (
        err.name === 'NotAllowedError' ||
        err.name === 'PermissionDeniedError' ||
        err.message?.includes('denied')
      ) {
        setMicError(
          'Microphone blocked. Click the lock icon in your address bar to allow mic access.'
        );
      } else {
        onStartCall();
      }
    }
  };

  return (
    <div
      ref={ref}
      className="relative flex min-h-screen w-full flex-col justify-between bg-[#060911] text-slate-100 font-sans antialiased overflow-hidden selection:bg-indigo-500 selection:text-white"
    >
      {/* Subtle Dot Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

      {/* Dynamic Ambient Background Glows */}
      <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-indigo-600/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-emerald-500/10 rounded-full blur-[130px] pointer-events-none" />

      {/* Integrated Header Bar */}
      <header className="relative z-20 w-full border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl px-6 md:px-12 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white shadow-md shadow-indigo-500/20 ring-1 ring-white/20">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white leading-none">
              Raksha AI
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5 font-medium tracking-wide">
              Digital Banking Safety & Fraud Prevention
            </p>
          </div>
        </div>

        {/* Shifted left to avoid overlapping the LiveKit Cloud tag */}
        <div className="flex items-center space-x-3 pr-44 md:pr-52">
          <div className="inline-flex items-center space-x-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-[11px] font-semibold text-emerald-400 backdrop-blur-md shadow-inner">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span>1930 Cyber Crime Sync Active</span>
          </div>
        </div>
      </header>

      {/* Centered Main Content Area */}
      <main className="relative z-10 flex-1 max-w-5xl w-full mx-auto p-6 md:p-8 flex items-center justify-center">
        <div className="w-full grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
          
          {/* Left Side: Security Features & Prompt Suggestions */}
          <div className="md:col-span-5 space-y-4">
            
            {/* Protocol Summary Card */}
            <div className="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-5 backdrop-blur-2xl shadow-xl shadow-black/40 ring-1 ring-white/10 space-y-3">
              <h3 className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 flex items-center space-x-2">
                <span>🛡️</span>
                <span>Active Guardrails</span>
              </h3>
              <ul className="space-y-2.5 text-xs text-slate-300 font-medium">
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Instant OTP & PIN Refusal Logic</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Native Hinglish Scam Detection</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>National Helpline 1930 Escalation</span>
                </li>
              </ul>
            </div>

            {/* Interactive Prompt Pills */}
            <div className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-4 backdrop-blur-2xl shadow-lg ring-1 ring-white/5 space-y-2.5">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Try asking Raksha:
              </p>
              <div className="flex flex-col gap-2">
                <span className="px-3 py-2 rounded-xl border border-slate-700/60 bg-slate-800/50 text-[11px] text-slate-300 transition-all hover:border-indigo-500/50 hover:bg-slate-800/80 hover:text-white cursor-pointer flex items-center justify-between">
                  <span>💬 "Mujhe ek suspicious link aaya hai"</span>
                  <span className="text-slate-500 text-[10px]">→</span>
                </span>
                <span className="px-3 py-2 rounded-xl border border-slate-700/60 bg-slate-800/50 text-[11px] text-slate-300 transition-all hover:border-indigo-500/50 hover:bg-slate-800/80 hover:text-white cursor-pointer flex items-center justify-between">
                  <span>🔑 "Can I share my OTP for verification?"</span>
                  <span className="text-slate-500 text-[10px]">→</span>
                </span>
                <span className="px-3 py-2 rounded-xl border border-slate-700/60 bg-slate-800/50 text-[11px] text-slate-300 transition-all hover:border-indigo-500/50 hover:bg-slate-800/80 hover:text-white cursor-pointer flex items-center justify-between">
                  <span>📞 "How to report fraud on 1930?"</span>
                  <span className="text-slate-500 text-[10px]">→</span>
                </span>
              </div>
            </div>
          </div>

          {/* Right Side: Hero Glass Consultation Card */}
          <div className="md:col-span-7 flex flex-col items-center">
            <div className="relative w-full max-w-md rounded-3xl border border-slate-700/60 bg-slate-900/70 p-8 md:p-10 backdrop-blur-2xl shadow-2xl shadow-indigo-950/30 ring-1 ring-white/10 flex flex-col items-center text-center space-y-6">
              
              {/* Inner Glow Spotlight */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-20 bg-indigo-500/20 rounded-full blur-2xl pointer-events-none" />

              {/* Center Shield Icon */}
              <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600/30 to-purple-600/30 border border-indigo-400/30 shadow-lg shadow-indigo-500/20 ring-1 ring-white/20 text-3xl">
                🛡️
              </div>

              <div className="space-y-2">
                <h2 className="text-2xl font-bold tracking-tight text-white">
                  Start Safety Consultation
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed max-w-xs mx-auto">
                  Connect with Raksha in real-time to analyze suspicious bank messages, verify links, or report scams.
                </p>
              </div>

              {/* Glowing CTA Button */}
              <div className="relative w-full pt-2">
                <button
                  onClick={handleStartCall}
                  className="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 active:scale-[0.98] text-white font-bold text-xs py-4 px-6 rounded-xl transition-all duration-200 shadow-lg shadow-indigo-600/30 border border-indigo-400/30 cursor-pointer tracking-wider uppercase"
                >
                  {startButtonText || 'Start Consultation'}
                </button>
              </div>

              {/* Mic Permission Error Alert */}
              {micError && (
                <div className="w-full bg-rose-950/70 border border-rose-800/80 text-rose-200 p-3.5 rounded-xl text-xs text-left leading-relaxed shadow-lg">
                  ⚠️ {micError}
                </div>
              )}
            </div>
          </div>

        </div>
      </main>

      {/* Grounded Footer */}
      <footer className="relative z-20 w-full border-t border-slate-800/80 bg-slate-950/70 py-3.5 text-center backdrop-blur-xl">
        <p className="text-[11px] text-slate-500 font-mono tracking-wider">
          POWERED BY <span className="text-slate-300 font-semibold">MURF FALCON</span> & LIVEKIT • #VOICEFORBHARAT
        </p>
      </footer>
    </div>
  );
};