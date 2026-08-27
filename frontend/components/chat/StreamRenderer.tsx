"use client";

export function StreamRenderer({ text }: { text: string }) {
  if (!text) {
    return <p className="text-sm text-muted">Generating…</p>;
  }
  return (
    <p className="whitespace-pre-wrap text-sm text-primary">
      {text}
      <span className="ml-0.5 inline-block h-3 w-1.5 animate-pulse bg-accent align-middle" />
    </p>
  );
}
