"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api";
import { Button, Card } from "@/components/ui";

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projects = [], isLoading } = useQuery({ queryKey: ["projects"], queryFn: projectsApi.list });

  return (
    <div className="mx-auto max-w-3xl p-8">
      <p className="eyebrow">Workspace organization</p>
      <h1 className="mt-2 text-2xl text-primary">Projects</h1>
      <p className="mt-2 text-sm text-secondary">Group conversations and keep persistent memory per project.</p>

      {isLoading && <p className="mt-6 text-sm text-muted">Loading…</p>}
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {projects.map((p) => (
          <button key={p.id} onClick={() => router.push(`/app/projects/${p.id}`)} className="text-left">
            <Card className="h-full transition-colors hover:border-accent">
              <h3 className="text-lg text-primary">{p.name}</h3>
              {p.description && <p className="mt-1 text-sm text-secondary">{p.description}</p>}
              <div className="mt-3 flex gap-3 text-xs text-muted">
                <span>{p.conversation_count} conversations</span>
                <span>{p.memory_count} memory items</span>
              </div>
            </Card>
          </button>
        ))}
      </div>
      {!isLoading && projects.length === 0 && (
        <p className="mt-6 text-sm text-muted">No projects yet.</p>
      )}
    </div>
  );
}
