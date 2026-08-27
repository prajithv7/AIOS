"use client";

import { useState } from "react";

export function CodePreview({ filename, code }: { filename: string; code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="overflow-hidden rounded-card border border-border bg-code-bg">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
        <span className="text-xs text-code-text">{filename}</span>
        <button
          onClick={() => {
            navigator.clipboard.writeText(code);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
          }}
          className="text-xs text-muted transition-colors hover:text-code-text"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed text-code-text">
        <code>{code}</code>
      </pre>
    </div>
  );
}
