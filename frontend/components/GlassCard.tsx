"use client";

import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  style?: React.CSSProperties;
  onClick?: () => void;
}

/**
 * GlassCard — Reusable glassmorphism card with optional hover effects.
 * Ported from .glass-card CSS class in app.py.
 */
export default function GlassCard({
  children,
  className = "",
  hover = true,
  style,
  onClick,
}: GlassCardProps) {
  return (
    <div
      className={`glass-card ${hover ? "glass-card-hover" : ""} ${className}`}
      style={style}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}
