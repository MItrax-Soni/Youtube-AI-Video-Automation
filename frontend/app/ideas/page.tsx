"use client";

import React, { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";
import { getTrends } from "@/lib/api";

const NICHES = [
  "Technology",
  "Science",
  "Business",
  "Health",
  "Finance",
  "Education",
  "Entertainment",
  "Gaming",
  "Travel",
  "Food",
];

export default function IdeasPage() {
  const { getToken } = useAuth();
  const [niche, setNiche] = useState("Technology");
  const [ideas, setIdeas] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDiscover = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await getTrends(niche, token);
      setIdeas(data.ideas);
      if (data.error) setError(data.error);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch trends");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="hero-header">
            <h1>Idea Generator</h1>
            <p>Discover trending video topics with AI</p>
          </div>

          <GlassCard>
            <div style={{ display: "flex", gap: "1rem", alignItems: "end" }}>
              <div style={{ flex: 1 }}>
                <label className="input-label">Niche / Category</label>
                <select
                  className="select-field"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  disabled={loading}
                >
                  {NICHES.map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <button
                className="btn-primary"
                onClick={handleDiscover}
                disabled={loading}
                style={{ whiteSpace: "nowrap" }}
              >
                {loading ? "⏳ Discovering..." : "💡 Discover Trends"}
              </button>
            </div>
          </GlassCard>

          {error && (
            <div style={{
              padding: "0.75rem 1rem",
              background: "rgba(239, 68, 68, 0.08)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: "var(--radius-md)",
              color: "var(--error)",
              fontSize: "0.85rem",
              marginBottom: "1rem",
            }}>
              {error}
            </div>
          )}

          {ideas.length > 0 && (
            <div className="section-title">🔥 Trending Topics</div>
          )}

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
            gap: "1rem",
          }}>
            {ideas.map((idea, i) => (
              <GlassCard key={i}>
                <div style={{
                  display: "flex",
                  gap: "12px",
                  alignItems: "flex-start",
                }}>
                  <span style={{ fontSize: "1.5rem" }}>
                    {["🔥", "🌍", "🚀", "⚡", "🧠", "💡", "🎯", "🌐", "📊", "🔬"][i % 10]}
                  </span>
                  <div>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "4px" }}>
                      {idea}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      Click to use as topic →
                    </div>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>

          {ideas.length === 0 && !loading && (
            <div className="empty-state">
              <h3>Explore Trending Topics</h3>
              <p>Select a niche and click Discover to get AI-powered video topic ideas.</p>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
