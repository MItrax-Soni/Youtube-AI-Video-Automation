"use client";

import React, { useEffect, useRef } from "react";

/**
 * NeonBackground — Animated neon grid with floating orbs and light streaks.
 * Ported from inject_dynamic_background() in app.py.
 */
export default function NeonBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate random light streaks
    if (!containerRef.current) return;
    const streakContainer = containerRef.current.querySelector(".neon-streaks");
    if (!streakContainer || streakContainer.children.length > 0) return;

    const colors = [
      "rgba(80, 100, 255, 0.22)",
      "rgba(140, 60, 220, 0.18)",
      "rgba(200, 50, 180, 0.15)",
      "rgba(100, 80, 255, 0.20)",
    ];

    for (let i = 0; i < 5; i++) {
      const streak = document.createElement("div");
      streak.className = "streak";
      const x = 8 + Math.random() * 84;
      const h = 120 + Math.random() * 160;
      const dur = 8 + Math.random() * 8;
      const delay = Math.random() * 12;
      const color = colors[i % colors.length];

      streak.style.cssText = `
        left: ${x}%;
        height: ${h}px;
        background: linear-gradient(to bottom, transparent, ${color}, transparent);
        animation-duration: ${dur}s;
        animation-delay: ${delay}s;
      `;
      streakContainer.appendChild(streak);
    }
  }, []);

  return (
    <div className="neon-grid-wrap" ref={containerRef}>
      <div className="neon-grid-lines" />
      <div className="neon-color-wash" />
      <div className="glow-orb orb-blue" />
      <div className="glow-orb orb-purple" />
      <div className="glow-orb orb-magenta" />
      <div className="neon-streaks" />
    </div>
  );
}
