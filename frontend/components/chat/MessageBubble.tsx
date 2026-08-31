import { Message } from "@/lib/api/types";
import { IconFile } from "@tabler/icons-react";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const attachments = (message.metadata?.attachments as Array<{name: string; type: string; url?: string; size: number}>) || [];

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-card border px-4 py-3 ${
          isUser ? "border-accent-soft bg-accent-soft" : "border-border bg-surface"
        }`}
      >
        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachments.map((file, i) => (
              <div key={i} className="flex items-center gap-2 rounded bg-page border border-border p-2 pr-3">
                {file.type.startsWith('image/') && file.url ? (
                  <div className="flex items-center justify-center w-12 h-12 overflow-hidden rounded bg-surface">
                     <img src={file.url} alt={file.name} className="object-cover w-full h-full cursor-pointer" onClick={() => window.open(file.url, '_blank')} />
                  </div>
                ) : (
                  <IconFile className="text-muted w-5 h-5" />
                )}
                <div className="flex flex-col max-w-[150px]">
                  <span className="truncate text-xs font-medium text-primary">{file.name}</span>
                  <span className="text-[10px] text-muted">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="whitespace-pre-wrap text-sm text-primary">{message.content}</p>
        {!isUser && message.model_id && (
          <div className="mt-2 flex items-center gap-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent" />
            <span className="font-mono text-xs text-muted">
              {message.model_id}
              {message.provider_id ? ` · ${message.provider_id}` : ""}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
