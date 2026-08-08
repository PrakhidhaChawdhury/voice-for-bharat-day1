'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: { opacity: 1, translateY: '0%' },
    hidden: { opacity: 0, translateY: '100%' },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.3, delay: 0.2, ease: 'easeOut' },
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: { opacity: 1, transition: { ease: 'easeIn', duration: 0.5, delay: 0.3 } },
    hidden: { opacity: 0, transition: { ease: 'easeIn', duration: 0.3, delay: 0 } },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Raksha is listening. Ask about suspicious messages, OTPs, or bank links.',
  supportsChatInput = true,
  supportsVideoInput = false,
  supportsScreenShare = false,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const [chatOpen, setChatOpen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  // Auto scroll transcript to latest message
  useEffect(() => {
    if (chatOpen && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, chatOpen]);

  return (
    <section
      ref={ref}
      className={cn(
        'relative z-10 flex min-h-screen w-full flex-col justify-between bg-[#060911] text-slate-100 font-sans antialiased overflow-hidden selection:bg-indigo-500 selection:text-white',
        className
      )}
      {...props}
    >
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

      {/* Ambient Radial Background Highlights */}
      <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-indigo-600/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-emerald-500/10 rounded-full blur-[130px] pointer-events-none" />

      {/* Header Bar */}
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

        <div className="flex items-center space-x-3 pr-44 md:pr-52">
          <div className="inline-flex items-center space-x-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-[11px] font-semibold text-emerald-400 backdrop-blur-md shadow-inner">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span>Session Encrypted & Active</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col items-center justify-between my-auto">
        
        {/* Floating Visualizer (Expanded in Voice Mode, Compact in Chat Mode) */}
        <motion.div
          layout
          className={cn(
            'relative flex items-center justify-center w-full transition-all duration-300 ease-in-out',
            chatOpen ? 'h-[110px] my-0 scale-75' : 'h-[360px] my-auto scale-100'
          )}
        >
          {/* Soft Large Dark Radial Gradient Glow */}
          <div className="absolute w-[480px] h-[480px] rounded-full bg-gradient-to-r from-black/80 via-slate-950/70 to-transparent blur-3xl pointer-events-none" />
          <div className="absolute w-[360px] h-[360px] rounded-full bg-indigo-600/15 blur-2xl pointer-events-none animate-pulse" />

          {/* Screen Blend Visualizer Wrapper */}
          <div className="relative z-10 w-full h-full flex items-center justify-center mix-blend-screen [&_canvas]:mix-blend-screen [&_div]:!bg-transparent">
            <TileLayout
              chatOpen={false}
              audioVisualizerType={audioVisualizerType}
              audioVisualizerColor={audioVisualizerColor}
              audioVisualizerColorShift={audioVisualizerColorShift}
              audioVisualizerBarCount={audioVisualizerBarCount}
              audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
              audioVisualizerRadialRadius={audioVisualizerRadialRadius}
              audioVisualizerGridRowCount={audioVisualizerGridRowCount}
              audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
              audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
            />
          </div>
        </motion.div>

        {/* Chat Transcript Panel with Auto-Scroll Anchor */}
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              key="chat-panel"
              initial={{ opacity: 0, y: 15, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 15, scale: 0.98 }}
              transition={{ duration: 0.25 }}
              className="w-full max-w-2xl h-[340px] flex flex-col bg-slate-900/80 border border-slate-700/60 rounded-3xl p-4 backdrop-blur-2xl shadow-2xl ring-1 ring-white/10 overflow-hidden mb-2"
            >
              <div className="flex items-center space-x-2 pb-2.5 border-b border-slate-800/80">
                <span className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
                <span className="text-xs font-semibold text-slate-200">Live Fraud Security Transcript</span>
              </div>
              <div className="flex-1 overflow-y-auto pt-2 space-y-2">
                <AgentChatTranscript
                  agentState={agentState}
                  messages={messages}
                  className="w-full [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 md:[&>div>div]:px-6"
                />
                <div ref={chatEndRef} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Control Bar */}
        <motion.div
          {...BOTTOM_VIEW_MOTION_PROPS}
          className="relative z-30 w-full max-w-md px-2 pt-2 pb-2"
        >
          {isPreConnectBufferEnabled && !chatOpen && (
            <AnimatePresence>
              {messages.length === 0 && (
                <MotionMessage
                  key="pre-connect-message"
                  duration={2}
                  aria-hidden={messages.length > 0}
                  {...SHIMMER_MOTION_PROPS}
                  className="pointer-events-none mx-auto block w-full max-w-md pb-3 text-center text-xs font-medium text-slate-300 tracking-wide"
                >
                  {preConnectMessage}
                </MotionMessage>
              )}
            </AnimatePresence>
          )}

          <div className="relative mx-auto rounded-2xl border border-slate-700/60 bg-slate-900/90 p-2 backdrop-blur-2xl shadow-2xl ring-1 ring-white/10">
            <AgentControlBar
              variant="livekit"
              controls={controls}
              isChatOpen={chatOpen}
              isConnected={session.isConnected}
              onDisconnect={session.end}
              onIsChatOpenChange={setChatOpen}
            />
          </div>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="relative z-20 w-full border-t border-slate-800/80 bg-slate-950/70 py-3.5 text-center backdrop-blur-xl">
        <p className="text-[11px] text-slate-500 font-mono tracking-wider">
          POWERED BY <span className="text-slate-300 font-semibold">MURF FALCON</span> & LIVEKIT • #VOICEFORBHARAT
        </p>
      </footer>
    </section>
  );
}