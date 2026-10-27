"use client";

import { useState } from "react";
import { useGenerate } from "../hooks/useGenerate";
import ChatPanel from "../components/ChatPanel";
import PreviewPane from "../components/PreviewPane";
import ExportButton from "../components/ExportButton";
import { Sparkles } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"preview" | "backend" | "plan">("preview");

  const {
    prompt,
    setPrompt,
    loading,
    statusStep,
    messages,
    files,
    rawFiles,
    backendFiles,
    apiSpec,
    plan,
    partialErrors,
    template,
    dependencies,
    handleGenerate
  } = useGenerate();

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-zinc-950 text-zinc-100 font-sans antialiased">
      {/* Top Application Header */}
      <header className="h-12 border-b border-zinc-800/80 bg-zinc-950 px-4 flex items-center justify-between shrink-0 z-20">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-md shadow-blue-500/20">
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <div className="text-xs font-bold text-zinc-100 tracking-tight flex items-center gap-2">
              <span>Agentic IDE</span>
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                Full-Stack Studio
              </span>
            </div>
          </div>
        </div>

        {/* Global Action Bar */}
        <div className="flex items-center gap-2">
          <ExportButton rawFiles={rawFiles} />
        </div>
      </header>

      {/* Main Split Body: Left Chat Panel, Right Preview Pane */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Left Column: Chat & Prompt Panel */}
        <div className="w-96 min-w-[320px] max-w-[420px] h-full shrink-0">
          <ChatPanel
            prompt={prompt}
            setPrompt={setPrompt}
            loading={loading}
            statusStep={statusStep}
            messages={messages}
            partialErrors={partialErrors}
            onGenerate={handleGenerate}
          />
        </div>

        {/* Right Column: Code Preview & REST Inspector Workspace */}
        <div className="flex-1 h-full min-w-0">
          <PreviewPane
            files={files}
            backendFiles={backendFiles}
            apiSpec={apiSpec}
            plan={plan}
            template={template}
            dependencies={dependencies}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            onPresetClick={(preset) => handleGenerate(preset)}
          />
        </div>
      </div>
    </div>
  );
}
