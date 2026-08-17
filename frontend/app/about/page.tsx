"use client";

import React from "react";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";

export default function AboutPage() {
  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="hero-header">
            <h1>About</h1>
            <p>MAiX-YT Studio v3.0</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <GlassCard>
              <h3>🎬 MAiX-YT Studio</h3>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.8, marginTop: "0.5rem" }}>
                AI-powered YouTube video automation platform. Generate scripts,
                voiceovers, visuals, and fully assembled videos with a single click.
              </p>
              <div style={{ marginTop: "1.5rem" }}>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <span className="tag-pill">Gemini AI</span>
                  <span className="tag-pill">ElevenLabs</span>
                  <span className="tag-pill">Edge-TTS</span>
                  <span className="tag-pill">Pexels</span>
                  <span className="tag-pill">Pixabay</span>
                  <span className="tag-pill">FFmpeg</span>
                </div>
              </div>
            </GlassCard>

            <GlassCard>
              <h3>⚙️ Architecture</h3>
              <div style={{ color: "var(--text-secondary)", lineHeight: 2, marginTop: "0.5rem", fontSize: "0.88rem" }}>
                <div><strong style={{ color: "var(--text-primary)" }}>Frontend:</strong> Next.js on Vercel</div>
                <div><strong style={{ color: "var(--text-primary)" }}>Auth:</strong> Clerk</div>
                <div><strong style={{ color: "var(--text-primary)" }}>Backend:</strong> FastAPI on Railway</div>
                <div><strong style={{ color: "var(--text-primary)" }}>Database:</strong> MongoDB Atlas</div>
                <div><strong style={{ color: "var(--text-primary)" }}>Worker:</strong> Separate process on Railway</div>
                <div><strong style={{ color: "var(--text-primary)" }}>Storage:</strong> Railway Volume</div>
              </div>
            </GlassCard>

            <GlassCard>
              <h3>🎯 Pipeline Steps</h3>
              <div style={{ marginTop: "0.5rem" }}>
                {[
                  { icon: "📝", label: "Script Generation", desc: "Gemini AI creates structured video scripts" },
                  { icon: "🎙️", label: "Voice Generation", desc: "TTS narration with Edge-TTS or ElevenLabs" },
                  { icon: "🖼️", label: "Visual Collection", desc: "Stock footage from Pexels & Pixabay" },
                  { icon: "🎬", label: "Video Assembly", desc: "FFmpeg compositing with effects" },
                  { icon: "☁️", label: "Metadata & Upload", desc: "SEO-optimized YouTube metadata" },
                ].map((step, i) => (
                  <div key={i} style={{
                    display: "flex",
                    gap: "12px",
                    padding: "8px 0",
                    borderBottom: i < 4 ? "1px solid rgba(100, 100, 255, 0.06)" : "none",
                  }}>
                    <span style={{ fontSize: "1.2rem" }}>{step.icon}</span>
                    <div>
                      <div style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.88rem" }}>{step.label}</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{step.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>

            <GlassCard>
              <h3>📄 Version Info</h3>
              <div style={{ color: "var(--text-secondary)", lineHeight: 2, marginTop: "0.5rem", fontSize: "0.88rem" }}>
                <div><strong style={{ color: "var(--text-primary)" }}>Version:</strong> 3.0.0</div>
                <div><strong style={{ color: "var(--text-primary)" }}>Codename:</strong> MAiX-YT Studio</div>
                <div><strong style={{ color: "var(--text-primary)" }}>License:</strong> Private</div>
              </div>
            </GlassCard>
          </div>
        </main>
      </div>
    </>
  );
}
