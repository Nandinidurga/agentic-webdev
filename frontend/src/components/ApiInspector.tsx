"use client";

import { useState } from "react";
import { ApiEndpoint, TestResult } from "../types/studio";
import { Play, Terminal, Zap, AlertTriangle, CheckCircle2 } from "lucide-react";

interface ApiInspectorProps {
  apiSpec: ApiEndpoint[];
}

const DEFAULT_EXPRESS_URL = process.env.NEXT_PUBLIC_EXPRESS_URL || "http://localhost:5000";

export default function ApiInspector({ apiSpec }: ApiInspectorProps) {
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpoint | null>(apiSpec[0] || null);
  const [customPayload, setCustomPayload] = useState<string>("");
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testingApi, setTestingApi] = useState(false);

  const handleSelectEndpoint = (ep: ApiEndpoint) => {
    setSelectedEndpoint(ep);
    setTestResult(null);
    if (ep.sampleRequest) {
      setCustomPayload(JSON.stringify(ep.sampleRequest, null, 2));
    } else {
      setCustomPayload("");
    }
  };

  const handleTestEndpoint = async (endpoint: ApiEndpoint) => {
    setTestingApi(true);
    const startTime = performance.now();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);

      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const resolvedPath = endpoint.path.replace(/:[a-zA-Z0-9_]+/g, "1");
      const expressBase = DEFAULT_EXPRESS_URL.replace(/\/+$/, "");
      const targetUrl = expressBase.includes("localhost") && host !== "localhost"
        ? `http://${host}:5000${resolvedPath}`
        : `${expressBase}${resolvedPath}`;

      let parsedBody: unknown = undefined;
      if (endpoint.method !== "GET") {
        if (customPayload.trim()) {
          try {
            parsedBody = JSON.parse(customPayload);
          } catch {
            parsedBody = endpoint.sampleRequest;
          }
        } else if (endpoint.sampleRequest) {
          parsedBody = endpoint.sampleRequest;
        }
      }

      const res = await fetch(targetUrl, {
        method: endpoint.method,
        headers: { "Content-Type": "application/json" },
        body: parsedBody ? JSON.stringify(parsedBody) : undefined,
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const duration = Math.round(performance.now() - startTime);
      const data = await res.json().catch(() => ({}));
      setTestResult({
        status: res.status,
        duration,
        data,
        source: `Live Express Server (${expressBase})`,
        isSimulated: false
      });
    } catch {
      // Fallback: simulate response using endpoint sampleResponse or in-memory preview data
      const duration = Math.round(performance.now() - startTime) + 35;
      setTestResult({
        status: 200,
        duration,
        data: endpoint.sampleResponse || { message: "Simulated preview response" },
        source: "In-Memory Virtual Store (Simulated Fallback)",
        isSimulated: true // Explicitly marked as simulated; never shown with green indicator
      });
    } finally {
      setTestingApi(false);
    }
  };

  if (!apiSpec || apiSpec.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-zinc-500">
        <Terminal className="w-10 h-10 mb-3 opacity-40 text-blue-400" />
        <p className="text-sm font-medium text-zinc-400">No REST endpoints detected.</p>
        <p className="text-xs text-zinc-600 mt-1">Endpoints will appear here once the backend architecture is planned.</p>
      </div>
    );
  }

  const activeEp = selectedEndpoint || apiSpec[0];

  return (
    <div className="flex flex-col h-full bg-zinc-950/80 border-t border-zinc-800/60 overflow-hidden">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800/60 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold text-zinc-200">REST API Inspector</span>
          <span className="px-1.5 py-0.5 text-[10px] rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
            {apiSpec.length} route{apiSpec.length > 1 ? "s" : ""}
          </span>
        </div>
        <div className="text-[11px] text-zinc-400 font-mono flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Target: {DEFAULT_EXPRESS_URL}</span>
        </div>
      </div>

      <div className="grid grid-cols-12 flex-1 min-h-0 divide-x divide-zinc-800/50">
        {/* Left column: Endpoint List */}
        <div className="col-span-5 overflow-y-auto p-2 space-y-1.5">
          {apiSpec.map((ep, idx) => {
            const isSelected = activeEp?.path === ep.path && activeEp?.method === ep.method;
            const methodColor = 
              ep.method === "GET" ? "bg-blue-500/10 text-blue-400 border-blue-500/30" :
              ep.method === "POST" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" :
              ep.method === "DELETE" ? "bg-rose-500/10 text-rose-400 border-rose-500/30" :
              "bg-amber-500/10 text-amber-400 border-amber-500/30";

            return (
              <button
                key={`${ep.method}-${ep.path}-${idx}`}
                onClick={() => handleSelectEndpoint(ep)}
                className={`w-full text-left p-2.5 rounded-lg border transition-all text-xs flex items-center justify-between gap-2 ${
                  isSelected
                    ? "bg-zinc-800/90 border-blue-500/40 shadow-sm"
                    : "bg-zinc-900/40 border-zinc-800/40 hover:bg-zinc-850 hover:border-zinc-700/60"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`px-2 py-0.5 text-[10px] font-bold rounded border font-mono ${methodColor}`}>
                    {ep.method}
                  </span>
                  <span className="font-mono text-zinc-200 truncate">{ep.path}</span>
                </div>
                <span className="text-[10px] text-zinc-500 truncate max-w-[120px]">{ep.description}</span>
              </button>
            );
          })}
        </div>

        {/* Right column: Execution Console & Output */}
        <div className="col-span-7 flex flex-col p-3 overflow-y-auto space-y-3">
          {activeEp && (
            <>
              {/* Endpoint Header & Trigger Button */}
              <div className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800/60">
                <div className="flex items-center gap-2 font-mono text-xs text-zinc-200">
                  <span className="font-bold text-blue-400">{activeEp.method}</span>
                  <span>{activeEp.path}</span>
                </div>
                <button
                  onClick={() => handleTestEndpoint(activeEp)}
                  disabled={testingApi}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-sm active:scale-95 disabled:opacity-50"
                >
                  <Play className={`w-3.5 h-3.5 ${testingApi ? "animate-spin" : ""}`} />
                  <span>{testingApi ? "Testing..." : "Send Request"}</span>
                </button>
              </div>

              {/* Editable Payload Editor for mutating methods */}
              {activeEp.method !== "GET" && (
                <div>
                  <div className="text-[11px] font-semibold text-zinc-400 mb-1 flex items-center gap-1">
                    <Zap className="w-3 h-3 text-amber-400" />
                    <span>Request Body (JSON)</span>
                  </div>
                  <textarea
                    value={customPayload}
                    onChange={(e) => setCustomPayload(e.target.value)}
                    rows={4}
                    className="w-full p-2 text-xs font-mono rounded bg-zinc-900 border border-zinc-800 text-zinc-200 focus:outline-none focus:border-blue-500"
                    placeholder="{ 'key': 'value' }"
                  />
                </div>
              )}

              {/* Execution Result */}
              {testResult && (
                <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/70 p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {testResult.isSimulated ? (
                        <div className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-bold rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 font-mono">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>SIMULATED (200 MOCK)</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 px-2 py-0.5 text-xs font-bold rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>LIVE HTTP {testResult.status}</span>
                        </div>
                      )}
                      <span className="text-xs text-zinc-400 font-mono">{testResult.duration}ms</span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono truncate max-w-[200px]">
                      {testResult.source}
                    </span>
                  </div>

                  {testResult.isSimulated && (
                    <div className="text-[11px] p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-200/90 leading-tight">
                      ⚠️ <strong>Simulated Response:</strong> Live Express backend is not running on port 5000. Displaying mock preview data from application specification.
                    </div>
                  )}

                  <div className="text-[11px] font-semibold text-zinc-400">Response Data:</div>
                  <pre className="p-2.5 rounded bg-zinc-950 border border-zinc-800/60 font-mono text-xs text-zinc-300 overflow-x-auto max-h-48">
                    {JSON.stringify(testResult.data, null, 2)}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
