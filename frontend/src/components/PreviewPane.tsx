"use client";

import { useState } from "react";
import { 
  SandpackProvider, 
  SandpackLayout, 
  SandpackCodeEditor, 
  SandpackPreview,
  SandpackFileExplorer 
} from "@codesandbox/sandpack-react";
import Editor from "./Editor";
import ApiInspector from "./ApiInspector";
import { ApiEndpoint } from "../types/studio";
import { PRESET_PROMPTS } from "../hooks/useGenerate";
import { 
  Eye, 
  Server, 
  Code2, 
  Cpu, 
  Copy, 
  Check, 
  ChevronRight, 
  Sparkles,
  FileCode
} from "lucide-react";

interface PreviewPaneProps {
  files: Record<string, string> | null;
  backendFiles: Record<string, string>;
  apiSpec: ApiEndpoint[];
  plan: string;
  template: "react" | "vanilla";
  dependencies: Record<string, string>;
  activeTab: "preview" | "backend" | "plan";
  setActiveTab: (tab: "preview" | "backend" | "plan") => void;
  onPresetClick: (preset: string) => void;
}

export default function PreviewPane({
  files,
  backendFiles,
  apiSpec,
  plan,
  template,
  dependencies,
  activeTab,
  setActiveTab,
  onPresetClick
}: PreviewPaneProps) {
  const [selectedBackendFile, setSelectedBackendFile] = useState<string>("/server.js");
  const [copiedServerCode, setCopiedServerCode] = useState(false);

  const bKeys = Object.keys(backendFiles || {});
  const activeBackendKey = bKeys.includes(selectedBackendFile)
    ? selectedBackendFile
    : bKeys.find(k => k.toLowerCase().endsWith("server.js")) || bKeys[0] || "/server.js";

  const activeBackendCode = backendFiles[activeBackendKey] || "// Server code will appear here.";

  const handleCopyCode = () => {
    navigator.clipboard.writeText(activeBackendCode);
    setCopiedServerCode(true);
    setTimeout(() => setCopiedServerCode(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-zinc-950">
      {/* Workspace Subheader Navigation */}
      {files && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800/70 bg-zinc-900/40">
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-zinc-950 border border-zinc-800/80">
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "preview"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Live App Preview</span>
            </button>

            <button
              onClick={() => setActiveTab("backend")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "backend"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>Backend & REST API</span>
              {apiSpec.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-500/30 text-indigo-300 font-mono">
                  {apiSpec.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("plan")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "plan"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Architecture Plan</span>
            </button>
          </div>

          <div className="text-[11px] text-zinc-400 font-mono">
            {activeTab === "preview" && "Sandpack React Sandbox"}
            {activeTab === "backend" && "Node.js Express + REST Inspector"}
            {activeTab === "plan" && "LangGraph Multi-Agent Architecture"}
          </div>
        </div>
      )}

      {/* Main Workspace Body */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* State 1: Empty state */}
        {!files && (
          <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
            <div className="max-w-md w-full text-center space-y-6">
              <div className="inline-flex p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 shadow-inner">
                <Cpu className="w-10 h-10 animate-pulse" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold text-zinc-100 tracking-tight">Full-Stack AI Application Developer</h2>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Type a prompt to autonomously engineer both a <span className="text-blue-400 font-semibold">React Frontend</span> and an <span className="text-indigo-400 font-semibold">Express REST Backend</span> with real-time preview and API testing.
                </p>
              </div>

              <div className="pt-2 text-left space-y-2">
                <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3 text-blue-400" />
                  <span>Try an example prompt:</span>
                </div>
                <div className="space-y-1.5">
                  {PRESET_PROMPTS.map((sample, i) => (
                    <button
                      key={i}
                      onClick={() => onPresetClick(sample)}
                      className="w-full text-left p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-850 border border-zinc-800 text-xs text-zinc-300 hover:text-white transition-all flex items-center justify-between group"
                    >
                      <span className="truncate">{sample}</span>
                      <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-blue-400 shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* State 2: Tab 1 - Sandpack React Live Preview */}
        {files && activeTab === "preview" && (
          <div className="flex-1 h-full w-full">
            <SandpackProvider
              template={template}
              theme="dark"
              files={files}
              customSetup={{ dependencies }}
            >
              <SandpackLayout style={{ display: "flex", height: "100%", width: "100%", borderRadius: 0, border: "none" }}>
                <div style={{ display: "flex", flex: 1, minWidth: "380px", borderRight: "1px solid #27272a" }}>
                  <SandpackFileExplorer style={{ width: "28%", minWidth: "150px", height: "100%" }} />
                  <SandpackCodeEditor style={{ flex: 1, height: "100%" }} showLineNumbers showTabs closableTabs />
                </div>
                <div style={{ flex: 1.2, height: "100%" }}>
                  <SandpackPreview style={{ height: "100%", width: "100%" }} showOpenInCodeSandbox={false} showRefreshButton />
                </div>
              </SandpackLayout>
            </SandpackProvider>
          </div>
        )}

        {/* State 3: Tab 2 - Backend Source Inspector & REST Inspector */}
        {files && activeTab === "backend" && (
          <div className="flex-1 flex flex-col h-full overflow-hidden">
            {/* Upper half: Monaco Source Inspector */}
            <div className="flex-1 flex flex-col min-h-0 border-b border-zinc-800/80">
              <div className="flex items-center justify-between px-3 py-2 bg-zinc-900/60 border-b border-zinc-800/70">
                <div className="flex items-center gap-1.5 overflow-x-auto">
                  {bKeys.map((fPath) => (
                    <button
                      key={fPath}
                      onClick={() => setSelectedBackendFile(fPath)}
                      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono transition-all ${
                        activeBackendKey === fPath
                          ? "bg-zinc-800 text-zinc-100 border border-zinc-700/80 shadow-sm"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850"
                      }`}
                    >
                      <FileCode className="w-3.5 h-3.5 text-blue-400" />
                      <span>{fPath}</span>
                    </button>
                  ))}
                </div>

                <button
                  onClick={handleCopyCode}
                  className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition"
                  title="Copy current backend file code"
                >
                  {copiedServerCode ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedServerCode ? "Copied" : "Copy"}</span>
                </button>
              </div>

              <div className="flex-1 min-h-0 bg-zinc-950">
                <Editor
                  value={activeBackendCode}
                  language={activeBackendKey.endsWith(".json") ? "json" : "javascript"}
                  readOnly
                />
              </div>
            </div>

            {/* Lower half: Interactive REST API Inspector */}
            <div className="h-72 min-h-64">
              <ApiInspector apiSpec={apiSpec} />
            </div>
          </div>
        )}

        {/* State 4: Tab 3 - Architecture Plan */}
        {files && activeTab === "plan" && (
          <div className="flex-1 h-full overflow-y-auto p-6 bg-zinc-950 text-zinc-300">
            <div className="max-w-3xl mx-auto space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-zinc-800">
                <Code2 className="w-5 h-5 text-blue-400" />
                <h2 className="text-base font-bold text-zinc-100">Architectural Plan & Specifications</h2>
              </div>
              <pre className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 font-mono text-xs text-zinc-200 whitespace-pre-wrap leading-relaxed">
                {plan || "No architectural plan available."}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
