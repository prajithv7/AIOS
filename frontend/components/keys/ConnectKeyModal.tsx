"use client";

import { useState } from "react";
import { KeyStatus } from "@/lib/api/types";
import { Button, Card, Input } from "@/components/ui";

interface ConnectKeyModalProps {
  provider: KeyStatus | null;
  onClose: () => void;
  onSubmit: (providerId: string, apiKey: string) => Promise<void>;
}

export function ConnectKeyModal({ provider, onClose, onSubmit }: ConnectKeyModalProps) {
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!provider) return null;

  const providerId = provider.provider_id;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit(providerId, apiKey);
      setApiKey("");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <Card className="w-full max-w-md" >
        <div onClick={(e) => e.stopPropagation()}>
          <p className="eyebrow">Connect provider</p>
          <h2 className="mt-2 text-xl text-primary">{provider.display_name}</h2>
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div>
              <label className="mb-1 block text-sm text-secondary">API key</label>
              <Input
                type="password"
                autoFocus
                required
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-…"
              />
            </div>
            {error && <p className="text-sm text-[#c0392b]">{error}</p>}
            <p className="text-xs text-muted">Keys are encrypted at rest and never sent back to your browser.</p>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Connecting…" : "Connect"}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
