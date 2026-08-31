"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { conversationsApi, modelsApi, routeApi } from "@/lib/api";
import { streamChat } from "@/lib/stream";
import { Message } from "@/lib/api/types";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ModelSelector } from "@/components/chat/ModelSelector";
import { Composer } from "@/components/chat/Composer";
import { StreamRenderer } from "@/components/chat/StreamRenderer";
import { useKeyVaultStore } from "@/lib/stores/keys";

export default function ChatWorkspace() {
  const params = useParams<{ conversationId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const conversationId = params.conversationId === "new" ? null : params.conversationId;

  const [modelId, setModelId] = useState("");
  const [recommendedId, setRecommendedId] = useState<string | undefined>();
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [streamModel, setStreamModel] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<{ code: string; message: string } | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: models = [] } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });
  const { data: conversations = [] } = useQuery({ queryKey: ["conversations"], queryFn: conversationsApi.list });
  const { data: messages = [] } = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => conversationsApi.messages(conversationId!),
    enabled: !!conversationId,
  });
  const { fetch: fetchKeys } = useKeyVaultStore();

  const deleteMutation = useMutation({
    mutationFn: (id: string) => conversationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      router.push("/app/chat/new");
    },
  });

  const renameMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => conversationsApi.update(id, { title }),
    onSuccess: () => {
      setEditingId(null);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  useEffect(() => {
    fetchKeys().catch(() => undefined);
  }, [fetchKeys]);

  useEffect(() => {
    if (models.length && !modelId) {
      const authorized = models.filter((m) => m.authorized && m.status === "active");
      if (authorized.length) setModelId(authorized[0].model_id);
    }
  }, [models, modelId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamText]);

  async function handleNewConversation() {
    const conv = await conversationsApi.create("New conversation");
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
    router.push(`/app/chat/${conv.id}`);
  }

  async function handleSend(content: string) {
    let cid = conversationId;
    if (!cid) {
      const conv = await conversationsApi.create(content.slice(0, 40));
      cid = conv.id;
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      router.replace(`/app/chat/${cid}`);
    }

    setStreaming(true);
    setStreamText("");
    setStreamError(null);
    const chosen = modelId || recommendedId;
    if (!chosen) {
      setStreamError({ code: "MODEL_UNAVAILABLE", message: "Select a model to continue." });
      setStreaming(false);
      return;
    }
    setStreamModel(chosen);

    abortRef.current = await streamChat(cid, content, chosen, {
      onToken: (token) => setStreamText((prev) => prev + token),
      onDone: () => {
        setStreaming(false);
        queryClient.invalidateQueries({ queryKey: ["messages", cid] });
      },
      onError: (code, message) => {
        setStreamError({ code, message });
        setStreaming(false);
      },
    });
  }

  function handleCompare(content: string) {
    let cid = conversationId ?? "new";
    router.push(`/app/compare/new?task=${encodeURIComponent(content)}&conversationId=${cid}`);
  }

  async function handleRecommend(content: string) {
    try {
      const rec = await routeApi.recommend(content, conversationId ?? undefined);
      setRecommendedId(rec.recommended_model_id);
      setModelId(rec.recommended_model_id);
    } catch {
      /* ignore */
    }
  }

  const streamRoleMessage: Message | null = streamText
    ? {
        id: "__stream__",
        conversation_id: conversationId || "",
        role: "assistant",
        content: streamText,
        provider_id: streamModel,
        model_id: streamModel,
        metadata: {},
        created_at: null,
      }
    : null;

  return (
    <div className="flex h-screen overflow-hidden">
      {sidebarOpen && <div className="fixed inset-0 bg-black/50 z-20 md:hidden" onClick={() => setSidebarOpen(false)} />}
      
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 transform flex-col border-r border-border bg-surface transition-transform md:static md:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-3">
          <button
            onClick={handleNewConversation}
            className="w-full rounded bg-accent px-3 py-2 text-sm text-white hover:opacity-90"
          >
            New conversation
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group mb-1 flex items-center rounded transition-colors ${
                c.id === conversationId ? "bg-accent-soft text-accent" : "text-secondary hover:bg-page"
              }`}
            >
              {editingId === c.id ? (
                <input
                  autoFocus
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => {
                    if (editTitle.trim()) renameMutation.mutate({ id: c.id, title: editTitle.trim() });
                    setEditingId(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      if (editTitle.trim()) renameMutation.mutate({ id: c.id, title: editTitle.trim() });
                      setEditingId(null);
                    }
                    if (e.key === "Escape") setEditingId(null);
                  }}
                  className="flex-1 bg-transparent px-3 py-2 text-sm outline-none"
                />
              ) : (
                <button
                  onClick={() => router.push(`/app/chat/${c.id}`)}
                  className="flex-1 truncate px-3 py-2 text-left text-sm"
                >
                  {c.title}
                </button>
              )}
              {editingId !== c.id && (
                <div className="hidden gap-1 px-1 group-hover:flex">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingId(c.id);
                      setEditTitle(c.title);
                    }}
                    className="rounded px-1 text-xs text-muted hover:text-primary"
                    title="Rename"
                  >
                    ✎
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm("Delete this conversation?")) deleteMutation.mutate(c.id);
                    }}
                    className="rounded px-1 text-xs text-muted hover:text-[#c0392b]"
                    title="Delete"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden w-full">
        <header className="flex items-center justify-between border-b border-border bg-surface px-4 py-3">
          <div className="flex items-center gap-3">
            <button className="md:hidden text-primary p-1 hover:bg-page rounded" onClick={() => setSidebarOpen(true)}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 6l16 0" /><path d="M4 12l16 0" /><path d="M4 18l16 0" /></svg>
            </button>
            <h2 className="truncate text-primary">
              {conversations.find((c) => c.id === conversationId)?.title || "New conversation"}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <ModelSelector
              models={models}
              value={modelId}
              onChange={setModelId}
              recommendedId={recommendedId}
              disabled={streaming}
            />
          </div>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {streamRoleMessage && <MessageBubble message={streamRoleMessage} />}
          {streaming && !streamText && (
            <div className="rounded-card border border-border bg-surface p-4">
              <StreamRenderer text="" />
            </div>
          )}
          {streamError && (
            <div className="flex items-center gap-3 rounded-card border border-border bg-surface p-3">
              <p className="text-sm text-[#c0392b]">
                {streamError.code}: {streamError.message}
              </p>
              <button
                onClick={() => handleSend((conversationId ? messages[messages.length - 1] : undefined)?.content || "")}
                className="text-sm text-accent hover:underline"
              >
                Retry
              </button>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <Composer onSend={handleSend} onCompare={handleCompare} disabled={streaming} />
      </div>
    </div>
  );
}
