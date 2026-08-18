/**
 * types.ts — TypeScript interfaces for MAiX-YT Studio
 */

// ---------------------------------------------------------------------------
// Job / Generation
// ---------------------------------------------------------------------------

export type JobStatus =
  | "queued"
  | "generating_script"
  | "generating_voice"
  | "generating_visuals"
  | "assembling_video"
  | "uploading"
  | "completed"
  | "failed"
  | "cancelled";

export interface GenerateParams {
  topic: string;
  tone: string;
  duration: number;
  voice_gender: string;
  voice_engine: string;
  style: string;
  language: string;
  aspect_ratio: string;
}

export interface Job {
  _id: string;
  user_id: string;
  topic: string;
  status: JobStatus;
  progress: number;
  current_step: string;
  params: GenerateParams;
  created_at: string;
  updated_at: string;
  video_url: string | null;
  thumbnail_url: string | null;
  video_title: string | null;
  metadata: Record<string, unknown>;
  error: string | null;
  failed_step: string | null;
  timing: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Generation History
// ---------------------------------------------------------------------------

export interface HistoryEntry {
  job_id: string;
  title: string;
  topic: string;
  status: JobStatus;
  created_at: string;
  duration: number;
  scene_count: number;
  video_url: string | null;
  thumbnail_url: string | null;
  timing: Record<string, number>;
  params: GenerateParams;
  metadata: Record<string, any>;
  errors: string[];
  youtube_meta: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// API Status
// ---------------------------------------------------------------------------

export interface ApiServiceStatus {
  status: "connected" | "disconnected" | "missing_key" | "error";
  message: string;
}

export type ApiCheckResult = Record<string, ApiServiceStatus>;

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export interface UserSettings {
  default_duration: number;
  default_tone: string;
  default_voice: string;
  default_voice_gender: string;
  default_style: string;
  enable_transition_effects: boolean;
  enable_motion_effects: boolean;
  enable_text_highlights: boolean;
  enable_subtitles: boolean;
  enable_bg_music: boolean;
  bg_music_volume: number;
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

export interface DurationPreset {
  key: string;
  label: string;
  seconds: number;
  scenes: number;
  min_words: number;
  max_words: number;
}

export interface PresetsResponse {
  duration_presets: Record<string, DurationPreset>;
  styles: string[];
  tones: string[];
  voice_engines: string[];
  languages: string[];
}

// ---------------------------------------------------------------------------
// Trends
// ---------------------------------------------------------------------------

export interface TrendsResponse {
  ideas: string[];
  error?: string;
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

export interface NavItem {
  label: string;
  icon: string;
  href: string;
}

// Pipeline step info for ProgressTracker
export interface PipelineStep {
  key: string;
  label: string;
  icon: string;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  { key: "generating_script", label: "Script Generation", icon: "📝" },
  { key: "generating_voice", label: "Voice Generation", icon: "🎙️" },
  { key: "generating_visuals", label: "Visual Collection", icon: "🖼️" },
  { key: "assembling_video", label: "Video Assembly", icon: "🎬" },
  { key: "uploading", label: "Upload & Finalize", icon: "☁️" },
];
