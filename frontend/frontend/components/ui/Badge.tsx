export function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-medium text-accent">
      {children}
    </span>
  );
}
