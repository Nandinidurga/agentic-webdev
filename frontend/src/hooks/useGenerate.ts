"use client";

import { useState } from "react";
import { ApiEndpoint, ChatMessage, GenerationResponse, StructuredError } from "../types/studio";

export const PRESET_PROMPTS = [
  "Task & Priority Tracker with categories, due dates, and completion status",
  "Real-time Crypto & Stock Watchlist with portfolio calculator",
  "E-Commerce Product Catalog with cart, filters, and checkout simulation",
  "Personal Fitness & Workout Log with daily stats and routines"
];

const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useGenerate() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusStep, setStatusStep] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [files, setFiles] = useState<Record<string, string> | null>(null);
  const [rawFiles, setRawFiles] = useState<Record<string, string> | null>(null);
  const [backendFiles, setBackendFiles] = useState<Record<string, string>>({});
  const [frontendFiles, setFrontendFiles] = useState<Record<string, string>>({});
  const [apiSpec, setApiSpec] = useState<ApiEndpoint[]>([]);
  const [plan, setPlan] = useState<string>("");
  const [partialErrors, setPartialErrors] = useState<StructuredError[]>([]);
  const [template, setTemplate] = useState<"react" | "vanilla">("react");
  const [dependencies, setDependencies] = useState<Record<string, string>>({
    "lucide-react": "latest",
    "tailwindcss": "latest"
  });

  const handleGenerate = async (customPrompt?: string) => {
    const promptToUse = (customPrompt || prompt).trim() || PRESET_PROMPTS[0];
    if (!promptToUse) return;

    setLoading(true);
    setStatusStep("Planning full-stack architecture...");
    setPartialErrors([]);
    setMessages(prev => [...prev, { role: "user", text: promptToUse }]);

    const timers: NodeJS.Timeout[] = [];
    const clearTimers = () => {
      timers.forEach(t => clearTimeout(t));
      timers.length = 0;
    };

    try {
      timers.push(setTimeout(() => setStatusStep("Synthesizing technical documentation & RAG context..."), 2000));
      timers.push(setTimeout(() => setStatusStep("Generating Express.js REST API & React components in parallel..."), 4500));
      timers.push(setTimeout(() => setStatusStep("Running Reviewer static validation & AST syntax checks..."), 9000));

      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const candidateEndpoints = Array.from(new Set([
        `${DEFAULT_API_URL.replace(/\/+$/, "")}/generate`,
        `http://${host}:8000/generate`,
        "http://localhost:8000/generate",
        "http://127.0.0.1:8000/generate"
      ]));

      let data: GenerationResponse | null = null;
      let lastError: Error | null = null;

      for (const endpointUrl of candidateEndpoints) {
        try {
          const res = await fetch(endpointUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: promptToUse }),
          });

          const resData: GenerationResponse = await res.json().catch(() => null);

          if (res.ok && resData && resData.status !== "error") {
            data = resData;
            break;
          } else {
            const errMsg = resData?.message || `Server returned ${res.status}: ${res.statusText}`;
            lastError = new Error(errMsg);
            if (resData && resData.message) break;
          }
        } catch (err: unknown) {
          lastError = err instanceof Error ? err : new Error(String(err));
        }
      }

      clearTimers();

      if (!data) {
        throw lastError || new Error(`Failed to connect to backend at ${DEFAULT_API_URL}. Please verify the FastAPI server is running: uvicorn main:app --reload --port 8000`);
      }

      const backendCount = Object.keys(data.backend_files || {}).length;
      const frontendCount = Object.keys(data.frontend_files || {}).length;
      const remainingErrors: StructuredError[] = Array.isArray(data.errors) ? data.errors : [];
      setPartialErrors(remainingErrors);

      const isPartial = data.status === "partial" || remainingErrors.length > 0;
      const completionText = isPartial
        ? `Full-Stack generation completed with partial issues:\n• Created ${backendCount} Backend files (Node.js/Express)\n• Created ${frontendCount} Frontend files (React + Tailwind)\n• ${remainingErrors.length} remaining validator issue(s) detected.`
        : `Full-Stack generation complete!\n• Created ${backendCount} Backend files (Node.js/Express)\n• Created ${frontendCount} Frontend files (React + Tailwind)\n• Configured ${data.api_spec?.length || 0} REST API Endpoints`;

      setMessages(prev => [...prev, {
        role: "agent",
        text: completionText,
        details: {
          backendFiles: Object.keys(data?.backend_files || {}),
          frontendFiles: Object.keys(data?.frontend_files || {}),
          endpoints: data?.api_spec || [],
          errors: remainingErrors
        }
      }]);

      setPlan(data.plan || "");
      setApiSpec(data.api_spec || []);
      setBackendFiles(data.backend_files || {});
      setFrontendFiles(data.frontend_files || {});
      setRawFiles(data.files || {});

      if (data.files && Object.keys(data.files).length > 0) {
        const fileKeys = Object.keys(data.files).map(k => k.toLowerCase());
        const isVanilla = fileKeys.some(k => k.includes("index.html")) && !fileKeys.some(k => k.includes("app.js") || k.includes("app.jsx") || k.includes("react"));
        setTemplate(isVanilla ? "vanilla" : "react");

        const formattedFiles: Record<string, string> = {};
        let parsedDependencies: Record<string, string> = {
          "lucide-react": "latest",
          "tailwindcss": "latest"
        };

        for (const [key, value] of Object.entries(data.files)) {
          let safeKey = key.startsWith("/") ? key : `/${key}`;
          const lowerKey = safeKey.toLowerCase();

          // Exclude backend server files from Sandpack browser preview
          if (lowerKey.startsWith("/server") || lowerKey.includes("server.js")) {
            continue;
          }

          if (lowerKey.endsWith("package.json")) {
            try {
              const parsed = JSON.parse(value);
              if (parsed?.dependencies && typeof parsed.dependencies === "object") {
                parsedDependencies = { ...parsedDependencies, ...parsed.dependencies };
              }
            } catch {
              // Ignore client package.json formatting anomalies
            }
            continue;
          }

          if (isVanilla) {
            if (lowerKey.endsWith("index.html")) safeKey = "/index.html";
            if (lowerKey.endsWith("script.js") || lowerKey.endsWith("main.js") || lowerKey.endsWith("index.js")) safeKey = "/index.js";
            if (lowerKey.endsWith("style.css") || lowerKey.endsWith("styles.css")) safeKey = "/styles.css";
          } else {
            if (lowerKey.endsWith("app.jsx") || lowerKey.endsWith("app.js") || lowerKey.endsWith("app.tsx")) {
              safeKey = "/App.js";
            }
            if (lowerKey.endsWith("index.css") || lowerKey.endsWith("styles.css") || lowerKey.endsWith("globals.css")) {
              safeKey = "/styles.css";
            }
          }

          let fileContent = typeof value === "string" ? value : String(value);

          // Auto-detect package imports in JS/JSX
          if (safeKey.endsWith(".js") || safeKey.endsWith(".jsx") || safeKey.endsWith(".tsx") || safeKey.endsWith(".ts")) {
            const importRegex = /import\s+(?:.*from\s+)?['"]([^'".\\]+)['"]/g;
            let match: RegExpExecArray | null;
            while ((match = importRegex.exec(fileContent)) !== null) {
              const pkgName = match[1];
              if (!pkgName.startsWith(".") && !pkgName.startsWith("/") && !pkgName.startsWith("react/") && pkgName !== "react" && pkgName !== "react-dom") {
                const basePkg = pkgName.startsWith("@") ? pkgName.split("/").slice(0, 2).join("/") : pkgName.split("/")[0];
                parsedDependencies[basePkg] = "latest";
              }
            }
          }

          if (safeKey === "/App.js") {
            fileContent = fileContent.replace(/import\s+['"](?:\.\/)?(?:index\.css|globals\.css)['"]\s*;?/g, "import './styles.css';");
          }

          formattedFiles[safeKey] = fileContent;
        }

        // Guarantee fallback mock API client if /App.js imports api but /services/api.js is absent
        if (!formattedFiles["/services/api.js"] && formattedFiles["/App.js"]?.includes("services/api")) {
          formattedFiles["/services/api.js"] = `// Auto-generated fallback preview store\nlet store = [];\nexport const api = {\n  getAll: async () => [...store],\n  create: async (item) => { const n = { id: Date.now(), ...item }; store.push(n); return n; },\n  update: async (id, item) => { store = store.map(x => x.id == id ? { ...x, ...item } : x); return item; },\n  delete: async (id) => { store = store.filter(x => x.id != id); return { success: true }; },\n  health: async () => ({ status: 'ok', mode: 'sandpack-preview' })\n};\nexport default api;\n`;
        }

        setDependencies(parsedDependencies);
        setFiles(formattedFiles);

        // Confetti celebration on success
        try {
          const confettiModule = await import("canvas-confetti");
          const confetti = confettiModule.default || confettiModule;
          confetti({ particleCount: 75, spread: 80, origin: { y: 0.6 } });
        } catch {
          // Non-critical confetti fallback
        }
      }
    } catch (error: unknown) {
      console.error(error);
      const errMsg = error instanceof Error ? error.message : "Error connecting to AI Orchestrator backend.";
      setMessages(prev => [...prev, {
        role: "agent",
        text: `Generation Failed: ${errMsg}\n\nPlease verify your Python FastAPI server is running: uvicorn main:app --reload --port 8000`
      }]);
    } finally {
      clearTimers();
      setLoading(false);
      setStatusStep("");
      setPrompt("");
    }
  };

  return {
    prompt,
    setPrompt,
    loading,
    statusStep,
    messages,
    files,
    rawFiles,
    backendFiles,
    frontendFiles,
    apiSpec,
    plan,
    partialErrors,
    template,
    dependencies,
    handleGenerate
  };
}
