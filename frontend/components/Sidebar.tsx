"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import {
  LayoutDashboard,
  Video,
  Lightbulb,
  History,
  Workflow,
  KeyRound,
  Settings,
  Info,
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, href: "/" },
  { label: "Generate Video", icon: Video, href: "/generate" },
  { label: "Idea Generator", icon: Lightbulb, href: "/ideas" },
  { label: "Generation History", icon: History, href: "/history" },
  { label: "n8n Workflow", icon: Workflow, href: "/workflow" },
  { label: "API Status", icon: KeyRound, href: "/api-status" },
  { label: "Settings", icon: Settings, href: "/settings" },
  { label: "About", icon: Info, href: "/about" },
];

/**
 * Sidebar — Navigation sidebar with animated logo, nav links, system status.
 * Ported from render_sidebar() in app.py.
 */
export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      {/* Gradient accent line on right edge */}
      <div className="sidebar-accent" />

      {/* Brand */}
      <div className="sidebar-brand">
        <div className="logo-container">
          <div className="logo-spinner" />
          <div className="logo-glow" />
          <div className="logo-inner">
            <span className="logo-emoji">🎬</span>
          </div>
        </div>
        <h2 className="brand-title">MAiX-YT Studio</h2>
        <p className="brand-sub">AI VIDEO ENGINE</p>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item ${isActive ? "nav-item-active" : ""}`}
            >
              <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="sidebar-status">
        <div className="status-indicator">
          <span className="status-dot status-dot-online" />
          <span className="status-text-online">System Online</span>
        </div>
        <div className="status-subtitle">All services operational</div>
      </div>

      {/* User section */}
      <div className="sidebar-user">
        <UserButton
          appearance={{
            elements: {
              avatarBox: "sidebar-avatar",
            },
          }}
        />
        <span className="sidebar-version">v3.0</span>
      </div>
    </aside>
  );
}
