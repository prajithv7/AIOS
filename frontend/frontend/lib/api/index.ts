import { api } from "./client";
import {
  AuthResponse,
  Conversation,
  KeyStatus,
  MemoryItem,
  Message,
  ModelInfo,
  Project,
  ProviderInfo,
  CompareResult,
  Recommendation,
  User,
} from "./types";

export const authApi = {
  signup: (email: string, name: string, password: string) =>
    api<AuthResponse>("/api/auth/signup", { method: "POST", body: JSON.stringify({ email, name, password }) }),
  login: (email: string, password: string) =>
    api<AuthResponse>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => api<User>("/api/users/me"),
};

export const keysApi = {
  list: () => api<KeyStatus[]>("/api/keys"),
  connect: (providerId: string, apiKey: string) =>
    api<{ provider_id: string; status: string; masked_key: string }>("/api/keys", {
      method: "POST",
      body: JSON.stringify({ provider_id: providerId, api_key: apiKey }),
    }),
  disconnect: (providerId: string) => api<{ ok: boolean }>(`/api/keys/${providerId}`, { method: "DELETE" }),
};

export const providersApi = {
  list: () => api<ProviderInfo[]>("/api/providers"),
};

export const modelsApi = {
  list: () => api<ModelInfo[]>("/api/models"),
};

export const conversationsApi = {
  list: () => api<Conversation[]>("/api/conversations"),
  create: (title: string, projectId?: string) =>
    api<{ id: string; title: string; project_id: string | null }>("/api/conversations", {
      method: "POST",
      body: JSON.stringify({ title, project_id: projectId ?? null }),
    }),
  get: (id: string) => api<{ id: string; title: string; project_id: string | null }>(`/api/conversations/${id}`),
  messages: (id: string) => api<Message[]>(`/api/conversations/${id}/messages`),
  send: (conversationId: string, content: string, modelId?: string) =>
    api<{ message: Message; model_id: string; provider_id: string; latency_ms: number }>(
      `/api/conversations/${conversationId}/messages`,
      { method: "POST", body: JSON.stringify({ content, modelId }) }
    ),
};

export const compareApi = {
  run: (conversationId: string | null, content: string, modelIds: string[]) =>
    api<CompareResult>("/api/compare", {
      method: "POST",
      body: JSON.stringify({ conversationId, content, modelIds }),
    }),
  get: (runId: string) => api<CompareResult>(`/api/compare/${runId}`),
};

export const routeApi = {
  recommend: (content: string, conversationId?: string) =>
    api<Recommendation>("/api/route/recommend", {
      method: "POST",
      body: JSON.stringify({ content, conversationId }),
    }),
};

export const projectsApi = {
  list: () => api<Project[]>("/api/projects"),
  create: (name: string, description?: string) =>
    api<{ id: string; name: string; description: string | null }>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  memory: (projectId: string) => api<MemoryItem[]>(`/api/projects/${projectId}/memory`),
  createMemory: (projectId: string, type: string, content: string) =>
    api<MemoryItem>(`/api/projects/${projectId}/memory`, {
      method: "POST",
      body: JSON.stringify({ type, content }),
    }),
  updateMemory: (projectId: string, memoryId: string, content: string) =>
    api<MemoryItem>(`/api/projects/${projectId}/memory/${memoryId}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
  deleteMemory: (projectId: string, memoryId: string) =>
    api<{ ok: boolean }>(`/api/projects/${projectId}/memory/${memoryId}`, { method: "DELETE" }),
};
