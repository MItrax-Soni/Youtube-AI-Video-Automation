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
// Stats (Dashboard)
// ---------------------------------------------------------------------------

export interface StatsResponse {
  total_videos: number;
  unique_topics: number;
  today_count: number;
  avg_time: string;
  success_rate: string;
  recent: {
    job_id: string;
    title: string;
    status: string;
    created_at: string;
    timing: Record<string, number>;
  }[];
}

export async function getStats(token: string): Promise<StatsResponse> {
  const res = await fetchWithAuth("/api/stats", {}, token);
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

/**
 * Build a full video URL from the video_url stored in the job document.
 *
 * The worker stores either:
 *   - A relative path like "/api/videos/video_20260818/final_video.mp4"
 *   - An absolute URL like "https://drive.google.com/..." (future Google Drive)
 *
 * For relative paths, we prepend BACKEND_URL.
 * For absolute URLs, we return them as-is.
 */
export function getFullVideoUrl(videoUrl: string): string {
  if (!videoUrl) return "";
  // Already a full URL (https:// or http://)
  if (videoUrl.startsWith("http://") || videoUrl.startsWith("https://")) {
    return videoUrl;
  }
  // Relative path — prepend backend URL
  return `${BACKEND_URL}${videoUrl}`;
}

// ---------------------------------------------------------------------------
// Google Drive
// ---------------------------------------------------------------------------

export async function getDriveStatus(token: string): Promise<{
  configured: boolean;
  connected: boolean;
  email?: string;
  display_name?: string;
  message?: string;
}> {
  const res = await fetchWithAuth("/api/drive/status", {}, token);
  return res.json();
}

export async function getDriveAuthUrl(token: string): Promise<{ auth_url: string }> {
  const res = await fetchWithAuth("/api/drive/auth-url", {}, token);
  return res.json();
}

export async function disconnectDrive(token: string): Promise<{ status: string }> {
  const res = await fetchWithAuth(
    "/api/drive/disconnect",
    { method: "POST" },
    token
  );
  return res.json();
}

