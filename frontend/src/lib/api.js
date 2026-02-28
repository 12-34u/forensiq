/**
 * ForensIQ API client — talks to the FastAPI backend at /api/v1.
 * All methods return parsed JSON or throw on error.
 */

const BASE = "/api/v1";

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
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
  const res = await fetch(`${BASE}/ingest/upload${qs}`, {
    method: "POST",
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
