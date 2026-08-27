import { ApiErrorBody } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export class ApiError extends Error {
  code: string;
  requestId?: string;
  status: number;

  constructor(status: number, body?: ApiErrorBody) {
    super(body?.error?.message || "Request failed");
    this.code = body?.error?.code || "INTERNAL_ERROR";
    this.requestId = body?.error?.requestId;
    this.status = status;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });

  if (!res.ok) {
    let body: ApiErrorBody | undefined;
    try {
      body = await res.json();
    } catch {
      /* ignore */
    }
    if (res.status === 401 && body?.error?.code === "AUTH_REQUIRED") {
      const refreshed = await tryRefresh();
      if (refreshed) {
        return api<T>(path, options);
      }
    }
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

let refreshing: Promise<boolean> | null = null;

export async function tryRefresh(): Promise<boolean> {
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/auth/refresh`, { method: "POST", credentials: "include" });
        if (res.ok) {
          const data = await res.json();
          accessToken = data.access_token;
          return true;
        }
        accessToken = null;
        return false;
      } catch {
        accessToken = null;
        return false;
      } finally {
        refreshing = null;
      }
    })();
  }
  return refreshing;
}

export function logout() {
  accessToken = null;
  fetch(`${API_URL}/api/auth/logout`, { method: "POST", credentials: "include" }).catch(() => undefined);
}
