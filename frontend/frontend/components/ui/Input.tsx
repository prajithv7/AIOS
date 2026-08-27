"use client";

import { InputHTMLAttributes } from "react";

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:border-accent focus:outline-none ${className}`}
      {...props}
    />
  );
}
