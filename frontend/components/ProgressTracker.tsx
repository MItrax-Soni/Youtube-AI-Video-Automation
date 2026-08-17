"use client";

import React from "react";
import { PIPELINE_STEPS } from "@/lib/types";
import type { JobStatus } from "@/lib/types";

interface ProgressTrackerProps {
  status: JobStatus;
  progress: number;
  currentStep: string;
}

/**
 * ProgressTracker — Shows pipeline progress with animated stage indicators.
 * Ported from the Streamlit pipeline progress UI.
 */
export default function ProgressTracker({
  status,
  progress,
  currentStep,
}: ProgressTrackerProps) {
  const activeIndex = PIPELINE_STEPS.findIndex((s) => s.key === status);

  const getStageClass = (index: number) => {
    if (status === "failed") {
      if (index === activeIndex) return "stage-error";
      if (index < activeIndex) return "stage-done";
      return "stage-pending";
    }
    if (status === "completed") return "stage-done";
    if (index < activeIndex) return "stage-done";
    if (index === activeIndex) return "stage-active";
    return "stage-pending";
  };

  const getStageIcon = (index: number) => {
    if (status === "failed" && index === activeIndex) return "❌";
    if (status === "completed") return "✅";
    if (index < activeIndex) return "✅";
    if (index === activeIndex) return "⏳";
    return "⬜";
  };

  return (
    <div>
      {/* Progress Bar */}
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "1rem",
          fontSize: "0.8rem",
          color: "var(--text-secondary)",
        }}
      >
        <span>{currentStep}</span>
        <span>{progress}%</span>
      </div>

      {/* Pipeline Steps */}
      {PIPELINE_STEPS.map((step, index) => (
        <div key={step.key} className={`progress-stage ${getStageClass(index)}`}>
          <span className="stage-icon">{getStageIcon(index)}</span>
          <span>{step.icon}</span>
          <span>{step.label}</span>
        </div>
      ))}
    </div>
  );
}
