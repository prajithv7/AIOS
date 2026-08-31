"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api";
import { Button, Card, Input } from "@/components/ui";

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: projects = [], isLoading } = useQuery({ queryKey: ["projects"], queryFn: projectsApi.list });

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const createMutation = useMutation({
    mutationFn: () => projectsApi.create(name, description || undefined),
    onSuccess: () => {
      setName("");
      setDescription("");
      setShowForm(false);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });

  return (
    <div className="mx-auto max-w-3xl p-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="eyebrow">Workspace organization</p>
          <h1 className="mt-2 text-2xl text-primary">Projects</h1>
          <p className="mt-2 text-sm text-secondary">Group conversations and keep persistent memory per project.</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "New project"}
        </Button>
      </div>

      {showForm && (
        <Card className="mt-6">
          <div className="space-y-3">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" />
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optional)" />
            <div className="flex justify-end">
              <Button onClick={() => createMutation.mutate()} disabled={!name.trim()}>
                Create project
              </Button>
            </div>
          </div>
        </Card>
      )}

      {isLoading && <p className="mt-6 text-sm text-muted">Loading…</p>}
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {projects.map((p) => (
          <button key={p.id} onClick={() => router.push(`/app/projects/${p.id}`)} className="text-left">
            <Card className="h-full transition-colors hover:border-accent">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg text-primary">{p.name}</h3>
                  {p.description && <p className="mt-1 text-sm text-secondary">{p.description}</p>}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm("Delete this project?")) deleteMutation.mutate(p.id);
                  }}
                  className="text-sm text-muted hover:text-[#c0392b]"
                >
                  Delete
                </button>
              </div>
              <div className="mt-3 flex gap-3 text-xs text-muted">
                <span>{p.conversation_count} conversations</span>
                <span>{p.memory_count} memory items</span>
              </div>
            </Card>
          </button>
        ))}
      </div>
      {!isLoading && projects.length === 0 && (
        <p className="mt-6 text-sm text-muted">No projects yet. Create one to get started.</p>
      )}
    </div>
  );
}
