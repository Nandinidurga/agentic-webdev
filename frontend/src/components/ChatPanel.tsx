"use client";

import { useState } from "react";
import { ChatMessage, StructuredError } from "../types/studio";
import { PRESET_PROMPTS } from "../hooks/useGenerate";
import { Send, Sparkles, AlertCircle, CheckCircle2, ChevronRight, Terminal, RefreshCw } from "lucide-react";

interface ChatPanelProps {
  prompt: string;
  setPrompt: (v: string) => void;
  loading: boolean;
  statusStep: string;
  messages: ChatMessage[];
  partialErrors: StructuredError[];
  onGenerate: (customPrompt?: string) => void;
}

export default function ChatPanel({
  prompt,
  setPrompt,
  loading,
  statusStep,
  messages,
  partialErrors,
  onGenerate
}: ChatPanelProps) {
  const [showErrorDetails, setShowErrorDetails] = useState(true);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading && prompt.trim()) {
        onGenerate();
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 border-r border-zinc-800/80">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800/70 bg-zinc-900/40">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-md shadow-blue-500/20">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-zinc-100 tracking-tight">Agentic Studio</h1>
            <p className="text-[11px] text-zinc-400">Full-Stack AI Software Engineer</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-zinc-800/60 border border-zinc-700/40 text-[10px] text-zinc-400 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Online</span>
        </div>
      </div>

      {/* Partial Errors Banner (Shown when backend returns partial status) */}
      {partialErrors && partialErrors.length > 0 && (
        <div className="m-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200">
          <div 
            className="flex items-center justify-between cursor-pointer select-none"
            onClick={() => setShowErrorDetails(!showErrorDetails)}
          >
            <div className="flex items-center gap-2 text-xs font-semibold">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Partial Workflow Notice ({partialErrors.length} Issue{partialErrors.length > 1 ? "s" : ""})</span>
            </div>
            <span className="text-[10px] underline font-mono text-amber-300">
              {showErrorDetails ? "Hide" : "Show"}
            </span>
          </div>
          {showErrorDetails && (
            <div className="mt-2 space-y-1.5 pt-2 border-t border-amber-500/20 max-h-40 overflow-y-auto">
              {partialErrors.map((err, idx) => (
                <div key={idx} className="text-[11px] font-mono leading-tight bg-zinc-950/60 p-1.5 rounded border border-amber-500/20">
                  <div className="text-amber-400 font-bold flex items-center justify-between">
                    <span>{err.file}:{err.line}</span>
                    <span className="text-[9px] uppercase tracking-wider px-1 rounded bg-amber-500/20">{err.rule}</span>
                  </div>
                  <div className="text-zinc-300 mt-0.5">{err.message}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3 text-zinc-500">
            <Terminal className="w-10 h-10 opacity-30 text-blue-400" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-zinc-300">Autonomous Web Development Studio</p>
              <p className="text-xs text-zinc-500 max-w-[260px]">
                Describe your desired application. The multi-agent loop writes, reviews, and validates both frontend and backend code.
              </p>
            </div>

            {/* Presets */}
            <div className="w-full space-y-1.5 pt-4 text-left">
              <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider px-1">Example Prompts</div>
              {PRESET_PROMPTS.map((sample, i) => (
                <button
                  key={i}
                  disabled={loading}
                  onClick={() => onGenerate(sample)}
                  className="w-full text-left p-2 rounded-lg bg-zinc-900/60 border border-zinc-800/60 hover:bg-zinc-850 hover:border-zinc-700/80 transition-all text-xs text-zinc-300 group flex items-center justify-between gap-2"
                >
                  <span className="truncate">{sample}</span>
                  <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-blue-400 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-zinc-900 border border-zinc-800 text-zinc-200 shadow-sm"
                }`}
              >
                <div className="whitespace-pre-line">{msg.text}</div>

                {msg.details?.endpoints && msg.details.endpoints.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-zinc-800/80 space-y-1 text-[11px]">
                    <div className="font-semibold text-blue-400">Endpoints Configured:</div>
                    {msg.details.endpoints.slice(0, 4).map((ep, idx) => (
                      <div key={idx} className="font-mono text-[10px] text-zinc-400">
                        <span className="font-bold text-zinc-300">{ep.method}</span> {ep.path}
                      </div>
                    ))}
                    {msg.details.endpoints.length > 4 && (
                      <div className="text-[10px] text-zinc-500 italic">
                        +{msg.details.endpoints.length - 4} more endpoints in Inspector
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Live Status Step */}
        {loading && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
            <span>{statusStep || "Processing agentic cognitive loop..."}</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <div className="p-3 border-t border-zinc-800/70 bg-zinc-900/30">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            rows={3}
            placeholder="Describe an app (e.g., 'Inventory manager with low-stock alerts, REST API, and filters')..."
            className="w-full resize-none rounded-xl bg-zinc-900 border border-zinc-800 p-3 pr-10 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500/80 transition-all shadow-inner"
          />
          <button
            onClick={() => onGenerate()}
            disabled={loading || !prompt.trim()}
            className="absolute bottom-2.5 right-2.5 p-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:hover:bg-blue-600 transition-all shadow-md active:scale-95"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2 px-1 text-[10px] text-zinc-500">
          <span>Press Enter to generate, Shift+Enter for new line</span>
          <span>Dual RAG + Parallel Generation</span>
        </div>
      </div>
    </div>
  );
}
