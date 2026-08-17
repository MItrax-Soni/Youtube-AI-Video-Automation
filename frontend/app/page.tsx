"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Video,
  Lightbulb,
  History,
  Settings,
  KeyRound,
  TrendingUp,
} from "lucide-react";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import StatsCard from "@/components/StatsCard";

const QUICK_ACTIONS = [
  {
    icon: "🎬",
    label: "Generate Video",
    desc: "Create an AI-powered video",
    href: "/generate",
    lucide: Video,
  },
  {
    icon: "💡",
    label: "Idea Generator",
    desc: "Discover trending topics",
    href: "/ideas",
    lucide: Lightbulb,
  },
  {
    icon: "📜",
    label: "History",
    desc: "View past generations",
    href: "/history",
    lucide: History,
  },
  {
    icon: "🔑",
    label: "API Status",
    desc: "Check service connectivity",
    href: "/api-status",
    lucide: KeyRound,
  },
  {
    icon: "⚙️",
    label: "Settings",
    desc: "Configure defaults",
    href: "/settings",
    lucide: Settings,
  },
  {
    icon: "📈",
    label: "Trends",
    desc: "AI topic discovery",
    href: "/ideas",
    lucide: TrendingUp,
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};

export default function DashboardPage() {
  // TODO: Fetch real stats from backend in Phase 2
  const stats = {
    totalVideos: 0,
    uniqueTopics: 0,
    todayCount: 0,
    avgTime: "—",
    successRate: "—",
  };

  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          {/* Hero Header */}
          <div className="hero-header">
            <h1>Dashboard</h1>
            <p>MAiX-YT Studio — Command Center</p>
          </div>

          {/* Stats Grid */}
          <div className="section-title">📊 System Metrics</div>
          <div className="stats-grid">
            <motion.div
              custom={0}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <StatsCard
                icon="🎬"
                value={stats.totalVideos}
                label="Total Videos"
              />
            </motion.div>
            <motion.div
              custom={1}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <StatsCard
                icon="📝"
                value={stats.uniqueTopics}
                label="Unique Topics"
              />
            </motion.div>
            <motion.div
              custom={2}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <StatsCard
                icon="⚡"
                value={stats.todayCount}
                label="Today"
              />
            </motion.div>
            <motion.div
              custom={3}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <StatsCard
                icon="⏱️"
                value={stats.avgTime}
                label="Avg Time"
              />
            </motion.div>
            <motion.div
              custom={4}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <StatsCard
                icon="✅"
                value={stats.successRate}
                label="Success Rate"
              />
            </motion.div>
          </div>

          {/* Main Grid: Quick Actions + Activity */}
          <div className="dashboard-grid">
            {/* Left Column */}
            <div>
              {/* Quick Actions */}
              <div className="section-title">🚀 Quick Actions</div>
              <div className="quick-actions-grid">
                {QUICK_ACTIONS.map((action, i) => (
                  <motion.div
                    key={action.href + action.label}
                    custom={i}
                    initial="hidden"
                    animate="visible"
                    variants={fadeUp}
                  >
                    <Link
                      href={action.href}
                      className="quick-action-card"
                    >
                      <div className="quick-action-icon">{action.icon}</div>
                      <div className="quick-action-label">{action.label}</div>
                      <div className="quick-action-desc">{action.desc}</div>
                    </Link>
                  </motion.div>
                ))}
              </div>

              {/* Recent Activity */}
              <div className="section-title">📜 Recent Activity</div>
              <div className="empty-state" style={{ padding: "2rem" }}>
                <h3>No videos generated yet</h3>
                <p>
                  Use <strong>Generate Video</strong> to create your first
                  AI-powered video!
                </p>
              </div>
            </div>

            {/* Right Column */}
            <div>
              {/* API Status Panel */}
              <div className="section-title">🔌 API Status</div>
              <div className="glass-card" style={{ padding: "1rem" }}>
                <div className="api-status-row api-ok">
                  <span className="api-dot dot-green" />
                  <span>Backend</span>
                  <span style={{ marginLeft: "auto", opacity: 0.6 }}>
                    Ready
                  </span>
                </div>
                <div className="api-status-row api-ok">
                  <span className="api-dot dot-green" />
                  <span>Gemini AI</span>
                  <span style={{ marginLeft: "auto", opacity: 0.6 }}>
                    Check on API Status page
                  </span>
                </div>
                <div className="api-status-row api-ok">
                  <span className="api-dot dot-green" />
                  <span>ElevenLabs</span>
                  <span style={{ marginLeft: "auto", opacity: 0.6 }}>
                    Check on API Status page
                  </span>
                </div>
                <div className="api-status-row api-ok">
                  <span className="api-dot dot-green" />
                  <span>Pexels</span>
                  <span style={{ marginLeft: "auto", opacity: 0.6 }}>
                    Check on API Status page
                  </span>
                </div>
                <div style={{ marginTop: "0.5rem", textAlign: "center" }}>
                  <Link
                    href="/api-status"
                    style={{
                      fontSize: "0.8rem",
                      color: "#818cf8",
                    }}
                  >
                    View Full Status →
                  </Link>
                </div>
              </div>

              {/* Getting Started */}
              <div className="section-title">🎯 Getting Started</div>
              <div className="glass-card">
                <div
                  style={{
                    fontSize: "0.85rem",
                    lineHeight: 1.8,
                    color: "var(--text-secondary)",
                  }}
                >
                  <div style={{ marginBottom: "8px" }}>
                    <strong style={{ color: "var(--text-primary)" }}>
                      1.
                    </strong>{" "}
                    Enter a topic or use Idea Generator
                  </div>
                  <div style={{ marginBottom: "8px" }}>
                    <strong style={{ color: "var(--text-primary)" }}>
                      2.
                    </strong>{" "}
                    Choose tone, style & duration
                  </div>
                  <div style={{ marginBottom: "8px" }}>
                    <strong style={{ color: "var(--text-primary)" }}>
                      3.
                    </strong>{" "}
                    Click Generate — AI does the rest
                  </div>
                  <div>
                    <strong style={{ color: "var(--text-primary)" }}>
                      4.
                    </strong>{" "}
                    Preview, download, or upload to YouTube
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
