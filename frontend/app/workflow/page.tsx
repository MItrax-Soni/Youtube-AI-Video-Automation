"use client";

import React from "react";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";

export default function WorkflowPage() {
  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="hero-header">
            <h1>n8n Workflow</h1>
            <p>Automation workflow integration</p>
          </div>

          <GlassCard>
            <div style={{ textAlign: "center", padding: "3rem 2rem" }}>
              <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔄</div>
              <h3 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                n8n Not Connected
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", maxWidth: "500px", margin: "0 auto", lineHeight: 1.8 }}>
                The n8n workflow integration is optional. To enable it, configure
                <code style={{ color: "#c4b5fd", padding: "2px 6px", background: "rgba(80, 100, 255, 0.08)", borderRadius: "4px" }}>
                  {" "}N8N_WEBHOOK_URL{" "}
                </code>
                in your environment variables.
              </p>
              <div style={{ marginTop: "1.5rem" }}>
                <a
                  href="https://n8n.io"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                  style={{ textDecoration: "none" }}
                >
                  Learn about n8n →
                </a>
              </div>
            </div>
          </GlassCard>
        </main>
      </div>
    </>
  );
}
