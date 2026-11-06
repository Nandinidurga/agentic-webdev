"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { buildExportBundle } from "@/utils/exportScaffold";

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

      // Generate known-good client scaffold and merge generated files into it
      const bundle = buildExportBundle(rawFiles);
      for (const [relativePath, content] of Object.entries(bundle)) {
        zip.file(relativePath, content);
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
