"use client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8787";

const TOKEN_KEY = "saw_token";
const USER_KEY = "saw_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token: string, username: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, username);
}

export function getUser(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(USER_KEY) || "";
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  raw = false
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (raw) return res as unknown as T;
  return (await res.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<{
      access_token: string;
      token_type: string;
      user_id: number;
      username: string;
    }>("/api/auth/login/json", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  createTask: (prompt: string, file: File | null) => {
    const form = new FormData();
    form.append("prompt", prompt);
    form.append("code_request", "false");
    if (file) form.append("file", file);
    return request<{ task_id: number; status: string }>("/api/tasks", {
      method: "POST",
      body: form,
    });
  },

  taskDetail: (id: number) => request<any>(`/api/tasks/${id}`),

  taskEventsUrl: (id: number) => {
    const token = getToken() || "";
    return `${API_URL}/api/tasks/${id}/events?token=${encodeURIComponent(token)}`;
  },

  listTasks: () => request<any[]>("/api/tasks"),

  listModels: () => request<{ models: any[] }>("/api/models"),

  testModel: (role: string) =>
    request<any>(`/api/models/test?model=${encodeURIComponent(role)}`, {
      method: "POST",
    }),

  listDocuments: () => request<any[]>("/api/documents"),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<any>("/api/documents/upload", {
      method: "POST",
      body: form,
    });
  },

  ingestKnowledge: (body: {
    document_id: string;
    document_name?: string;
    text: string;
    section?: string;
    version?: string;
    classification?: string;
  }) =>
    request<any>("/api/knowledge/ingest", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  searchKnowledge: (query: string, limit = 5) =>
    request<{ query: string; results: any[]; count: number }>(
      "/api/knowledge/search",
      {
        method: "POST",
        body: JSON.stringify({ query, limit }),
      }
    ),

  listRuns: () => request<any[]>("/api/agents/runs"),

  sovereignty: () => request<any>("/api/system/sovereignty"),
  health: () => request<any>("/api/system/health"),

  listAudit: (limit = 100) =>
    request<any[]>(`/api/audit?limit=${limit}`),
};

export async function downloadArtifact(
  id: number,
  filename: string
): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_URL}/api/artifacts/${id}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export { API_URL };
