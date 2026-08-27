"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { useAuthStore } from "@/lib/stores/auth";
import { Button, Card, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-sm">
        <p className="eyebrow">Welcome back</p>
        <h1 className="mt-2 text-2xl text-primary">Log in</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm text-secondary">Email</label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm text-secondary">Password</label>
            <Input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="text-sm text-[#c0392b]">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Logging in…" : "Log in"}
          </Button>
        </form>
        <p className="mt-4 text-sm text-muted">
          No account?{" "}
          <Link href="/signup" className="text-accent hover:underline">Sign up</Link>
        </p>
      </Card>
    </main>
  );
}
