import { API_URL, getAccessToken } from "../api/client";

export interface StreamHandlers {
  onToken: (token: string, modelId: string, providerId?: string) => void;
  onDone: () => void;
  onError: (code: string, message: string) => void;
}

/**
 * Opens a POST-based SSE stream to /chat/stream. Uses fetch streaming so we can
 * attach the Authorization header. Falls back to native EventSource if needed.
 */
export async function streamChat(
  conversationId: string,
  content: string,
  modelId: string,
  handlers: StreamHandlers
): Promise<AbortController> {
  const controller = new AbortController();
  const token = getAccessToken();

  try {
    const res = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: "include",
      body: JSON.stringify({ conversationId, content, modelId }),
      signal: controller.signal,
    });

    if (!res.ok || !res.body) {
      handlers.onError("AI_REQUEST_FAILED", "Stream failed to start");
      return controller;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const pump = async (): Promise<void> => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const rawEvent = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            handleEvent(rawEvent, handlers);
          }
        }
        if (buffer.trim()) {
          handleEvent(buffer, handlers);
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          handlers.onError("AI_REQUEST_FAILED", "Stream connection lost");
        }
      }
    };

    pump();
  } catch {
    handlers.onError("AI_REQUEST_FAILED", "Unable to connect to stream");
  }

  return controller;
}

function handleEvent(raw: string, handlers: StreamHandlers) {
  let event = "message";
  const lines = raw.split("\n");
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (!dataLines.length) return;
  const payload = JSON.parse(dataLines.join("\n"));

  switch (event) {
    case "token":
      handlers.onToken(payload.token || "", payload.model_id || "", payload.provider_id);
      break;
    case "done":
      handlers.onDone();
      break;
    case "error":
      handlers.onError(payload.code || "AI_REQUEST_FAILED", payload.message || "Stream error");
      break;
  }
}
