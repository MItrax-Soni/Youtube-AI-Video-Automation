"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import { checkApis } from "@/lib/api";
import type { ApiCheckResult } from "@/lib/types";

export default function ApiStatusPage() {
  const { getToken } = useAuth();
  const [statuses, setStatuses] = useState<ApiCheckResult>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await checkApis(token);
        setStatuses(data);
      } catch (err) {
        console.error("Failed to fetch API status:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchStatus();
  }, [getToken]);

  const apiIcons: Record<string, string> = {
    Gemini: "🤖",
    Pexels: "📷",
    Pixabay: "🖼️",
    ElevenLabs: "🎙️",
    FFmpeg: "🎥",
  };

  const getRowClass = (status: string) => {
    if (status === "connected") return "api-ok";
    if (status === "missing_key") return "api-warn";
    return "api-err";
  };

  const getDotClass = (status: string) => {
    if (status === "connected") return "dot-green";
    if (status === "missing_key") return "dot-yellow";
    return "dot-red";
  };

  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="hero-header">
            <h1>API Status</h1>
            <p>Service connectivity dashboard</p>
          </div>

          <div className="glass-card" style={{ padding: "1.5rem" }}>
            {loading ? (
              <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-secondary)" }}>
                Checking services...
              </div>
            ) : Object.keys(statuses).length === 0 ? (
              <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-secondary)" }}>
                No API status data available. Make sure the backend is running.
              </div>
            ) : (
              Object.entries(statuses).map(([name, info]) => (
                <div
                  key={name}
                  className={`api-status-row ${getRowClass(info.status)}`}
                >
                  <span className={`api-dot ${getDotClass(info.status)}`} />
                  <span style={{ fontWeight: 600, minWidth: "120px" }}>
                    {apiIcons[name] || "🔧"} {name}
                  </span>
                  <span style={{ marginLeft: "auto", opacity: 0.7, fontSize: "0.8rem" }}>
                    {info.message}
                  </span>
                </div>
              ))
            )}
          </div>
        </main>
      </div>
    </>
  );
}
