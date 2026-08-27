export type Role = "system" | "user" | "assistant" | "tool";

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
}

export interface ModelInfo {
  model_id: string;
  provider_id: string;
  display_name: string;
  capabilities: Record<string, boolean>;
  context_window: number;
  supports_streaming: boolean;
  supports_tools: boolean;
  supports_vision: boolean;
  status: string;
  authorized: boolean;
}

export interface ProviderInfo {
  provider_id: string;
  name: string;
  display_name: string;
  auth_type: string;
  connected: boolean;
}

export interface KeyStatus {
  provider_id: string;
  name: string;
  display_name: string;
  connected: boolean;
  active: boolean;
  masked_key: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: Role;
  content: string;
  provider_id: string | null;
  model_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
}

export interface Conversation {
  id: string;
  title: string;
  project_id: string | null;
  message_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  conversation_count: number;
  memory_count: number;
  last_active: string | null;
}

export interface MemoryItem {
  id: string;
  type: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string | null;
}

export interface ModelRun {
  model_id: string;
  provider_id: string;
  content: string;
  status: "success" | "error" | "pending";
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  error_code: string | null;
  error_message: string | null;
}

export interface CompareResult {
  runId: string;
  task: string;
  runs: ModelRun[];
  winner: string | null;
  scores: Record<string, number>;
  reason: string;
  criteria: string[];
}

export interface Recommendation {
  task_type: string;
  recommended_model_id: string;
  candidates: string[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    requestId: string;
  };
}

export type ErrorCode =
  | "AUTH_REQUIRED"
  | "FORBIDDEN"
  | "INVALID_REQUEST"
  | "MODEL_NOT_FOUND"
  | "PROVIDER_NOT_FOUND"
  | "PROVIDER_UNAUTHORIZED"
  | "PROVIDER_UNAVAILABLE"
  | "MODEL_UNAVAILABLE"
  | "RATE_LIMITED"
  | "CONTEXT_TOO_LARGE"
  | "AI_REQUEST_FAILED"
  | "INTERNAL_ERROR";
