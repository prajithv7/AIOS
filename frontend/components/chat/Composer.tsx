"use client";

import { useState } from "react";
import { Button } from "@/components/ui";

interface ComposerProps {
  onSend: (content: string) => void;
  onCompare: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function Composer({ onSend, onCompare, disabled, placeholder }: ComposerProps) {
  const [content, setContent] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim() || disabled) return;
    onSend(content.trim());
    setContent("");
  }

  return (
    <form onSubmit={submit} className="flex items-end gap-2 border-t border-border bg-surface p-4">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        disabled={disabled}
        placeholder={placeholder || "Ask anything…"}
        rows={2}
        className="flex-1 resize-none rounded border border-border bg-page px-3 py-2 text-sm text-primary placeholder:text-muted focus:border-accent focus:outline-none disabled:opacity-50"
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit(e);
          }
        }}
      />
      <Button type="submit" disabled={disabled || !content.trim()}>
        Send
      </Button>
      <Button type="button" variant="secondary" disabled={disabled || !content.trim()} onClick={() => onCompare(content.trim())}>
        Compare
      </Button>
    </form>
  );
}
