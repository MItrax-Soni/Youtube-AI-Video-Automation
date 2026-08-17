"use client";

import React from "react";

interface StatsCardProps {
  icon: string;
  value: string | number;
  label: string;
  className?: string;
}

/**
 * StatsCard — Metric display card with icon, value, and label.
 * Ported from the dashboard metrics row in app.py.
 */
export default function StatsCard({
  icon,
  value,
  label,
  className = "",
}: StatsCardProps) {
  return (
    <div className={`stats-card ${className}`}>
      <div className="stats-card-icon">{icon}</div>
      <div className="stats-card-value">{value}</div>
      <div className="stats-card-label">{label}</div>
    </div>
  );
}
