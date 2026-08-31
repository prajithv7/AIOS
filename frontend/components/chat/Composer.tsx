"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui";
import { IconPaperclip, IconX, IconFile, IconPhoto } from "@tabler/icons-react";

interface ComposerProps {
  onSend: (content: string) => void;
  onCompare: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function Composer({ onSend, onCompare, disabled, placeholder }: ComposerProps) {
  const [content, setContent] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(f => {
      if (f.size > 10 * 1024 * 1024) { // 10MB limit example
        alert(`File ${f.name} is too large. Max size is 10MB.`);
        return false;
      }
      return true;
    });
    if (validFiles.length) {
      setAttachments(prev => [...prev, ...validFiles]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (attachments.length > 0) {
      alert("Backend attachment endpoint /api/upload is required. File uploading is not yet supported in this environment.");
      return;
    }
    if (!content.trim() || disabled) return;
    onSend(content.trim());
    setContent("");
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 border-t border-border bg-surface p-4">
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 px-2 pb-2">
          {attachments.map((file, i) => (
            <div key={i} className="flex items-center gap-2 rounded bg-page border border-border p-2 pr-3">
              {file.type.startsWith('image/') ? (
                <div className="flex items-center justify-center w-8 h-8 overflow-hidden rounded bg-surface">
                   <img src={URL.createObjectURL(file)} alt={file.name} className="object-cover w-full h-full" />
                </div>
              ) : (
                <IconFile className="text-muted w-5 h-5" />
              )}
              <div className="flex flex-col max-w-[150px]">
                <span className="truncate text-xs font-medium text-primary">{file.name}</span>
                <span className="text-[10px] text-muted">{(file.size / 1024).toFixed(1)} KB</span>
              </div>
              <button
                type="button"
                onClick={() => removeAttachment(i)}
                className="ml-1 text-muted hover:text-primary p-1 rounded-full hover:bg-surface"
                title="Remove attachment"
                aria-label="Remove attachment"
              >
                <IconX size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
      <div className="flex items-end gap-2 relative">
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          multiple 
          accept="image/*,.pdf,.txt,.md,.csv,.json"
          className="hidden" 
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="p-2 text-muted hover:text-primary hover:bg-page rounded flex-shrink-0 mb-1"
          title="Attach files or images"
          aria-label="Attach files or images"
        >
          <IconPaperclip size={20} />
        </button>
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleInput}
          disabled={disabled}
          placeholder={placeholder || "Ask anything…"}
          rows={1}
          style={{ minHeight: '40px' }}
          className="flex-1 resize-none rounded border border-border bg-page px-3 py-2 text-sm text-primary placeholder:text-muted focus:border-accent focus:outline-none disabled:opacity-50"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(e);
            }
          }}
        />
        <Button type="submit" disabled={disabled || (!content.trim() && attachments.length === 0)} title="Send message" aria-label="Send message">
          Send
        </Button>
        <Button type="button" variant="secondary" disabled={disabled || (!content.trim() && attachments.length === 0)} onClick={() => onCompare(content.trim())} title="Compare across models" aria-label="Compare across models">
          Compare
        </Button>
      </div>
    </form>
  );
}
