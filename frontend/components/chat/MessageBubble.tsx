import { Message } from "@/lib/api/types";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-card border px-4 py-3 ${
          isUser ? "border-accent-soft bg-accent-soft" : "border-border bg-surface"
        }`}
      >
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
