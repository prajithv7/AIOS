"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-page">
      <div className="text-center max-w-md mx-auto p-8">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-xl">!</span>
        </div>
        <h1 className="font-serif text-2xl text-primary mb-2">Something went wrong</h1>
        <p className="text-secondary mb-6">
          {error.message || "An unexpected error occurred."}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-accent text-white rounded-card text-sm font-medium"
          >
            Try again
          </button>
          <button
            onClick={() => router.push("/app/chat/new")}
            className="px-4 py-2 border border-border rounded-card text-sm font-medium text-secondary hover:bg-surface"
          >
            Go to workspace
          </button>
        </div>
      </div>
    </div>
  );
}
