"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { useAuthStore } from "@/lib/stores/auth";
import { Button, Card, Input } from "@/components/ui";

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuthStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await signup(email, name, password);
      router.push("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <Card className="w-full max-w-sm">
        <p className="eyebrow">Get started</p>
        <h1 className="mt-2 text-2xl text-primary">Create your account</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm text-secondary">Name</label>
            <Input type="text" required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm text-secondary">Email</label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-sm text-secondary">Password</label>
            <Input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="text-sm text-[#c0392b]">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Creating…" : "Sign up"}
          </Button>
        </form>
        <p className="mt-4 text-sm text-muted">
          Already have an account?{" "}
          <Link href="/login" className="text-accent hover:underline">Log in</Link>
        </p>
      </Card>
    </main>
  );
}
