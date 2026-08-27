"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth";
import { usePathname } from "next/navigation";
import { Providers } from "@/components/Providers";

const NAV = [
  { href: "/app", label: "Chat" },
  { href: "/app/projects", label: "Projects" },
  { href: "/app/keys", label: "Keys" },
  { href: "/app/settings", label: "Settings" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!user) {
      router.replace("/login");
    }
  }, [user, router]);

  if (!user) return null;

  return (
    <Providers>
      <div className="flex min-h-screen">
        <aside className="flex w-56 flex-col border-r border-border bg-surface p-4">
          <Link href="/app" className="mb-6 flex items-center gap-2 px-1">
            <span className="inline-block h-3 w-3 rounded-full bg-accent" />
            <span className="font-medium text-primary">AIOS</span>
          </Link>
          <nav className="flex flex-col gap-1">
            {NAV.map((n) => {
              const active = pathname === n.href || (n.href === "/app" && pathname.startsWith("/app/chat"));
              return (
                <Link
                  key={n.href}
                  href={n.href}
                  className={`rounded px-3 py-2 text-sm transition-colors ${
                    active ? "bg-accent-soft text-accent" : "text-secondary hover:bg-surface hover:text-primary"
                  }`}
                >
                  {n.label}
                </Link>
              );
            })}
          </nav>
          <div className="mt-auto border-t border-border pt-4">
            <p className="px-1 text-sm text-primary">{user.name}</p>
            <button
              onClick={() => logout().then(() => router.push("/login"))}
              className="mt-2 rounded px-3 py-1 text-sm text-muted hover:bg-surface hover:text-primary"
            >
              Log out
            </button>
          </div>
        </aside>
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </Providers>
  );
}
