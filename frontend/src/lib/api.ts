import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// ── Types ──────────────────────────────────────────────────────────────────

export interface Ambiguity {
  mention: string;
  candidates: string[];
}

export interface QueryResult {
  table: Record<string, unknown>[];
  columns: string[];
  nl_summary: string;
  row_count: number;
}

export interface QueryResponse {
  question: string;
  query_type: string;
  generated_sql: string;
  explanation: string;
  result: QueryResult;
  latency_ms: number;
  ambiguities: Ambiguity[];
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}

export interface SchemaColumn {
  id: number;
  table_name: string;
  column_name: string;
  description: string | null;
  synonyms: string[];
  is_sensitive: boolean;
  created_at: string;
  updated_at: string;
}

export interface FewShotExample {
  id: number;
  question: string;
  sql: string;
  query_type: string;
  created_at: string;
  updated_at: string;
}

export interface QueryLog {
  id: number;
  nl_query: string;
  query_type: string | null;
  generated_sql: string | null;
  status: string;
  error_message: string | null;
  latency_ms: number | null;
  row_count: number | null;
  created_at: string;
}

export interface GuardrailConfig {
  key: string;
  value: string;
  description: string | null;
}

export interface ModelConfig {
  key: string;
  value: string;
  description: string | null;
}

// ── API Calls ──────────────────────────────────────────────────────────────

export const queryApi = {
  run: (question: string) =>
    api.post<QueryResponse | ErrorResponse>("/query", { question }),
};

export const schemaApi = {
  introspect: () => api.get<{ schema: Record<string, Record<string, string>> }>("/admin/schema/introspect"),
  listColumns: () => api.get<SchemaColumn[]>("/admin/schema/columns"),
  createColumn: (data: Partial<SchemaColumn>) => api.post<SchemaColumn>("/admin/schema/columns", data),
  updateColumn: (id: number, data: Partial<SchemaColumn>) =>
    api.patch<SchemaColumn>(`/admin/schema/columns/${id}`, data),
  deleteColumn: (id: number) => api.delete(`/admin/schema/columns/${id}`),
};

export const examplesApi = {
  list: (queryType?: string) =>
    api.get<FewShotExample[]>("/admin/examples", { params: { query_type: queryType } }),
  create: (data: Partial<FewShotExample>) => api.post<FewShotExample>("/admin/examples", data),
  update: (id: number, data: Partial<FewShotExample>) =>
    api.patch<FewShotExample>(`/admin/examples/${id}`, data),
  delete: (id: number) => api.delete(`/admin/examples/${id}`),
  syncEmbeddings: () => api.post("/admin/examples/sync-embeddings"),
};

export const logsApi = {
  list: (page: number = 1, pageSize: number = 20, status?: string) =>
    api.get("/admin/logs", { params: { page, page_size: pageSize, status } }),
};

export const guardrailsApi = {
  list: () => api.get<GuardrailConfig[]>("/admin/guardrails"),
  update: (key: string, value: string) =>
    api.patch<GuardrailConfig>(`/admin/guardrails/${key}`, { value }),
};

export const modelConfigApi = {
  list: () => api.get<ModelConfig[]>("/admin/config"),
  update: (key: string, value: string) =>
    api.patch<ModelConfig>(`/admin/config/${key}`, { value }),
};
