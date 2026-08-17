/**
 * api.ts — API client for MAiX-YT Studio
 *
 * All calls go directly to the FastAPI backend on Railway.
 * Clerk bearer token is attached for authentication.
 */

import type {
  Job,
  GenerateParams,
  HistoryEntry,
  UserSettings,
  ApiCheckResult,
  TrendsResponse,
  PresetsResponse,
} from "./types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function fetchWithAuth(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res;
}

// ---------------------------------------------------------------------------
// Generate
// ---------------------------------------------------------------------------

export async function startGeneration(
  params: GenerateParams,
  token: string
): Promise<{ job_id: string; status: string }> {
  const res = await fetchWithAuth("/api/generate", {
    method: "POST",
    body: JSON.stringify(params),
  }, token);
  return res.json();
}

export async function getJobStatus(
  jobId: string,
  token: string
): Promise<Job> {
  const res = await fetchWithAuth(`/api/jobs/${jobId}`, {}, token);
  return res.json();
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

export async function getHistory(
  token: string
): Promise<{ generations: HistoryEntry[] }> {
  const res = await fetchWithAuth("/api/history", {}, token);
  return res.json();
}

// ---------------------------------------------------------------------------
// Trends
// ---------------------------------------------------------------------------

export async function getTrends(
  niche: string,
  token: string
): Promise<TrendsResponse> {
  const res = await fetchWithAuth("/api/trends", {
    method: "POST",
    body: JSON.stringify({ niche }),
  }, token);
  return res.json();
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export async function getSettings(
  token: string
): Promise<{ settings: UserSettings }> {
  const res = await fetchWithAuth("/api/settings", {}, token);
  return res.json();
}

export async function updateSettings(
  settings: Partial<UserSettings>,
  token: string
): Promise<{ status: string }> {
  const res = await fetchWithAuth("/api/settings", {
    method: "PUT",
    body: JSON.stringify({ settings }),
  }, token);
  return res.json();
}

// ---------------------------------------------------------------------------
// API Status / Health
// ---------------------------------------------------------------------------

export async function checkApis(
  token: string
): Promise<ApiCheckResult> {
  const res = await fetchWithAuth("/api/api-check", {}, token);
  return res.json();
}

export async function healthCheck(): Promise<{
  status: string;
  service: string;
  version: string;
}> {
  const res = await fetch(`${BACKEND_URL}/`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

export async function getPresets(
  token: string
): Promise<PresetsResponse> {
  const res = await fetchWithAuth("/api/presets", {}, token);
  return res.json();
}

// ---------------------------------------------------------------------------
// Video URL
// ---------------------------------------------------------------------------

export function getVideoUrl(jobId: string): string {
  return `${BACKEND_URL}/api/videos/${jobId}/video.mp4`;
}

export function getThumbnailUrl(jobId: string): string {
  return `${BACKEND_URL}/api/videos/${jobId}/thumbnail.jpg`;
}
