"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";
import ProgressTracker from "@/components/ProgressTracker";
import { startGeneration, getJobStatus } from "@/lib/api";
import type { Job, JobStatus } from "@/lib/types";

const TONES = [
  "Neutral",
  "Friendly",
  "Serious",
  "Conversational",
  "Energetic",
  "Inspirational",
  "Dramatic",
  "Authoritative",
];

const STYLES = [
  "Documentary",
  "Educational Explainer",
  "Storytelling",
  "News",
  "Cinematic",
  "Entertainment",
  "Listicle",
  "Case Study",
];

const DURATIONS = [
  { label: "30s (Short)", value: 30 },
  { label: "60s (Medium)", value: 60 },
  { label: "180s (Extended)", value: 180 },
];

const LANGUAGES = ["English", "Hindi", "Gujarati"];
const ASPECT_RATIOS = ["16:9", "9:16"];

export default function GeneratePage() {
  const { getToken } = useAuth();

  // Form state
  const [topic, setTopic] = useState("");
  const [tone, setTone] = useState("Neutral");
  const [style, setStyle] = useState("Documentary");
  const [duration, setDuration] = useState(60);
  const [language, setLanguage] = useState("English");
  const [aspectRatio, setAspectRatio] = useState("16:9");

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const pollJobStatus = useCallback(
    async (jobId: string) => {
      try {
        const token = await getToken();
        if (!token) return;
        const job = await getJobStatus(jobId, token);
        setCurrentJob(job);

        // Stop polling if job is done or failed
        if (
          job.status === "completed" ||
          job.status === "failed" ||
          job.status === "cancelled"
        ) {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setIsGenerating(false);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    },
    [getToken]
  );

  const handleGenerate = async () => {
    if (!topic.trim()) return;

    setError(null);
    setIsGenerating(true);
    setCurrentJob(null);

    try {
      const token = await getToken();
      if (!token) {
        setError("Authentication required");
        setIsGenerating(false);
        return;
      }

      const result = await startGeneration(
        {
          topic: topic.trim(),
          tone: tone.toLowerCase(),
          duration,
          voice_gender: "female",
          voice_engine: "Edge-TTS (Neural)",
          style,
          language: language.toLowerCase(),
          aspect_ratio: aspectRatio,
        },
        token
      );

      // Start polling every 3 seconds
      pollRef.current = setInterval(
        () => pollJobStatus(result.job_id),
        3000
      );

      // Also do an immediate poll
      pollJobStatus(result.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
      setIsGenerating(false);
    }
  };

  const isTerminal =
    currentJob?.status === "completed" ||
    currentJob?.status === "failed" ||
    currentJob?.status === "cancelled";

  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          {/* Hero */}
          <div className="hero-header">
            <h1>Generate Video</h1>
            <p>Create AI-powered videos from any topic</p>
          </div>

          <div className="dashboard-grid">
            {/* Left: Form */}
            <div>
              <GlassCard>
                {/* Topic */}
                <label className="input-label">Topic / Prompt</label>
                <textarea
                  className="input-field"
                  rows={3}
                  placeholder="Enter your video topic or a detailed prompt..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  disabled={isGenerating}
                  style={{ resize: "vertical", marginBottom: "1rem" }}
                />

                {/* Options Grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "1rem",
                    marginBottom: "1rem",
                  }}
                >
                  <div>
                    <label className="input-label">Duration</label>
                    <select
                      className="select-field"
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      disabled={isGenerating}
                    >
                      {DURATIONS.map((d) => (
                        <option key={d.value} value={d.value}>
                          {d.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="input-label">Tone</label>
                    <select
                      className="select-field"
                      value={tone}
                      onChange={(e) => setTone(e.target.value)}
                      disabled={isGenerating}
                    >
                      {TONES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="input-label">Style</label>
                    <select
                      className="select-field"
                      value={style}
                      onChange={(e) => setStyle(e.target.value)}
                      disabled={isGenerating}
                    >
                      {STYLES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="input-label">Language</label>
                    <select
                      className="select-field"
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      disabled={isGenerating}
                    >
                      {LANGUAGES.map((l) => (
                        <option key={l} value={l}>
                          {l}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="input-label">Aspect Ratio</label>
                    <select
                      className="select-field"
                      value={aspectRatio}
                      onChange={(e) => setAspectRatio(e.target.value)}
                      disabled={isGenerating}
                    >
                      {ASPECT_RATIOS.map((ar) => (
                        <option key={ar} value={ar}>
                          {ar}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  className="btn-primary"
                  style={{ width: "100%", padding: "14px" }}
                  onClick={handleGenerate}
                  disabled={!topic.trim() || isGenerating}
                >
                  {isGenerating ? "⏳ Generating..." : "🎬 Generate Video"}
                </button>

                {error && (
                  <div
                    style={{
                      marginTop: "1rem",
                      padding: "0.75rem 1rem",
                      background: "rgba(239, 68, 68, 0.08)",
                      border: "1px solid rgba(239, 68, 68, 0.2)",
                      borderRadius: "var(--radius-md)",
                      color: "var(--error)",
                      fontSize: "0.85rem",
                    }}
                  >
                    ❌ {error}
                  </div>
                )}
              </GlassCard>
            </div>

            {/* Right: Progress / Results */}
            <div>
              {currentJob && (
                <GlassCard hover={false}>
                  <div className="section-title" style={{ marginTop: 0 }}>
                    {isTerminal ? "📊 Results" : "⏳ Progress"}
                  </div>

                  <ProgressTracker
                    status={currentJob.status}
                    progress={currentJob.progress}
                    currentStep={currentJob.current_step}
                  />

                  {/* Show video player when complete */}
                  {currentJob.status === "completed" &&
                    currentJob.video_url && (
                      <div style={{ marginTop: "1.5rem" }}>
                        <div className="section-title">🎬 Your Video</div>
                        <video
                          controls
                          style={{ width: "100%", borderRadius: "var(--radius-lg)" }}
                        >
                          <source
                            src={currentJob.video_url}
                            type="video/mp4"
                          />
                        </video>
                        {currentJob.video_title && (
                          <div
                            style={{
                              marginTop: "0.5rem",
                              fontWeight: 600,
                              color: "var(--text-primary)",
                            }}
                          >
                            {currentJob.video_title}
                          </div>
                        )}
                      </div>
                    )}

                  {/* Error display */}
                  {currentJob.status === "failed" && currentJob.error && (
                    <div
                      style={{
                        marginTop: "1rem",
                        padding: "1rem",
                        background: "rgba(239, 68, 68, 0.06)",
                        border: "1px solid rgba(239, 68, 68, 0.15)",
                        borderRadius: "var(--radius-md)",
                        color: "var(--error)",
                        fontSize: "0.85rem",
                      }}
                    >
                      <strong>Error:</strong> {currentJob.error}
                    </div>
                  )}
                </GlassCard>
              )}

              {!currentJob && (
                <div className="empty-state" style={{ padding: "3rem 2rem" }}>
                  <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>
                    🎬
                  </div>
                  <h3>Ready to Create</h3>
                  <p>
                    Enter a topic and hit Generate to start your AI video
                    pipeline.
                  </p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
