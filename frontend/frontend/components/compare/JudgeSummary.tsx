"use client";

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { CompareResult } from "@/lib/api/types";
import { Card } from "@/components/ui";

export function JudgeSummary({ result }: { result: CompareResult }) {
  const data = Object.entries(result.scores || {}).map(([model, score]) => ({ model, score }));
  const winnerRun = result.runs?.find((r) => r.model_id === result.winner);

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Judge verdict</p>
          <h2 className="mt-1 text-xl text-primary">
            {winnerRun ? `Winner: ${winnerRun.model_id}` : "No winner"}
          </h2>
          <p className="mt-2 max-w-xl text-sm text-secondary">{result.reason}</p>
        </div>
        <div className="h-40 w-full md:w-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <XAxis dataKey="model" tick={{ fontSize: 10 }} hide />
              <YAxis domain={[0, 10]} hide />
              <Tooltip />
              <Bar dataKey="score" fill="#0F6E56" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {data.map((d) => (
          <span key={d.model} className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs text-accent">
            {d.model}: {d.score.toFixed(1)}
          </span>
        ))}
      </div>
    </Card>
  );
}
