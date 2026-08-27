"use client";

import { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  children: ReactNode;
}

export function Button({ variant = "primary", className = "", children, ...props }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-accent text-white hover:opacity-90",
    secondary: "bg-transparent border border-border text-primary hover:bg-surface",
    ghost: "bg-transparent text-secondary hover:bg-surface hover:text-primary",
    danger: "bg-transparent border border-[#c0392b] text-[#c0392b] hover:bg-[#c0392b] hover:text-white",
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
