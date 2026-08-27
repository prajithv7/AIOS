"use client";

import { useSearchParams, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { compareApi, modelsApi } from "@/lib/api";
import { CompareResult } from "@/lib/api/types";
import { ModelPicker } from "@/components/compare/ModelPicker";
import { ComparisonGrid } from "@/components/compare/ComparisonGrid";
import { JudgeSummary } from "@/components/compare/JudgeSummary";

export default function CompareWorkspace() {
  const params = useParams<{ runId: string }>();
  const searchParams = useSearchParams();
  const isNew = params.runId === "new";

  const [task, setTask] = useState(searchParams.get("task") || "");
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: models = [] } = useQuery({ queryKey: ["models"], queryFn: modelsApi.list });
  const { data: fetched } = useQuery({
    queryKey: ["compare", params.runId],
    queryFn: () => compareApi.get(params.runId!),
    enabled: !isNew,
  });

  useEffect(() => {
    if (fetched) setResult(fetched);
  }, [fetched]);

  useEffect(() => {
    if (selected.length === 0 && models.length) {
      const authorized = models.filter((m) => m.authorized && m.status === "active");
      setSelected(authorized.slice(0, 3).map((m) => m.model_id));
    }
  }, [models, selected]);

  function toggle(modelId: string) {
    setSelected((prev) =>
      prev.includes(modelId) ? prev.filter((m) => m !== modelId) : [...prev, modelId]
    );
  }

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const conversationId = searchParams.get("conversationId");
      const res = await compareApi.run(conversationId && conversationId !== "new" ? conversationId : null, task, selected);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compare failed");
    } finally {
      setLoading(false);
    }
  }

  if (!result) {
    return (
      <ModelPicker
        models={models}
        selected={selected}
        onToggle={toggle}
        task={task}
        onTaskChange={setTask}
        onRun={run}
        loading={loading}
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8">
      <div>
        <p className="eyebrow">Comparison complete</p>
        <h1 className="mt-1 text-2xl text-primary">{result.task}</h1>
      </div>
      {error && <p className="text-sm text-[#c0392b]">{error}</p>}
      <JudgeSummary result={result} />
      <ComparisonGrid runs={result.runs || []} />
      <button
        onClick={() => setResult(null)}
        className="text-sm text-accent hover:underline"
      >
        Run another comparison
      </button>
    </div>
  );
}
