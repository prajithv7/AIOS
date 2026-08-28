"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api";
import { Button, Card, Input } from "@/components/ui";

const MEMORY_TYPES = ["instructions", "decisions", "tech_stack", "preferences", "notes"];

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const queryClient = useQueryClient();

  const [tab, setTab] = useState<"conversations" | "memory">("memory");
  const [type, setType] = useState("notes");
  const [content, setContent] = useState("");

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.list().then((ps) => ps.find((p) => p.id === projectId)),
  });

  const { data: memory = [] } = useQuery({
    queryKey: ["memory", projectId],
    queryFn: () => projectsApi.memory(projectId),
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ["projectConversations", projectId],
    queryFn: () => projectsApi.conversations(projectId),
    enabled: tab === "conversations",
  });

  const createMutation = useMutation({
    mutationFn: () => projectsApi.createMemory(projectId, type, content),
    onSuccess: () => {
      setContent("");
      queryClient.invalidateQueries({ queryKey: ["memory", projectId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (memoryId: string) => projectsApi.deleteMemory(projectId, memoryId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["memory", projectId] }),
  });

  const deleteProjectMutation = useMutation({
    mutationFn: () => projectsApi.delete(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      router.push("/app/projects");
    },
  });

  return (
    <div className="mx-auto max-w-3xl p-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="eyebrow">Project</p>
          <h1 className="mt-2 text-2xl text-primary">{project?.name || projectId}</h1>
          {project?.description && <p className="mt-1 text-sm text-secondary">{project.description}</p>}
        </div>
        <Button
          variant="danger"
          onClick={() => {
            if (confirm("Delete this project and all its memory?")) deleteProjectMutation.mutate();
          }}
        >
          Delete project
        </Button>
      </div>

      <div className="mt-4 flex gap-2 border-b border-border">
        {(["memory", "conversations"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 text-sm capitalize transition-colors ${
              tab === t ? "border-b-2 border-accent text-accent" : "text-muted hover:text-primary"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "memory" && (
        <div className="mt-6">
          <Card className="mb-4">
            <div className="flex gap-2">
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="rounded border border-border bg-surface px-3 py-2 text-sm text-primary focus:border-accent focus:outline-none"
              >
                {MEMORY_TYPES.map((t) => (
                  <option key={t} value={t}>{t.replace("_", " ")}</option>
                ))}
              </select>
              <Input value={content} onChange={(e) => setContent(e.target.value)} placeholder="Add a memory entry…" />
              <Button onClick={() => createMutation.mutate()} disabled={!content.trim()}>
                Add
              </Button>
            </div>
          </Card>

          <div className="space-y-3">
            {memory.map((m) => (
              <Card key={m.id} className="flex items-start justify-between">
                <div>
                  <span className="eyebrow text-xs">{m.type.replace("_", " ")}</span>
                  <p className="mt-1 text-sm text-primary">{m.content}</p>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(m.id)}
                  className="text-sm text-muted hover:text-[#c0392b]"
                >
                  Delete
                </button>
              </Card>
            ))}
            {memory.length === 0 && <p className="text-sm text-muted">No memory items yet.</p>}
          </div>
        </div>
      )}

      {tab === "conversations" && (
        <div className="mt-6">
          {conversations.length === 0 ? (
            <p className="text-sm text-muted">No conversations in this project yet.</p>
          ) : (
            <div className="space-y-3">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => router.push(`/app/chat/${c.id}`)}
                  className="w-full text-left"
                >
                  <Card className="transition-colors hover:border-accent">
                    <h3 className="text-sm font-medium text-primary">{c.title}</h3>
                    <div className="mt-1 flex gap-3 text-xs text-muted">
                      <span>{c.message_count} messages</span>
                      {c.created_at && <span>{new Date(c.created_at).toLocaleDateString()}</span>}
                    </div>
                  </Card>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
