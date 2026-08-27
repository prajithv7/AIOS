"use client";

import { useEffect, useState } from "react";
import { useKeyVaultStore } from "@/lib/stores/keys";
import { KeyStatus } from "@/lib/api/types";
import { ProviderCard } from "@/components/keys/ProviderCard";
import { ConnectKeyModal } from "@/components/keys/ConnectKeyModal";

export default function KeysPage() {
  const { status, fetch, connect, disconnect } = useKeyVaultStore();
  const [modalProvider, setModalProvider] = useState<KeyStatus | null>(null);
  const [disconnectProvider, setDisconnectProvider] = useState<KeyStatus | null>(null);

  useEffect(() => {
    fetch().catch(() => undefined);
  }, [fetch]);

  return (
    <div className="mx-auto max-w-2xl p-8">
      <p className="eyebrow">Provider keys</p>
      <h1 className="mt-2 text-2xl text-primary">API key vault</h1>
      <p className="mt-2 text-sm text-secondary">
        Connect your provider keys to enable chat and comparison. Keys are encrypted at rest.
      </p>

      <div className="mt-6 space-y-3">
        {status.map((p) => (
          <ProviderCard
            key={p.provider_id}
            provider={p}
            onConnect={setModalProvider}
            onDisconnect={setDisconnectProvider}
          />
        ))}
      </div>

      <ConnectKeyModal
        provider={modalProvider}
        onClose={() => setModalProvider(null)}
        onSubmit={async (providerId, apiKey) => {
          await connect(providerId, apiKey);
        }}
      />

      {disconnectProvider && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-card border border-border bg-surface p-5">
            <h2 className="text-lg text-primary">Disconnect {disconnectProvider.display_name}?</h2>
            <p className="mt-2 text-sm text-secondary">
              Your stored key for this provider will be removed. This cannot be undone.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => setDisconnectProvider(null)}
                className="rounded px-4 py-2 text-sm text-secondary hover:bg-surface"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  await disconnect(disconnectProvider.provider_id);
                  setDisconnectProvider(null);
                }}
                className="rounded bg-[#c0392b] px-4 py-2 text-sm text-white"
              >
                Disconnect
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
