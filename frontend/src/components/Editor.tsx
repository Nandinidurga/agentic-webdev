"use client";

import React, { useRef } from "react";
import MonacoEditor, { OnMount } from "@monaco-editor/react";

interface EditorProps {
  code: string;
  onChange?: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
}

export default function Editor({ code, onChange, language = "javascript", readOnly = false }: EditorProps) {
  const editorRef = useRef<any>(null);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
  };

  return (
    <div className="w-full h-full border border-gray-700 rounded-md overflow-hidden">
      <MonacoEditor
        height="100%"
        defaultLanguage={language}
        language={language}
        value={code}
        theme="vs-dark"
        onChange={onChange}
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          wordWrap: "on",
          readOnly: readOnly,
          scrollBeyondLastLine: false,
          padding: { top: 16 },
        }}
      />
    </div>
  );
}
