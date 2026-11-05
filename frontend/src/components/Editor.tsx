"use client";

import React, { useRef, useState } from "react";
import MonacoEditor, { type OnMount } from "@monaco-editor/react";
import { Copy, Check, FileCode } from "lucide-react";

interface EditorProps {
  code: string;
  onChange?: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
  filename?: string;
  height?: string | number;
}

export default function Editor({
  code,
  onChange,
  language = "javascript",
  readOnly = true,
  filename,
  height = "100%",
}: EditorProps) {
  const editorRef = useRef<any>(null);
  const [copied, setCopied] = useState(false);

  const detectLanguage = (
    name?: string,
    fallback: string = "javascript"
  ) => {
    if (!name) return fallback;

    const lower = name.toLowerCase();

    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".css")) return "css";
    if (lower.endsWith(".html")) return "html";
    if (lower.endsWith(".md")) return "markdown";
    if (lower.endsWith(".ts") || lower.endsWith(".tsx"))
      return "typescript";
    if (lower.endsWith(".js") || lower.endsWith(".jsx"))
      return "javascript";
    if (lower.endsWith(".py")) return "python";
    if (lower.endsWith(".sql")) return "sql";

    return fallback;
  };

  const activeLanguage = filename
    ? detectLanguage(filename, language)
    : language;

  const handleEditorDidMount: OnMount = (editor) => {
    editorRef.current = editor;
  };

  const handleCopy = async () => {
    if (!code) return;

    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);

      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy code:", error);
    }
  };

  return (
    <div className="w-full h-full flex flex-col border border-gray-800 rounded-xl overflow-hidden bg-[#0d0f17]">
      {filename && (
        <div className="h-9 px-3.5 bg-[#151826] border-b border-gray-800 flex items-center justify-between text-xs text-gray-300 shrink-0">
          <div className="flex items-center space-x-2">
            <FileCode className="w-3.5 h-3.5 text-blue-400" />

            <span className="font-mono text-[11px] font-semibold text-gray-200">
              {filename}
            </span>

            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
              {activeLanguage}
            </span>
          </div>

          <button
            onClick={handleCopy}
            disabled={!code}
            className="flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] text-gray-400 hover:text-white hover:bg-gray-800 transition disabled:opacity-40"
            title="Copy file contents"
            aria-label="Copy file contents"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400 font-medium">
                  Copied
                </span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      )}

      <div className="flex-1 relative min-h-[220px]">
        <MonacoEditor
          height={height}
          language={activeLanguage}
          value={code}
          theme="vs-dark"
          onChange={onChange}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineHeight: 20,
            wordWrap: "on",
            readOnly,
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: "all",
          }}
        />
      </div>
    </div>
  );
}