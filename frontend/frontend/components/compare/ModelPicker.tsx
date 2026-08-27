"use client";

import { ModelInfo } from "@/lib/api/types";

interface ModelPickerProps {
  models: ModelInfo[];
  selected: string[];
  onToggle: (modelId: string) => void;
  task: string;
  onTaskChange: (task: string) => void;
  onRun: () => void;
  loading: boolean;
}

export function ModelPicker({ models, selected, onToggle, task, onTaskChange, onRun, loading }: ModelPickerProps) {
  const authorized = models.filter((m) => m.authorized && m.status === "active");

  return (
    <div className="mx-auto max-w-2xl p-8">
      <p className="eyebrow">Multi-model compare</p>
      <h1 className="mt-2 text-2xl text-primary">Compare across models</h1>
      <p className="mt-2 text-sm text-secondary">Select 2–4 models and run the same task against all of them.</p>

      <textarea
        value={task}
        onChange={(e) => onTaskChange(e.target.value)}
        rows={4}
        placeholder="Paste your task here…"
        className="mt-6 w-full resize-none rounded-card border border-border bg-surface px-4 py-3 text-sm text-primary placeholder:text-muted focus:border-accent focus:outline-none"
      />

      <div className="mt-6">
        <p className="mb-2 text-sm font-medium text-primary">Models</p>
        <div className="grid gap-2 md:grid-cols-2">
          {authorized.map((m) => (
            <label
              key={m.model_id}
              className={`flex cursor-pointer items-center gap-3 rounded-card border p-3 transition-colors ${
                selected.includes(m.model_id) ? "border-accent bg-accent-soft" : "border-border bg-surface hover:bg-page"
              }`}
            >
              <input
                type="checkbox"
                checked={selected.includes(m.model_id)}
                onChange={() => onToggle(m.model_id)}
                className="h-4 w-4 accent-accent"
              />
              <div>
                <p className="text-sm font-medium text-primary">{m.display_name}</p>
                <p className="font-mono text-xs text-muted">{m.provider_id}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <p className="text-xs text-muted">{selected.length} selected (recommend 2–4)</p>
        <button
          onClick={onRun}
          disabled={loading || selected.length < 2 || !task.trim()}
          className="rounded bg-accent px-5 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Running…" : "Compare"}
        </button>
      </div>
    </div>
  );
}
