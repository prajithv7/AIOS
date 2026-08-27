export function StepRow({ index, title, description }: { index: number; title: string; description: string }) {
  // Odd steps sit on accent-soft with accent eyebrow; even steps on surface with muted eyebrow (banded strip).
  const odd = index % 2 === 0;
  return (
    <div
      className={`rounded-card border border-border p-5 ${odd ? "bg-accent-soft" : "bg-surface"}`}
    >
      <span className={`eyebrow text-xs font-semibold ${odd ? "text-accent" : "text-muted"}`}>
        {String(index + 1).padStart(2, "0")}
      </span>
      <h3 className="mt-2 text-lg text-primary">{title}</h3>
      <p className="mt-1 text-sm text-secondary">{description}</p>
    </div>
  );
}
