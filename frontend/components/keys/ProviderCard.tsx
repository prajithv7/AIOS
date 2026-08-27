import { KeyStatus } from "@/lib/api/types";
import { Badge, Button } from "@/components/ui";

interface ProviderCardProps {
  provider: KeyStatus;
  onConnect: (provider: KeyStatus) => void;
  onDisconnect: (provider: KeyStatus) => void;
}

export function ProviderCard({ provider, onConnect, onDisconnect }: ProviderCardProps) {
  return (
    <div className="flex items-center justify-between rounded-card border border-border bg-surface p-4">
      <div>
        <p className="font-medium text-primary">{provider.display_name}</p>
        <div className="mt-1 flex items-center gap-2">
          {provider.connected ? (
            <Badge>Connected</Badge>
          ) : (
            <span className="inline-flex items-center rounded-full bg-muted/20 px-2.5 py-0.5 text-xs text-muted">
              Not connected
            </span>
          )}
          {provider.masked_key && (
            <span className="font-mono text-xs text-muted">{provider.masked_key}</span>
          )}
        </div>
      </div>
      <div>
        {provider.connected ? (
          <Button variant="danger" onClick={() => onDisconnect(provider)}>
            Disconnect
          </Button>
        ) : (
          <Button onClick={() => onConnect(provider)}>Connect</Button>
        )}
      </div>
    </div>
  );
}
