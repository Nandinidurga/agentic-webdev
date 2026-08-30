"use client";
import { useState } from "react";
import { 
  SandpackProvider, 
  SandpackLayout, 
  SandpackCodeEditor, 
  SandpackPreview,
  SandpackFileExplorer
} from "@codesandbox/sandpack-react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<{role: string, text: string}[]>([]);
  const [files, setFiles] = useState<Record<string, string> | null>(null);
  const [template, setTemplate] = useState<"react" | "vanilla">("react");
  const [dependencies, setDependencies] = useState<Record<string, string>>({
    "lucide-react": "latest",
    "tailwindcss": "latest"
  });

  const handleGenerate = async () => {
    if (!prompt) return;
    setLoading(true);
    setMessages(prev => [...prev, {role: 'user', text: prompt}]);
    setFiles(null);
    
    try {
      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });
      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'agent', 
        text: `Generation complete! Generated ${Object.keys(data.files || {}).length} files.`
      }]);
      
      if (data.files && Object.keys(data.files).length > 0) {
        const fileKeys = Object.keys(data.files).map(k => k.toLowerCase());
        const isVanilla = fileKeys.some(k => k.includes('index.html')) && !fileKeys.some(k => k.includes('app.js') || k.includes('app.jsx') || k.includes('react'));
        
        setTemplate(isVanilla ? "vanilla" : "react");

        const formattedFiles: Record<string, string> = {};
        let parsedDependencies: Record<string, string> = {
            "lucide-react": "latest",
            "tailwindcss": "latest"
        };

        for (const [key, value] of Object.entries(data.files)) {
            let safeKey = key.startsWith('/') ? key : `/${key}`;
            const lowerKey = safeKey.toLowerCase();
            
            if (lowerKey.includes('package.json')) {
                try {
                    const pkg = typeof value === 'string' ? JSON.parse(value) : value;
                    if (pkg && pkg.dependencies) {
                        parsedDependencies = { ...parsedDependencies, ...pkg.dependencies };
                    }
                } catch (e) {
                    console.error("Failed to parse package.json from LLM", e);
                }
                // Do not include package.json in formattedFiles to avoid confusing Sandpack React
                continue;
            }

            if (isVanilla) {
                if (lowerKey.endsWith('index.html')) safeKey = '/index.html';
                if (lowerKey.endsWith('script.js') || lowerKey.endsWith('main.js') || lowerKey.endsWith('index.js')) safeKey = '/index.js';
                if (lowerKey.endsWith('style.css') || lowerKey.endsWith('styles.css')) safeKey = '/styles.css';
            } else {
                // Force the main component to be /App.js
                if (lowerKey.endsWith('app.jsx') || lowerKey.endsWith('app.js') || lowerKey.endsWith('app.tsx')) {
                    safeKey = '/App.js';
                }
                
                // Force the main styles to be /styles.css
                if (lowerKey.endsWith('index.css') || lowerKey.endsWith('styles.css') || lowerKey.endsWith('globals.css')) {
                    safeKey = '/styles.css';
                }
                
                // Ignore build configs that confuse Sandpack React
                if (lowerKey.includes('vite.config') || lowerKey.includes('index.html') || lowerKey.includes('main.jsx') || lowerKey.includes('index.js')) {
                    continue;
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
            }
            
            // If this is the main React file, rewrite index.css or globals.css imports to styles.css
            // since we force renamed the CSS file to styles.css above.
            if (safeKey === '/App.js') {
                fileContent = fileContent.replace(/import\s+['"](?:\.\/)?(?:index\.css|globals\.css)['"]\s*;?/g, "import './styles.css';");
            }

            formattedFiles[safeKey] = fileContent;
        }
        
        setDependencies(parsedDependencies);
        setFiles(formattedFiles);
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {role: 'agent', text: "Error connecting to backend."}]);
    } finally {
      setLoading(false);
      setPrompt("");
    }
  };

  return (
    <div className="flex h-screen bg-[#0f111a] text-gray-300 font-sans overflow-hidden">
      
      {/* Left & Middle: Sandpack Area */}
      <div className="flex-1 flex flex-col bg-[#161822]">
        {files ? (
            <SandpackProvider
                template={template}
                theme="dark"
                files={files}
                customSetup={{
                    dependencies
                }}
            >
              <SandpackLayout style={{ display: 'flex', height: '100vh', width: '100%', borderRadius: 0, border: 'none' }}>
                {/* Left side: Explorer & Editor */}
                <div style={{ display: 'flex', flex: 1, minWidth: '300px', borderRight: '1px solid #2d3748' }}>
                  <SandpackFileExplorer style={{ width: '25%', minWidth: '150px' }} />
                  <SandpackCodeEditor style={{ flex: 1 }} showLineNumbers showTabs closableTabs />
                </div>
                {/* Middle: Preview */}
                <div style={{ flex: 1, minWidth: '300px' }}>
                  <SandpackPreview style={{ height: '100vh' }} showNavigator />
                </div>
              </SandpackLayout>
            </SandpackProvider>
        ) : (
            <div className="flex-1 flex items-center justify-center relative overflow-hidden bg-gradient-to-br from-[#0f111a] to-[#161822]">
              <div className="text-center space-y-4 relative z-10 p-8">
                <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">Agentic IDE</h2>
                <p className="text-gray-500 max-w-md mx-auto">Type a prompt in the sidebar on the right to generate a full-stack application. The live Replit-like preview will appear here.</p>
              </div>
            </div>
        )}
      </div>

      {/* Extreme Right: Sidebar / Chat */}
      <div className="w-96 flex flex-col border-l border-gray-800 bg-[#161822] shadow-xl z-20 shrink-0">
        <div className="p-4 border-b border-gray-800 font-bold text-white tracking-wider flex items-center justify-between">
          <span>AI DEVELOPER</span>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`p-3 rounded-xl shadow-sm ${msg.role === 'user' ? 'bg-blue-600/20 text-blue-100 ml-4 border border-blue-900/30' : 'bg-gray-800/60 mr-4 border border-gray-700/50'}`}>
              <div className="text-xs font-semibold text-gray-400 mb-1.5 uppercase tracking-wide">{msg.role}</div>
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</div>
            </div>
          ))}
          {loading && (
             <div className="p-3 bg-gray-800/60 mr-4 rounded-xl animate-pulse text-sm border border-gray-700/50">
                <div className="flex items-center space-x-2 text-blue-400">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  <span className="ml-2 font-medium">Coding...</span>
                </div>
             </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-800 bg-[#1a1d27]">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleGenerate())}
            placeholder="Build me a weather app..."
            className="w-full bg-gray-900/80 text-white rounded-xl p-3.5 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none h-28 border border-gray-700 placeholder-gray-500 text-sm shadow-inner transition-all"
          />
          <button
            onClick={handleGenerate}
            disabled={loading || !prompt}
            className="w-full mt-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all shadow-lg hover:shadow-blue-500/25 active:scale-[0.98]"
          >
            {loading ? "Generating..." : "Generate App"}
          </button>
        </div>
      </div>
      
    </div>
  );
}
