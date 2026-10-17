"use client";

import { useState } from "react";
import { 
  SandpackProvider, 
  SandpackLayout, 
  SandpackCodeEditor, 
  SandpackPreview,
  SandpackFileExplorer
} from "@codesandbox/sandpack-react";
import { 
  Layers, 
  Server, 
  Terminal, 
  Play, 
  CheckCircle2, 
  Sparkles, 
  Download, 
  Copy, 
  Check, 
  ChevronRight, 
  ExternalLink,
  Code2,
  Cpu,
  FileCode,
  Send,
  Zap,
  RefreshCw,
  Eye
} from "lucide-react";

interface ApiEndpoint {
  method: string;
  path: string;
  description: string;
  sampleRequest?: any;
  sampleResponse?: any;
}

// Polyfill window.crypto.subtle.digest for non-localhost/HTTP contexts (e.g. LAN IP 100.126.227.102)
if (typeof window !== "undefined") {
  if (!window.crypto) {
    (window as any).crypto = {};
  }
  if (!window.crypto.subtle || typeof window.crypto.subtle.digest !== "function") {
    const sha256 = (bytes: BufferSource): ArrayBuffer => {
      const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes as ArrayBuffer);
      const K = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
      ];
      const H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
      const bitLen = b.length * 8;
      const newLen = (((b.length + 8) >> 6) + 1) << 6;
      const p = new Uint8Array(newLen);
      p.set(b);
      p[b.length] = 0x80;
      const v = new DataView(p.buffer);
      v.setUint32(newLen - 4, bitLen >>> 0);
      v.setUint32(newLen - 8, Math.floor(bitLen / 0x100000000));
      const W = new Uint32Array(64);
      for (let i = 0; i < newLen; i += 64) {
        for (let t = 0; t < 16; t++) W[t] = v.getUint32(i + t * 4);
        for (let t = 16; t < 64; t++) {
          const s0 = ((W[t-15] >>> 7) | (W[t-15] << 25)) ^ ((W[t-15] >>> 18) | (W[t-15] << 14)) ^ (W[t-15] >>> 3);
          const s1 = ((W[t-2] >>> 17) | (W[t-2] << 15)) ^ ((W[t-2] >>> 19) | (W[t-2] << 13)) ^ (W[t-2] >>> 10);
          W[t] = (W[t-16] + s0 + W[t-7] + s1) | 0;
        }
        let a = H[0], b_ = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
        for (let t = 0; t < 64; t++) {
          const S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
          const ch = (e & f) ^ (~e & g);
          const temp1 = (h + S1 + ch + K[t] + W[t]) | 0;
          const S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
          const maj = (a & b_) ^ (a & c) ^ (b_ & c);
          const temp2 = (S0 + maj) | 0;
          h = g; g = f; f = e; e = (d + temp1) | 0; d = c; c = b_; b_ = a; a = (temp1 + temp2) | 0;
        }
        H[0] = (H[0] + a) | 0; H[1] = (H[1] + b_) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
        H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
      }
      const res = new ArrayBuffer(32);
      const out = new DataView(res);
      for (let j = 0; j < 8; j++) out.setUint32(j * 4, H[j]);
      return res;
    };

    const subtlePolyfill = {
      digest: async (_algo: any, data: BufferSource) => sha256(data)
    };

    try {
      Object.defineProperty(window.crypto, "subtle", { value: subtlePolyfill, configurable: true, writable: true });
    } catch {
      (window.crypto as any).subtle = subtlePolyfill;
    }
  }
}

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusStep, setStatusStep] = useState<string>("");
  const [messages, setMessages] = useState<{ role: string; text: string; details?: any }[]>([]);
  const [files, setFiles] = useState<Record<string, string> | null>(null);
  const [rawFiles, setRawFiles] = useState<Record<string, string> | null>(null);
  const [backendFiles, setBackendFiles] = useState<Record<string, string>>({});
  const [frontendFiles, setFrontendFiles] = useState<Record<string, string>>({});
  const [apiSpec, setApiSpec] = useState<ApiEndpoint[]>([]);
  const [plan, setPlan] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"preview" | "backend" | "plan">("preview");
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpoint | null>(null);
  const [testResult, setTestResult] = useState<{ status: number; duration: number; data: any; source: string } | null>(null);
  const [testingApi, setTestingApi] = useState(false);
  const [copiedServerCode, setCopiedServerCode] = useState(false);
  const [exportingZip, setExportingZip] = useState(false);
  const [template, setTemplate] = useState<"react" | "vanilla">("react");
  const [dependencies, setDependencies] = useState<Record<string, string>>({
    "lucide-react": "latest",
    "tailwindcss": "latest"
  });

  const presetPrompts = [
    "Task & Priority Tracker with categories, due dates, and completion status",
    "Real-time Crypto & Stock Watchlist with portfolio calculator",
    "E-Commerce Product Catalog with cart, filters, and checkout simulation",
    "Personal Fitness & Workout Log with daily stats and routines"
  ];

  const handleGenerate = async (customPrompt?: string) => {
    const promptToUse = (customPrompt || prompt).trim() || presetPrompts[0];
    if (!promptToUse) return;
    
    setLoading(true);
    setStatusStep("Planning full-stack architecture...");
    setMessages(prev => [...prev, { role: 'user', text: promptToUse }]);
    
    const timers: NodeJS.Timeout[] = [];
    const clearTimers = () => {
      timers.forEach(t => clearTimeout(t));
      timers.length = 0;
    };

    try {
      // Step-by-step progress simulation while waiting for LangGraph
      timers.push(setTimeout(() => setStatusStep("Synthesizing technical documentation & RAG context..."), 2500));
      timers.push(setTimeout(() => setStatusStep("Generating Express.js REST API & React components..."), 6000));
      timers.push(setTimeout(() => setStatusStep("Running Reviewer Agent verification & self-healing..."), 12000));

      // Attempt multiple direct backend endpoints
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const candidateEndpoints = Array.from(new Set([
        `http://${host}:8000/generate`,
        "http://localhost:8000/generate",
        "http://127.0.0.1:8000/generate"
      ]));

      let data: any = null;
      let lastError: any = null;

      for (const endpointUrl of candidateEndpoints) {
        try {
          const res = await fetch(endpointUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: promptToUse }),
          });

          const resData = await res.json().catch(() => null);

          if (res.ok && resData && resData.status !== "error") {
            data = resData;
            break;
          } else {
            const errMsg = resData?.detail || resData?.message || `Server returned ${res.status}: ${res.statusText}`;
            lastError = new Error(errMsg);
            // If FastAPI backend successfully replied with JSON error details, no need to retry other endpoints
            if (resData && (resData.detail || resData.message)) {
              break;
            }
          }
        } catch (err: any) {
          lastError = err;
        }
      }

      clearTimers();

      if (!data) {
        throw lastError || new Error("Failed to connect to backend on port 8000. Please ensure the Python server is running: uvicorn main:app --reload --port 8000");
      }
      
      const fileCount = Object.keys(data.files || {}).length;
      const backendCount = Object.keys(data.backend_files || {}).length;
      const frontendCount = Object.keys(data.frontend_files || {}).length;
      
      setMessages(prev => [...prev, {
        role: 'agent', 
        text: `Full-Stack generation complete!\n• Created ${backendCount} Backend files (Node.js/Express)\n• Created ${frontendCount} Frontend files (React + Tailwind)\n• Configured ${data.api_spec?.length || 0} REST API Endpoints`,
        details: {
          backendFiles: Object.keys(data.backend_files || {}),
          frontendFiles: Object.keys(data.frontend_files || {}),
          endpoints: data.api_spec || []
        }
      }]);

      setPlan(data.plan || "");
      setApiSpec(data.api_spec || []);
      setBackendFiles(data.backend_files || {});
      setFrontendFiles(data.frontend_files || {});
      setRawFiles(data.files || {});

      if (data.api_spec && data.api_spec.length > 0) {
        setSelectedEndpoint(data.api_spec[0]);
      }

      if (data.files && Object.keys(data.files).length > 0) {
        const fileKeys = Object.keys(data.files).map(k => k.toLowerCase());
        const isVanilla = fileKeys.some(k => k.includes('index.html')) && !fileKeys.some(k => k.includes('app.js') || k.includes('app.jsx') || k.includes('react'));
        
        setTemplate(isVanilla ? "vanilla" : "react");

        const formattedFiles: Record<string, string> = {};
        let parsedDependencies: Record<string, string> = {
            "lucide-react": "latest",
            "tailwindcss": "latest"
        };

        const parsePackageJson = (content: any): Record<string, string> => {
            if (!content) return {};
            if (typeof content === 'object' && content !== null) {
                return (content.dependencies && typeof content.dependencies === 'object') ? content.dependencies : {};
            }
            if (typeof content !== 'string') return {};

            let clean = content.trim();
            clean = clean.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
            clean = clean.replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');
            clean = clean.replace(/,\s*([}\]])/g, '$1');

            try {
                const parsed = JSON.parse(clean);
                return (parsed && typeof parsed.dependencies === 'object') ? parsed.dependencies : {};
            } catch {
                try {
                    const doubleQuoted = clean.replace(/'/g, '"');
                    const parsed = JSON.parse(doubleQuoted);
                    return (parsed && typeof parsed.dependencies === 'object') ? parsed.dependencies : {};
                } catch {
                    const deps: Record<string, string> = {};
                    const depMatch = clean.match(/["']dependencies["']\s*:\s*\{([^}]+)\}/i);
                    if (depMatch) {
                        const pairRegex = /["']([^"']+)["']\s*:\s*["']([^"']+)["']/g;
                        let m;
                        while ((m = pairRegex.exec(depMatch[1])) !== null) {
                            deps[m[1]] = m[2];
                        }
                    }
                    return deps;
                }
            }
        };

        for (const [key, value] of Object.entries(data.files)) {
            let safeKey = key.startsWith('/') ? key : `/${key}`;
            const lowerKey = safeKey.toLowerCase();
            
            // 1. Exclude backend server files from Sandpack client preview to prevent Node.js module conflicts
            if (lowerKey.startsWith('/server') || lowerKey.includes('server.js')) {
                continue;
            }

            // 2. Safely collect package dependencies without throwing SyntaxErrors
            if (lowerKey.endsWith('package.json')) {
                const deps = parsePackageJson(value);
                if (deps && Object.keys(deps).length > 0) {
                    parsedDependencies = { ...parsedDependencies, ...deps };
                }
                continue; // Do not include package.json in Sandpack directly to avoid template conflicts
            }

            if (isVanilla) {
                if (lowerKey.endsWith('index.html')) safeKey = '/index.html';
                if (lowerKey.endsWith('script.js') || lowerKey.endsWith('main.js') || lowerKey.endsWith('index.js')) safeKey = '/index.js';
                if (lowerKey.endsWith('style.css') || lowerKey.endsWith('styles.css')) safeKey = '/styles.css';
            } else {
                // Ensure main React component is /App.js
                if (lowerKey.endsWith('app.jsx') || lowerKey.endsWith('app.js') || lowerKey.endsWith('app.tsx')) {
                    safeKey = '/App.js';
                }
                
                // Ensure styles are in /styles.css
                if (lowerKey.endsWith('index.css') || lowerKey.endsWith('styles.css') || lowerKey.endsWith('globals.css')) {
                    safeKey = '/styles.css';
                }
            }

            let fileContent = typeof value === 'string' ? value : String(value);

            // Auto-detect imports for external packages
            if (safeKey.endsWith('.js') || safeKey.endsWith('.jsx') || safeKey.endsWith('.tsx') || safeKey.endsWith('.ts')) {
                const importRegex = /import\s+(?:.*from\s+)?['"]([^'".\\]+)['"]/g;
                let match;
                while ((match = importRegex.exec(fileContent)) !== null) {
                    const pkgName = match[1];
                    if (!pkgName.startsWith('.') && !pkgName.startsWith('/') && !pkgName.startsWith('react/') && pkgName !== 'react' && pkgName !== 'react-dom') {
                         let basePkg = pkgName;
                         if (pkgName.startsWith('@')) {
                             const parts = pkgName.split('/');
                             if (parts.length > 1) {
                                 basePkg = parts[0] + '/' + parts[1];
                             }
                         } else {
                             basePkg = pkgName.split('/')[0];
                         }
                         parsedDependencies[basePkg] = "latest";
                    }
                }

                // Defensive React code sanitization: immunity against runtime map/null/undefined crashes in Sandpack
                // 1. Uninitialized useState() or useState(undefined)
                fileContent = fileContent.replace(/useState\s*\(\s*\)/g, "useState([])");
                fileContent = fileContent.replace(/useState\s*\(\s*undefined\s*\)/g, "useState([])");

                // 2. Defensive array methods: map, filter, reduce, forEach, some, every, slice
                // Automatically wraps `expenses.map(...)` -> `(expenses || []).map(...)`
                const arrayMethodsRegex = /(?<![\)\w\?\]])\b([a-zA-Z_$][a-zA-Z0-9_$]*(?:\.[a-zA-Z_$][a-zA-Z0-9_$]*)*)\.(map|filter|reduce|forEach|some|every|slice)\(/g;
                fileContent = fileContent.replace(arrayMethodsRegex, (m, varChain, method) => {
                    if (['Array', 'React', 'Promise', 'Object'].includes(varChain.split('.')[0])) return m;
                    return `(${varChain} || []).${method}(`;
                });

                // 3. Defensive number formatting: amount.toFixed(2) -> (Number(amount) || 0).toFixed(2)
                const toFixedRegex = /(?<!Number\()(?<!\|\|\s*0\)\.)(?<![\.\)\]\w])\b([a-zA-Z_$][a-zA-Z0-9_$\.]*)\.toFixed\(/g;
                fileContent = fileContent.replace(toFixedRegex, (m, expr) => {
                    return `(Number(${expr}) || 0).toFixed(`;
                });
            }
            
            // Rewrite style imports in App.js
            if (safeKey === '/App.js') {
                fileContent = fileContent.replace(/import\s+['"](?:\.\/)?(?:index\.css|globals\.css)['"]\s*;?/g, "import './styles.css';");
            }

            formattedFiles[safeKey] = fileContent;
        }

        // Guarantee fallback mock API client if /App.js imports api but /services/api.js is missing
        if (!formattedFiles['/services/api.js'] && formattedFiles['/App.js'] && formattedFiles['/App.js'].includes('services/api')) {
            formattedFiles['/services/api.js'] = `// Auto-generated fallback preview store
let store = [];
export const api = {
    getAll: async () => [...store],
    create: async (item) => { const n = { id: Date.now(), ...item }; store.push(n); return n; },
    update: async (id, item) => { store = store.map(x => x.id == id ? { ...x, ...item } : x); return item; },
    delete: async (id) => { store = store.filter(x => x.id != id); return { success: true }; },
    health: async () => ({ status: 'ok', mode: 'sandpack-preview' })
};
export default api;
`;
        }
        
        setDependencies(parsedDependencies);
        setFiles(formattedFiles);
      }
    } catch (error: any) {
      console.error(error);
      const errMsg = error?.message || "Error connecting to AI Orchestrator backend.";
      setMessages(prev => [...prev, { 
        role: 'agent', 
        text: `Generation Failed: ${errMsg}\n\nPlease ensure the Python FastAPI backend is running: \`uvicorn main:app --reload --port 8000\`` 
      }]);
    } finally {
      clearTimers();
      setLoading(false);
      setStatusStep("");
      setPrompt("");
    }
  };

  const handleTestEndpoint = async (endpoint: ApiEndpoint) => {
    setTestingApi(true);
    const startTime = performance.now();
    
    try {
      // First try live backend on port 5000
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1200);

      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const targetUrl = `http://${host}:5000${endpoint.path}`;
      const res = await fetch(targetUrl, {
        method: endpoint.method,
        headers: { "Content-Type": "application/json" },
        body: (endpoint.method !== 'GET' && endpoint.sampleRequest) ? JSON.stringify(endpoint.sampleRequest) : undefined,
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const duration = Math.round(performance.now() - startTime);
      const data = await res.json();
      setTestResult({
        status: res.status,
        duration,
        data,
        source: "Live Server (http://localhost:5000)"
      });
    } catch (err) {
      // Graceful fallback: return mock data derived from API spec / server code
      const duration = Math.round(performance.now() - startTime) + 15;
      const fallbackData = endpoint.sampleResponse || {
        status: "success",
        message: `Endpoint ${endpoint.method} ${endpoint.path} simulated successfully`,
        data: endpoint.sampleRequest ? { id: 101, ...endpoint.sampleRequest, createdAt: new Date().toISOString() } : [{ id: 1, title: "Sample Item", status: "active" }]
      };
      
      setTestResult({
        status: 200,
        duration,
        data: fallbackData,
        source: "In-Memory Simulation (Local Server Offline)"
      });
    } finally {
      setTestingApi(false);
    }
  };

  const getServerCode = () => {
    if (!rawFiles) return "";
    for (const [path, code] of Object.entries(rawFiles)) {
      if (path.toLowerCase().endsWith("server.js")) {
        return code;
      }
    }
    return "// Express server.js will appear here once generated.";
  };

  const copyServerCode = () => {
    const code = getServerCode();
    navigator.clipboard.writeText(code);
    setCopiedServerCode(true);
    setTimeout(() => setCopiedServerCode(false), 2000);
  };

  const downloadFullstackProject = async () => {
    if (!rawFiles) return;
    setExportingZip(true);
    try {
      const JSZipModule = await import("jszip");
      const JSZip = JSZipModule.default || JSZipModule;
      const zip = new JSZip();

      // Root Readme
      const readmeContent = `# Full-Stack Application Bundle\nGenerated autonomously by Agentic IDE.\n\n## 📁 Architecture\n- \\`/server\\`: Node.js + Express REST API Backend\n- \\`/client\\`: React 19 + Tailwind Interactive Frontend\n\n## 🚀 Quickstart Guide\n\n### 1. Launch the Backend Server\n\\`\\`\\`bash\ncd server\nnpm install\nnpm start\n\\`\\`\\`\nServer runs at http://localhost:5000 with CORS and REST endpoints.\n\n### 2. Launch the Frontend Client\n\\`\\`\\`bash\ncd client\nnpm install\nnpm start\n\\`\\`\\`\nFrontend opens at http://localhost:3000 and connects to the backend on port 5000.\n`;
      zip.file("README.md", readmeContent);

      const serverFolder = zip.folder("server");
      const clientFolder = zip.folder("client");
      const clientSrcFolder = clientFolder?.folder("src");
      const clientServicesFolder = clientSrcFolder?.folder("services");

      let hasServerPkg = false;
      let hasClientPkg = false;

      for (const [path, fileVal] of Object.entries(rawFiles)) {
        const cleanPath = path.startsWith("/") ? path.slice(1) : path;
        const lower = cleanPath.toLowerCase();

        if (lower.startsWith("server/") || lower === "server.js") {
          const subPath = cleanPath.replace(/^server\//i, "");
          serverFolder?.file(subPath, fileVal);
          if (subPath === "package.json") hasServerPkg = true;
        } else if (lower.endsWith("package.json") && !lower.includes("server")) {
          clientFolder?.file("package.json", fileVal);
          hasClientPkg = true;
        } else if (lower.includes("services/api.js") || lower.endsWith("api.js")) {
          clientServicesFolder?.file("api.js", fileVal);
        } else if (lower.endsWith("styles.css") || lower.endsWith("index.css") || lower.endsWith("globals.css")) {
          clientSrcFolder?.file("styles.css", fileVal);
        } else if (lower.endsWith("app.js") || lower.endsWith("app.jsx") || lower.endsWith("app.tsx")) {
          clientSrcFolder?.file("App.js", fileVal);
        } else if (lower === "readme.md") {
          // Included as root README.md
        } else {
          clientFolder?.file(cleanPath, fileVal);
        }
      }

      // Default server package.json if omitted
      if (!hasServerPkg && serverFolder) {
        serverFolder.file("package.json", JSON.stringify({
          name: "backend-server",
          version: "1.0.0",
          main: "server.js",
          scripts: { start: "node server.js" },
          dependencies: { express: "^4.19.2", cors: "^2.8.5" }
        }, null, 2));
      }

      // Default client package.json if omitted
      if (!hasClientPkg && clientFolder) {
        clientFolder.file("package.json", JSON.stringify({
          name: "frontend-client",
          version: "1.0.0",
          private: true,
          dependencies: {
            "react": "^19.0.0",
            "react-dom": "^19.0.0",
            "lucide-react": "^1.23.0"
          },
          scripts: {
            start: "react-scripts start",
            build: "react-scripts build"
          }
        }, null, 2));
      }

      const zipBlob = await zip.generateAsync({ type: "blob" });
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `agentic-fullstack-app-${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to generate zip export:", err);
    } finally {
      setExportingZip(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0d0f17] text-gray-200 font-sans overflow-hidden">
      
      {/* Main Workspace Area (Left + Center) */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#12141f]">
        
        {/* Top Header / Navigation */}
        <header className="h-14 border-b border-gray-800/80 bg-[#151824] px-4 flex items-center justify-between shrink-0 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white tracking-wide text-sm">AGENTIC IDE</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  Full-Stack
                </span>
              </div>
              <p className="text-[11px] text-gray-400">Autonomous React + Node.js Express Generator</p>
            </div>
          </div>

          {/* Center Tabs Switcher */}
          {files && (
            <div className="flex items-center bg-[#0d0f17]/80 p-1 rounded-xl border border-gray-800">
              <button
                onClick={() => setActiveTab("preview")}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "preview" 
                    ? "bg-blue-600 text-white shadow-sm" 
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Live App Preview</span>
              </button>

              <button
                onClick={() => setActiveTab("backend")}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "backend" 
                    ? "bg-blue-600 text-white shadow-sm" 
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                <Server className="w-3.5 h-3.5" />
                <span>Backend & API Inspector</span>
                {apiSpec.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-indigo-500/30 text-indigo-300 font-mono">
                    {apiSpec.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab("plan")}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "plan" 
                    ? "bg-blue-600 text-white shadow-sm" 
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Architecture Plan</span>
              </button>
            </div>
          )}

          {/* Right Action Buttons */}
          <div className="flex items-center space-x-2">
            {files && (
              <button
                onClick={downloadFullstackProject}
                disabled={exportingZip}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs font-medium text-gray-200 border border-gray-700 transition shadow-sm disabled:opacity-50"
                title="Download full-stack project as runnable ZIP distribution"
              >
                {exportingZip ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                <span>{exportingZip ? "Zipping..." : "Export ZIP"}</span>
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Workspace Body */}
        <div className="flex-1 flex overflow-hidden relative">
          
          {/* STATE 1: Empty state (No code generated yet) */}
          {!files && (
            <div className="flex-1 flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-[#0c0e17] via-[#121420] to-[#151829] p-8">
              <div className="max-w-xl w-full text-center space-y-6 relative z-10">
                <div className="inline-flex p-3.5 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-2 shadow-inner">
                  <Cpu className="w-10 h-10 animate-pulse" />
                </div>
                
                <div className="space-y-2">
                  <h1 className="text-3xl font-extrabold text-white tracking-tight">
                    Full-Stack AI Application Developer
                  </h1>
                  <p className="text-gray-400 text-sm leading-relaxed max-w-md mx-auto">
                    Type a prompt to autonomously engineer both a <span className="text-blue-400 font-semibold">React Frontend</span> and a complete <span className="text-indigo-400 font-semibold">Express REST Backend</span> with real-time preview and API testing.
                  </p>
                </div>

                {/* Preset Suggestions */}
                <div className="pt-2 text-left">
                  <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2.5 flex items-center space-x-1.5">
                    <Sparkles className="w-3 h-3 text-blue-400" />
                    <span>Try an example prompt:</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {presetPrompts.map((preset, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleGenerate(preset)}
                        className="text-left p-3 rounded-xl bg-gray-800/40 hover:bg-gray-800/80 border border-gray-800 hover:border-blue-500/40 text-xs text-gray-300 hover:text-white transition-all duration-200 group flex items-start justify-between"
                      >
                        <span className="line-clamp-2">{preset}</span>
                        <ChevronRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-blue-400 shrink-0 ml-1 mt-0.5" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STATE 2: Tab 1 - Live App Preview (Sandpack React) */}
          {files && activeTab === "preview" && (
            <div className="flex-1 h-full w-full">
              <SandpackProvider
                template={template}
                theme="dark"
                files={files}
                customSetup={{
                  dependencies
                }}
              >
                <SandpackLayout style={{ display: 'flex', height: '100%', width: '100%', borderRadius: 0, border: 'none' }}>
                  {/* Left: File Explorer & Code Editor */}
                  <div style={{ display: 'flex', flex: 1, minWidth: '380px', borderRight: '1px solid #232738' }}>
                    <SandpackFileExplorer style={{ width: '28%', minWidth: '160px', height: '100%' }} />
                    <SandpackCodeEditor style={{ flex: 1, height: '100%' }} showLineNumbers showTabs closableTabs />
                  </div>
                  {/* Right: Live Interactive App Preview */}
                  <div style={{ flex: 1.1, minWidth: '380px', height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <div className="h-8 bg-[#181b28] border-b border-gray-800 px-3 flex items-center justify-between text-[11px] text-gray-400">
                      <div className="flex items-center space-x-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                        <span>Interactive React Preview</span>
                      </div>
                      <span className="text-[10px] text-gray-500">Live Browser Environment</span>
                    </div>
                    <div className="flex-1 h-full">
                      <SandpackPreview style={{ height: 'calc(100% - 32px)' }} showNavigator />
                    </div>
                  </div>
                </SandpackLayout>
              </SandpackProvider>
            </div>
          )}

          {/* STATE 3: Tab 2 - Backend & API Inspector */}
          {files && activeTab === "backend" && (
            <div className="flex-1 flex flex-col h-full bg-[#0f111a] overflow-hidden">
              {/* Backend Sub-Header Bar */}
              <div className="h-12 border-b border-gray-800/80 bg-[#161826] px-5 flex items-center justify-between shrink-0">
                <div className="flex items-center space-x-3">
                  <span className="flex h-2.5 w-2.5 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </span>
                  <div className="text-xs">
                    <span className="font-semibold text-white">Express.js Backend Server</span>
                    <span className="text-gray-400 ml-2">Port: 5000</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="flex items-center bg-[#0e1017] px-2.5 py-1 rounded-md border border-gray-800 text-[11px] font-mono text-gray-300">
                    <Terminal className="w-3 h-3 mr-1.5 text-blue-400" />
                    <span>node server.js</span>
                  </div>
                  <button
                    onClick={copyServerCode}
                    className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-gray-800 hover:bg-gray-700 text-xs text-gray-200 border border-gray-700 transition"
                  >
                    {copiedServerCode ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedServerCode ? "Copied" : "Copy Server Code"}</span>
                  </button>
                </div>
              </div>

              {/* Split Inspector: Endpoints List & Test Console */}
              <div className="flex-1 flex overflow-hidden">
                
                {/* Left: Endpoints List */}
                <div className="w-80 border-r border-gray-800/80 bg-[#131522] flex flex-col shrink-0">
                  <div className="p-3 border-b border-gray-800/60 font-semibold text-xs text-gray-400 uppercase tracking-wider flex items-center justify-between">
                    <span>Configured Endpoints ({apiSpec.length})</span>
                  </div>

                  <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
                    {apiSpec.length === 0 ? (
                      <div className="p-4 text-xs text-gray-500 text-center">
                        No structured endpoints parsed. Check `/server.js` directly.
                      </div>
                    ) : (
                      apiSpec.map((ep, idx) => {
                        const isSelected = selectedEndpoint?.path === ep.path && selectedEndpoint?.method === ep.method;
                        const methodColors: Record<string, string> = {
                          GET: "bg-blue-500/20 text-blue-400 border-blue-500/30",
                          POST: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                          PUT: "bg-amber-500/20 text-amber-400 border-amber-500/30",
                          PATCH: "bg-amber-500/20 text-amber-400 border-amber-500/30",
                          DELETE: "bg-rose-500/20 text-rose-400 border-rose-500/30",
                        };

                        return (
                          <div
                            key={idx}
                            onClick={() => {
                              setSelectedEndpoint(ep);
                              setTestResult(null);
                            }}
                            className={`p-2.5 rounded-xl border cursor-pointer transition-all ${
                              isSelected
                                ? "bg-blue-600/10 border-blue-500/50 text-white shadow-sm"
                                : "bg-gray-800/30 hover:bg-gray-800/70 border-gray-800/60 text-gray-300"
                            }`}
                          >
                            <div className="flex items-center space-x-2 mb-1">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border ${methodColors[ep.method] || "bg-gray-700 text-gray-300"}`}>
                                {ep.method}
                              </span>
                              <span className="font-mono text-xs font-semibold truncate text-gray-100">
                                {ep.path}
                              </span>
                            </div>
                            <p className="text-[11px] text-gray-400 line-clamp-1">
                              {ep.description}
                            </p>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Right: Endpoint Test Console & Server Code Preview */}
                <div className="flex-1 flex flex-col overflow-y-auto p-5 bg-[#0f111a] space-y-5">
                  {selectedEndpoint ? (
                    <div className="space-y-4">
                      {/* Endpoint Header Card */}
                      <div className="p-4 rounded-xl bg-[#171a29] border border-gray-800 shadow-md">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                              {selectedEndpoint.method}
                            </span>
                            <span className="font-mono text-sm font-semibold text-white">
                              http://localhost:5000{selectedEndpoint.path}
                            </span>
                          </div>
                          
                          <button
                            onClick={() => handleTestEndpoint(selectedEndpoint)}
                            disabled={testingApi}
                            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md transition disabled:opacity-50"
                          >
                            <Play className="w-3.5 h-3.5 fill-current" />
                            <span>{testingApi ? "Sending..." : "Send Test Request"}</span>
                          </button>
                        </div>

                        <p className="text-xs text-gray-400">
                          {selectedEndpoint.description}
                        </p>
                      </div>

                      {/* Request Payload Card (if applicable) */}
                      {selectedEndpoint.sampleRequest && (
                        <div className="rounded-xl border border-gray-800 bg-[#141624] overflow-hidden">
                          <div className="px-3.5 py-2 bg-[#181b2d] border-b border-gray-800 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                            Sample Request Body (JSON)
                          </div>
                          <pre className="p-3.5 text-xs font-mono text-emerald-300 bg-[#0f111c] overflow-x-auto">
                            {JSON.stringify(selectedEndpoint.sampleRequest, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Live Test Results Card */}
                      {testResult && (
                        <div className="rounded-xl border border-gray-800 bg-[#141624] overflow-hidden shadow-lg animate-in fade-in duration-200">
                          <div className="px-3.5 py-2 bg-[#181b2d] border-b border-gray-800 flex items-center justify-between text-xs">
                            <div className="flex items-center space-x-3">
                              <span className="font-semibold text-white">Response Payload</span>
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                                {testResult.status} OK
                              </span>
                              <span className="text-gray-400 text-[11px] font-mono">
                                {testResult.duration}ms
                              </span>
                            </div>
                            <span className="text-[11px] text-indigo-400 font-mono">
                              {testResult.source}
                            </span>
                          </div>
                          <pre className="p-4 text-xs font-mono text-blue-300 bg-[#0d0f17] overflow-x-auto max-h-72">
                            {JSON.stringify(testResult.data, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Full Server Code Viewer */}
                      <div className="rounded-xl border border-gray-800 bg-[#141624] overflow-hidden shadow-md">
                        <div className="px-3.5 py-2.5 bg-[#181b2d] border-b border-gray-800 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2 text-gray-300 font-semibold">
                            <FileCode className="w-4 h-4 text-blue-400" />
                            <span>/server.js (Node.js Express Source)</span>
                          </div>
                          <button
                            onClick={copyServerCode}
                            className="text-[11px] text-gray-400 hover:text-white flex items-center space-x-1"
                          >
                            <Copy className="w-3 h-3" />
                            <span>Copy Code</span>
                          </button>
                        </div>
                        <pre className="p-4 text-xs font-mono text-gray-300 bg-[#0c0e17] overflow-x-auto max-h-96 leading-relaxed">
                          {getServerCode()}
                        </pre>
                      </div>

                    </div>
                  ) : (
                    <div className="text-center py-12 text-gray-500 text-xs">
                      Select an API endpoint from the left to inspect and test.
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}

          {/* STATE 4: Tab 3 - Architecture & Contract View */}
          {files && activeTab === "plan" && (
            <div className="flex-1 overflow-y-auto p-6 bg-[#0f111a]">
              <div className="max-w-3xl mx-auto space-y-6">
                <div className="p-4 rounded-xl bg-gradient-to-r from-blue-900/20 to-indigo-900/20 border border-blue-500/20 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-bold text-white">Full-Stack Architecture Specification</h2>
                    <p className="text-xs text-gray-400">Generated by Orchestrator Agent with RAG technical context</p>
                  </div>
                  <div className="flex items-center space-x-2 text-xs font-mono text-blue-400 bg-blue-500/10 px-3 py-1.5 rounded-lg border border-blue-500/30">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Contract Active</span>
                  </div>
                </div>

                <div className="p-6 rounded-xl bg-[#151824] border border-gray-800 prose prose-invert max-w-none text-xs leading-relaxed">
                  <div className="whitespace-pre-wrap font-sans text-gray-300">
                    {plan || "No architectural plan details recorded."}
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>

      {/* Right Sidebar: AI Developer Chat & Prompts */}
      <div className="w-96 flex flex-col border-l border-gray-800/80 bg-[#141624] shadow-2xl shrink-0 z-20">
        
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-800 bg-[#161928] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="font-bold text-white tracking-wider text-xs uppercase">AI FULL-STACK COPILOT</span>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
        </div>
        
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8 text-gray-500 text-xs space-y-3">
              <div className="w-10 h-10 rounded-full bg-gray-800/50 flex items-center justify-center mx-auto text-gray-400">
                <Code2 className="w-5 h-5" />
              </div>
              <p>Ready to build your next full-stack web app. Describe what you want to create below.</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`p-3.5 rounded-xl shadow-sm text-xs ${msg.role === 'user' ? 'bg-blue-600/20 text-blue-100 ml-4 border border-blue-800/40' : 'bg-gray-800/60 mr-4 border border-gray-700/50 text-gray-200'}`}>
              <div className="font-semibold text-gray-400 mb-1.5 uppercase tracking-wider text-[10px] flex items-center space-x-1.5">
                <span>{msg.role === 'user' ? 'You' : 'Orchestrator'}</span>
              </div>
              <div className="whitespace-pre-wrap leading-relaxed">{msg.text}</div>
              
              {/* Extra badges for Agent messages */}
              {msg.details && (
                <div className="mt-3 pt-2.5 border-t border-gray-700/40 flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[10px] font-mono">
                    Express Server
                  </span>
                  <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px] font-mono">
                    React Frontend
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-mono">
                    Dual-Mode API
                  </span>
                </div>
              )}
            </div>
          ))}

          {/* Loading Indicator with Stage Progression */}
          {loading && (
             <div className="p-3.5 bg-gray-800/70 mr-4 rounded-xl text-xs border border-gray-700/60 shadow-md space-y-2">
                <div className="flex items-center space-x-2 text-blue-400">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span className="font-semibold text-white">Engineering Full-Stack Solution...</span>
                </div>
                {statusStep && (
                  <p className="text-[11px] text-gray-400 pl-5 italic font-mono">
                    {statusStep}
                  </p>
                )}
             </div>
          )}
        </div>

        {/* Prompt Input Box */}
        <div className="p-4 border-t border-gray-800 bg-[#161826] space-y-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleGenerate())}
            placeholder="e.g. Build an employee directory with departments, search, and editing..."
            className="w-full bg-[#0e1017] text-white rounded-xl p-3 outline-none focus:ring-2 focus:ring-blue-500/80 focus:border-transparent resize-none h-28 border border-gray-700/80 placeholder-gray-500 text-xs shadow-inner transition-all"
          />
          <button
            onClick={() => handleGenerate()}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl transition-all shadow-lg hover:shadow-blue-500/25 active:scale-[0.98] text-xs flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Generating App...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>{prompt.trim() ? "Generate Full-Stack App" : "Generate Full-Stack App (or select preset above)"}</span>
              </>
            )}
          </button>
        </div>
      </div>
      
    </div>
  );
}
