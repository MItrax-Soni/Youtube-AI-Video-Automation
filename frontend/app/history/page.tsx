"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp } from "lucide-react";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";
import { getHistory, getFullVideoUrl } from "@/lib/api";
import type { HistoryEntry } from "@/lib/types";

export default function HistoryPage() {
  const { getToken } = useAuth();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await getHistory(token);
        setEntries(data.generations);
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, [getToken]);

  const toggleExpand = (jobId: string) => {
    setExpandedJobId(expandedJobId === jobId ? null : jobId);
  };

  const getBadgeClass = (status: string) => {
    if (status === "completed") return "badge-success";
    if (status === "failed") return "badge-error";
    if (status === "queued") return "badge-queued";
    return "badge-processing";
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="hero-header">
            <h1>Generation History</h1>
            <p>All your past video generations and metadata</p>
          </div>

          {loading ? (
            <GlassCard hover={false}>
              <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-secondary)" }}>
                Loading history...
              </div>
            </GlassCard>
          ) : entries.length === 0 ? (
            <div className="empty-state">
              <h3>No generations yet</h3>
              <p>Your video generation history will appear here.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {entries.map((entry) => {
                const totalTime = Object.values(entry.timing || {}).reduce((a, b) => a + b, 0).toFixed(0);
                const isExpanded = expandedJobId === entry.job_id;
                
                return (
                  <GlassCard key={entry.job_id} hover={false} style={{ padding: 0, overflow: "hidden" }}>
                    {/* Header (Clickable) */}
                    <div 
                      onClick={() => toggleExpand(entry.job_id)}
                      style={{ 
                        padding: "1.25rem", 
                        cursor: "pointer", 
                        display: "flex", 
                        justifyContent: "space-between", 
                        alignItems: "center",
                        backgroundColor: isExpanded ? "rgba(255, 255, 255, 0.03)" : "transparent",
                        transition: "background-color 0.2s"
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: "1.1rem", color: "var(--text-primary)" }}>
                          {entry.title || entry.topic}
                        </div>
                        <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.5rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                          <span>🕐 {formatDate(entry.created_at)}</span>
                          <span>⏱ {totalTime}s</span>
                          <span>🎞 {entry.scene_count} scenes</span>
                          <span>📏 {entry.duration}s</span>
                        </div>
                      </div>
                      
                      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        <span className={`status-badge ${getBadgeClass(entry.status)}`}>
                          {entry.status.toUpperCase()}
                        </span>
                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </div>
                    </div>

                    {/* Expanded Content */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3, ease: "easeInOut" }}
                          style={{ borderTop: "1px solid rgba(255, 255, 255, 0.05)" }}
                        >
                          <div style={{ padding: "1.25rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
                            
                            {/* Left Column: Video & Error */}
                            <div>
                              {entry.status === "completed" && entry.video_url ? (
                                <div>
                                  <div className="section-title" style={{ marginTop: 0, fontSize: "0.9rem" }}>🎬 Video Preview</div>
                                  <video
                                    controls
                                    style={{ width: "100%", borderRadius: "var(--radius-md)", border: "1px solid rgba(255, 255, 255, 0.1)" }}
                                  >
                                    <source src={getFullVideoUrl(entry.video_url)} type="video/mp4" />
                                  </video>
                                </div>
                              ) : entry.status === "failed" ? (
                                <div>
                                  <div className="section-title" style={{ marginTop: 0, fontSize: "0.9rem", color: "#ff8888" }}>❌ Generation Failed</div>
                                  <div style={{ padding: "1rem", backgroundColor: "rgba(255, 100, 100, 0.1)", borderRadius: "var(--radius-sm)", color: "#ff8888", fontSize: "0.85rem", whiteSpace: "pre-wrap" }}>
                                    {entry.errors?.join("\n") || "Unknown error occurred"}
                                  </div>
                                </div>
                              ) : (
                                <div>
                                  <div className="section-title" style={{ marginTop: 0, fontSize: "0.9rem" }}>⏳ Processing</div>
                                  <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Video is still generating...</p>
                                </div>
                              )}
                            </div>

                            {/* Right Column: Metadata */}
                            <div>
                              <div className="section-title" style={{ marginTop: 0, fontSize: "0.9rem" }}>⚙️ Configuration</div>
                              
                              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1.5rem" }}>
                                {entry.params?.tone && (
                                  <span style={{ padding: "4px 8px", backgroundColor: "rgba(100, 100, 255, 0.1)", borderRadius: "4px", fontSize: "0.75rem", border: "1px solid rgba(100, 100, 255, 0.2)" }}>
                                    Tone: {entry.params.tone}
                                  </span>
                                )}
                                {entry.params?.style && (
                                  <span style={{ padding: "4px 8px", backgroundColor: "rgba(100, 100, 255, 0.1)", borderRadius: "4px", fontSize: "0.75rem", border: "1px solid rgba(100, 100, 255, 0.2)" }}>
                                    Style: {entry.params.style}
                                  </span>
                                )}
                                {entry.params?.voice_engine && (
                                  <span style={{ padding: "4px 8px", backgroundColor: "rgba(100, 255, 100, 0.1)", borderRadius: "4px", fontSize: "0.75rem", border: "1px solid rgba(100, 255, 100, 0.2)", color: "#88ff88" }}>
                                    Voice: {entry.params.voice_engine} ({entry.params.voice_gender})
                                  </span>
                                )}
                                {entry.params?.aspect_ratio && (
                                  <span style={{ padding: "4px 8px", backgroundColor: "rgba(255, 255, 255, 0.05)", borderRadius: "4px", fontSize: "0.75rem", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                                    Aspect Ratio: {entry.params.aspect_ratio}
                                  </span>
                                )}
                              </div>

                              {entry.metadata?.youtube && (
                                <>
                                  <div className="section-title" style={{ fontSize: "0.9rem" }}>🏷️ YouTube Tags</div>
                                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                                    {entry.metadata.youtube.tags?.map((tag: string) => (
                                      <span key={tag} style={{ padding: "2px 6px", backgroundColor: "rgba(255, 255, 255, 0.05)", borderRadius: "4px", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                                        #{tag}
                                      </span>
                                    ))}
                                  </div>
                                </>
                              )}
                            </div>

                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </GlassCard>
                );
              })}
            </div>
          )}
        </main>
      </div>
    </>
  );
}
