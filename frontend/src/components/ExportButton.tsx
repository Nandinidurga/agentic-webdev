"use client";

import { useState } from "react";
import { Download } from "lucide-react";

interface ExportButtonProps {
  rawFiles: Record<string, string> | null;
}

export default function ExportButton({ rawFiles }: ExportButtonProps) {
  const [exportingZip, setExportingZip] = useState(false);

  const downloadFullstackProject = async () => {
    if (!rawFiles) return;
    setExportingZip(true);
    try {
      const JSZipModule = await import("jszip");
      const JSZip = JSZipModule.default || JSZipModule;
      const zip = new JSZip();

      // Root README
      const readmeContent = [
        "# Full-Stack Application Bundle",
        "Generated autonomously by Agentic IDE.",
        "",
        "## 📁 Architecture",
        "- `/server`: Node.js + Express REST API Backend",
        "- `/client`: React 19 + Tailwind Interactive Frontend",
        "",
        "## 🚀 Quickstart Guide",
        "",
        "### 1. Launch the Backend Server",
        "```bash",
        "cd server",
        "npm install",
        "npm start",
        "```",
        "Server runs at http://localhost:5000 with CORS and REST endpoints.",
        "",
        "### 2. Launch the Frontend Client",
        "```bash",
        "cd client",
        "npm install",
        "npm start",
        "```",
        "Frontend opens at http://localhost:3000 and connects to the backend on port 5000."
      ].join("\n");
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

      if (!hasServerPkg && serverFolder) {
        serverFolder.file("package.json", JSON.stringify({
          name: "backend-server",
          version: "1.0.0",
          main: "server.js",
          scripts: { start: "node server.js" },
          dependencies: { express: "^4.19.2", cors: "^2.8.5" }
        }, null, 2));
      }

      if (!hasClientPkg && clientFolder) {
        clientFolder.file("package.json", JSON.stringify({
          name: "frontend-client",
          version: "1.0.0",
          scripts: { start: "react-scripts start" },
          dependencies: { "react": "^19.0.0", "react-dom": "^19.0.0", "lucide-react": "latest" }
        }, null, 2));
      }

      const blob = await zip.generateAsync({ type: "blob" });
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `agentic-fullstack-app-${Date.now()}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error("ZIP export failed:", err);
    } finally {
      setExportingZip(false);
    }
  };

  if (!rawFiles || Object.keys(rawFiles).length === 0) {
    return null;
  }

  return (
    <button
      onClick={downloadFullstackProject}
      disabled={exportingZip}
      className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all shadow-sm active:scale-95 disabled:opacity-50"
      title="Download complete runnable project with /server and /client"
    >
      <Download className={`w-3.5 h-3.5 ${exportingZip ? 'animate-bounce' : ''}`} />
      <span>{exportingZip ? "Packaging ZIP..." : "Download Full-Stack ZIP"}</span>
    </button>
  );
}
