"use client";

import { ModelInfo } from "@/lib/api/types";

interface ModelSelectorProps {
  models: ModelInfo[];
  value: string;
  onChange: (modelId: string) => void;
  recommendedId?: string;
  disabled?: boolean;
}

export function ModelSelector({ models, value, onChange, recommendedId, disabled }: ModelSelectorProps) {
  const authorized = models.filter((m) => m.authorized && m.status === "active");

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="rounded border border-border bg-surface px-3 py-1.5 text-sm text-primary focus:border-accent focus:outline-none disabled:opacity-50"
    >
      {authorized.length === 0 && <option value="">No models authorized</option>}
      {authorized.map((m) => (
        <option key={m.model_id} value={m.model_id}>
          {m.display_name}
          {recommendedId === m.model_id ? " (recommended)" : ""}
        </option>
      ))}
    </select>
  );
}
