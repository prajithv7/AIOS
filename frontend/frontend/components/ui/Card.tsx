import { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-card border border-border bg-surface p-5 ${className}`}>
      {children}
    </div>
  );
}
