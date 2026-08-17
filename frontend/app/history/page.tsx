"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";
import { getHistory } from "@/lib/api";
import type { HistoryEntry } from "@/lib/types";

export default function HistoryPage() {
  const { getToken } = useAuth();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

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
            <p>All your past video generations</p>
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
            entries.map((entry) => (
              <div key={entry.job_id} className="history-card">
                <div className="history-card-header">
                  <div>
                    <div className="history-title">
                      {entry.title || entry.topic}
                    </div>
                    <div className="history-meta">
                      🕐 {formatDate(entry.created_at)} &nbsp;·&nbsp;
                      ⏱ {Object.values(entry.timing).reduce((a, b) => a + b, 0).toFixed(0)}s &nbsp;·&nbsp;
                      🎞 {entry.scene_count} scenes &nbsp;·&nbsp;
                      📏 {entry.duration}s
                    </div>
                  </div>
                  <span className={`status-badge ${getBadgeClass(entry.status)}`}>
                    {entry.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))
          )}
        </main>
      </div>
    </>
  );
}
