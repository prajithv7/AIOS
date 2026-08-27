import { ModelRun } from "@/lib/api/types";
import { Card } from "@/components/ui";

export function ComparisonGrid({ runs }: { runs: ModelRun[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {runs.map((run) => {
        const failed = run.status === "error";
        return (
          <Card key={run.model_id} className={failed ? "opacity-60" : ""}>
            <div className="flex items-center justify-between">
              <p className="font-medium text-primary">{run.model_id}</p>
              <p className="font-mono text-xs text-muted">{run.provider_id}</p>
            </div>
            {failed ? (
              <div className="mt-3 rounded border border-[#c0392b]/40 bg-[#c0392b]/5 p-3">
                <p className="text-sm text-[#c0392b]">
                  {run.error_code}: {run.error_message}
                </p>
              </div>
            ) : (
              <>
                <p className="mt-3 whitespace-pre-wrap text-sm text-primary">{run.content}</p>
                <div className="mt-3 flex gap-4 border-t border-border pt-2 text-xs text-muted">
                  <span>{run.latency_ms} ms</span>
                  <span>{run.input_tokens} in</span>
                  <span>{run.output_tokens} out</span>
                </div>
              </>
            )}
          </Card>
        );
      })}
    </div>
  );
}
