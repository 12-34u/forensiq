/**
 * ForensIQ API client — talks to the FastAPI backend at /api/v1.
 * All methods return parsed JSON or throw on error.
 */

const API_ORIGIN = import.meta.env.VITE_API_URL || "";
const BASE = `${API_ORIGIN}/api/v1`;
const TOKEN_KEY = "forensiq_token";

/** Get the stored JWT token (if any). */
function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const headers = { "Content-Type": "application/json", ...options.headers };

  // Attach JWT token if available
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    headers,
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ── Ingest ──────────────────────────────────────────

/** Upload a .ufdr / .clbe file for ingestion. */
export async function ingestUpload(file, { skipGraph = false } = {}) {
  const form = new FormData();
  form.append("file", file);
  const qs = skipGraph ? "?skip_graph=true" : "";

  // Build headers with auth token (no Content-Type — browser sets multipart boundary)
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}/ingest/upload${qs}`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}

/** Ingest a file already on disk (by server-side path). */
export function ingestPath(path, { skipGraph = false } = {}) {
  const qs = new URLSearchParams({ path, skip_graph: String(skipGraph) });
  return request(`/ingest/path?${qs}`, { method: "POST" });
}

// ── Query ───────────────────────────────────────────

/** Run the full RAG query pipeline. */
export function query(text, options = {}) {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({
      query: text,
      k: options.k ?? 10,
      graph_depth: options.graphDepth ?? 2,
      include_graph: options.includeGraph ?? true,
      skip_cache: options.skipCache ?? false,
      skip_llm: options.skipLlm ?? false,
    }),
  });
}

// ── Pages ───────────────────────────────────────────

export function listPages(extractionId) {
  return request(`/pages/${extractionId}`);
}

// ── Graph ───────────────────────────────────────────

export function graphFull({ limit = 500, projectId } = {}) {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (projectId) qs.set("project_id", projectId);
  return request(`/graph/full?${qs}`);
}

export function graphByEntity(label, { depth = 1, limit = 200 } = {}) {
  const qs = new URLSearchParams({ depth: String(depth), limit: String(limit) });
  return request(`/graph/entity/${label}?${qs}`);
}

export function graphSearch(name, { depth = 2 } = {}) {
  const qs = new URLSearchParams({ depth: String(depth) });
  return request(`/graph/search/${encodeURIComponent(name)}?${qs}`);
}

export function graphExport() {
  return request("/graph/export");
}

// ── Projects ────────────────────────────────────────

/** List only projects uploaded by the current user. */
export function listMyProjects() {
  return request("/graph/my-projects");
}

export function listProjects() {
  return request("/graph/projects");
}

export function graphProject(projectId, { limit = 500 } = {}) {
  const qs = new URLSearchParams({ limit: String(limit) });
  return request(`/graph/project/${projectId}?${qs}`);
}

export function deleteProject(projectId) {
  return request(`/graph/project/${projectId}`, { method: "DELETE" });
}

// ── Stats / Health ──────────────────────────────────

export function getStats() {
  return request("/stats");
}

export function getHealth() {
  return request("/health");
}

// ── Cache ───────────────────────────────────────────

export function cacheStats() {
  return request("/cache/stats");
}

export function cacheFlush() {
  return request("/cache/flush", { method: "DELETE" });
}

// ── LLM ─────────────────────────────────────────────

export function llmStatus() {
  return request("/llm/status");
}

// ── Anomaly detection (LLM-powered) ─────────────────

export function detectAnomalies(projectId) {
  return request(`/anomalies/${projectId}`);
}

// ── Risk Intel (rule-based detection) ────────────────

export function getRiskIntel(projectId) {
  return request(`/riskintel/${projectId}`);
}

// ── Auth (MongoDB Atlas) ─────────────────────────────

/** Register a new user account. */
export async function authSignup({ name, email, password, role, department }) {
  return request("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ name, email, password, role, department }),
  });
}

/** Log in with email + password. */
export async function authLogin({ email, password }) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

/** Request a password reset token. */
export async function authForgotPassword(email) {
  return request("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

/** Reset password using a token. */
export async function authResetPassword(token, newPassword) {
  return request("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

// ── Conversations (per-user chat history) ────────────────

/** Create a new conversation. */
export function createConversation(title = "New Conversation") {
  return request("/conversations", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

/** List all conversations for the current user (newest first). */
export function listConversations() {
  return request("/conversations");
}

/** Get a conversation with full message history. */
export function getConversation(conversationId) {
  return request(`/conversations/${conversationId}`);
}

/** Append a message to a conversation. */
export function appendMessage(conversationId, message) {
  return request(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

/** Rename a conversation. */
export function renameConversation(conversationId, title) {
  return request(`/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

/** Delete a conversation. */
export function deleteConversation(conversationId) {
  return request(`/conversations/${conversationId}`, { method: "DELETE" });
}
