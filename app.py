"""
app.py — Streamlit Dashboard for AI YouTube Automation Platform

Premium futuristic UI with animated particle background, glassmorphism,
dynamic gradient effects, and professional typography.

Run with: streamlit run app.py

Pages:
  - Dashboard: Global statistics and system overview.
  - Generate Video: Topic input, settings, live progress, results.
  - Generation History: Browse, preview, download, delete past generations.
  - n8n Workflow: Automation workflow status and testing.
  - API Status: Comprehensive API dashboard.
  - Settings: Configurable defaults saved locally.
  - About: Project information.
"""

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

from scripts.config import OUTPUT_DIR, ASSETS_DIR, get_n8n_webhook_url
from scripts.config import get_scene_count, get_duration_preset, DURATION_PRESETS, SettingsManager
from scripts.pipeline import run_pipeline
from scripts.trend import discover_trends


# Load user settings
USER_SETTINGS = SettingsManager.load()

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MAiX-YT Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Premium Dark Theme + Dynamic Background
# ---------------------------------------------------------------------------
def inject_css():
    """Inject premium futuristic neon-grid dark-theme CSS design system."""
    st.markdown("""
    <style>
    /* ===== Google Font ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ===== CSS Custom Properties ===== */
    :root {
        --bg-primary: #050510;
        --bg-card: rgba(12, 12, 35, 0.65);
        --bg-card-hover: rgba(18, 18, 50, 0.78);
        --border-subtle: rgba(100, 100, 255, 0.08);
        --border-glow: rgba(120, 80, 220, 0.30);
        --neon-blue: #4f7cff;
        --neon-purple: #8b5cf6;
        --neon-magenta: #d946ef;
        --neon-cyan: #22d3ee;
        --text-primary: #f0f0ff;
        --text-secondary: rgba(255, 255, 255, 0.55);
        --text-muted: rgba(255, 255, 255, 0.35);
        --success: #4ade80;
        --warning: #fbbf24;
        --error: #f87171;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ===== Global ===== */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: linear-gradient(160deg,
            #050510 0%,
            #0a0a2e 25%,
            #100a30 50%,
            #180535 75%,
            #1f0535 100%) !important;
        color: var(--text-primary);
    }
    [data-testid="stMainBlockContainer"] {
        position: relative;
        z-index: 1;
        padding-top: 2.5rem !important;
    }

    /* ===== Neon Grid Background ===== */
    .neon-grid-wrap {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }
    .neon-grid-lines {
        position: absolute;
        top: -60px; left: -60px;
        width: calc(100% + 120px);
        height: calc(100% + 120px);
        background-image:
            linear-gradient(rgba(80, 100, 255, 0.055) 1px, transparent 1px),
            linear-gradient(90deg, rgba(80, 100, 255, 0.055) 1px, transparent 1px);
        background-size: 55px 55px;
        animation: grid-scroll 35s linear infinite;
    }
    .neon-color-wash {
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg,
            rgba(30, 60, 255, 0.14) 0%,
            rgba(80, 40, 180, 0.07) 35%,
            rgba(160, 40, 160, 0.11) 65%,
            rgba(220, 60, 180, 0.09) 100%);
    }
    .glow-orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(100px);
        will-change: transform;
    }
    .orb-blue {
        width: 600px; height: 600px;
        top: -8%; left: -5%;
        background: radial-gradient(circle, rgba(50, 80, 255, 0.18), transparent 70%);
        animation: orb-float 28s ease-in-out infinite;
    }
    .orb-purple {
        width: 500px; height: 500px;
        top: 45%; right: -8%;
        background: radial-gradient(circle, rgba(140, 60, 220, 0.14), transparent 70%);
        animation: orb-float 32s ease-in-out infinite reverse;
    }
    .orb-magenta {
        width: 450px; height: 450px;
        bottom: -5%; left: 25%;
        background: radial-gradient(circle, rgba(210, 60, 180, 0.12), transparent 70%);
        animation: orb-float 36s ease-in-out infinite 4s;
    }
    .streak {
        position: absolute;
        width: 1.5px;
        background: linear-gradient(to bottom, transparent, rgba(120, 80, 255, 0.35), transparent);
        animation: streak-fall linear infinite;
        opacity: 0;
    }

    /* ===== Custom Scrollbar ===== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(100, 100, 255, 0.2);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(100, 100, 255, 0.4); }

    /* ===== Streamlit Header ===== */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8, 8, 32, 0.96) 0%, rgba(12, 6, 28, 0.98) 100%) !important;
        backdrop-filter: blur(28px) !important;
        -webkit-backdrop-filter: blur(28px) !important;
        border-right: 1px solid rgba(80, 80, 255, 0.06) !important;
        position: relative;
        overflow: hidden;
    }
    /* Remove Streamlit's bulky default top padding in the sidebar */
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }
    section[data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle at 30% 20%, rgba(79, 124, 255, 0.06) 0%, transparent 50%),
                    radial-gradient(circle at 70% 80%, rgba(139, 92, 246, 0.04) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    section[data-testid="stSidebar"]::after {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 2px; height: 100%;
        background: linear-gradient(to bottom,
            rgba(79, 124, 255, 0.5),
            rgba(139, 92, 246, 0.4),
            rgba(217, 70, 239, 0.25),
            transparent);
        pointer-events: none;
        z-index: 10;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background: transparent !important;
        position: relative;
        z-index: 1;
    }
    .sidebar-brand {
        text-align: center;
        padding: 0 1rem 0.8rem;
        position: relative;
    }
    .sidebar-brand::after {
        content: '';
        display: block;
        width: 60%;
        height: 1px;
        margin: 12px auto 0;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.4), transparent);
    }

    /* ===== Animated Logo with Rotating Border ===== */
    .logo-container {
        position: relative;
        width: 110px;
        height: 110px;
        margin: 0 auto 14px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .logo-spinner {
        position: absolute;
        inset: -3px;
        border-radius: 50%;
        background: conic-gradient(
            from 0deg,
            #4f7cff,
            #8b5cf6,
            #d946ef,
            #f472b6,
            #22d3ee,
            #4f7cff
        );
        animation: logo-rotate 4s linear infinite;
        z-index: 0;
    }
    .logo-spinner::after {
        content: '';
        position: absolute;
        inset: 3px;
        border-radius: 50%;
        background: rgba(8, 8, 32, 0.97);
    }
    .logo-glow {
        position: absolute;
        inset: -8px;
        border-radius: 50%;
        background: conic-gradient(
            from 180deg,
            transparent 40%,
            rgba(79, 124, 255, 0.25) 50%,
            transparent 60%
        );
        animation: logo-rotate 4s linear infinite;
        filter: blur(10px);
        z-index: 0;
    }
    .logo-img {
        position: relative;
        z-index: 1;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(20, 20, 50, 0.9);
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
    }
    @keyframes logo-rotate {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    .sidebar-brand h2 {
        font-size: 1.45rem;
        font-weight: 900;
        margin: 0;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 40%, #e879f9 70%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% 200%;
        animation: brand-shimmer 4s ease-in-out infinite;
        letter-spacing: -0.5px;
        filter: drop-shadow(0 0 12px rgba(139, 92, 246, 0.3));
    }
    .sidebar-brand .brand-sub {
        color: rgba(196, 181, 253, 0.55);
        font-size: 0.65rem;
        margin: 6px 0 0 0;
        letter-spacing: 3px;
        text-transform: uppercase;
        font-weight: 500;
    }
    @keyframes brand-shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    /* Sidebar nav radio items — sleek minimalistic design */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        padding: 12px 20px !important;
        border-radius: 0 !important;
        margin-bottom: 4px;
        transition: all 0.2s ease !important;
        border: none !important;
        border-right: 2px solid transparent !important;
        cursor: pointer;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label span {
        color: rgba(200, 200, 240, 0.6) !important;
        -webkit-text-fill-color: rgba(200, 200, 240, 0.6) !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.5px;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        background: linear-gradient(90deg, rgba(79, 124, 255, 0.04) 0%, transparent 100%) !important;
        border-right: 2px solid rgba(139, 92, 246, 0.4) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover span {
        color: #e0e7ff !important;
        -webkit-text-fill-color: #e0e7ff !important;
        transform: translateX(4px);
    }
    
    /* Active nav item — sleek right accent */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"],
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(79, 124, 255, 0.08) 0%, transparent 100%) !important;
        border-right: 3px solid var(--neon-cyan) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] span,
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) p,
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:has(input:checked) span {
        color: var(--neon-cyan) !important;
        -webkit-text-fill-color: var(--neon-cyan) !important;
        font-weight: 600 !important;
        text-shadow: 0 0 8px rgba(34, 211, 238, 0.3);
        transform: translateX(4px);
    }

    /* Sidebar section dividers */
    .nav-section-label {
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: rgba(139, 92, 246, 0.45);
        padding: 12px 16px 4px;
        margin-top: 4px;
    }

    /* Sidebar general text visibility */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: rgba(200, 200, 240, 0.80) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stCaption"] {
        color: rgba(139, 92, 246, 0.4) !important;
    }

    /* ===== Hero Header ===== */
    .hero-header {
        background: linear-gradient(135deg,
            rgba(10, 10, 40, 0.82) 0%,
            rgba(30, 20, 60, 0.78) 40%,
            rgba(40, 15, 55, 0.82) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(100, 80, 255, 0.10);
        padding: 2.5rem 3rem;
        border-radius: var(--radius-xl);
        margin-bottom: 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow:
            0 8px 40px rgba(0, 0, 0, 0.4),
            0 0 80px rgba(100, 80, 255, 0.03),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        animation: fade-up 0.6s ease-out;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg,
            transparent 0%,
            var(--neon-blue) 20%,
            var(--neon-purple) 50%,
            var(--neon-magenta) 80%,
            transparent 100%);
        animation: shimmer 3s ease-in-out infinite;
    }
    .hero-header::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background:
            radial-gradient(circle at 30% 50%, rgba(80, 100, 255, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 70% 50%, rgba(140, 60, 220, 0.06) 0%, transparent 50%);
        animation: hero-drift 12s ease-in-out infinite;
        pointer-events: none;
    }
    .hero-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 900;
        margin: 0 0 0.3rem 0;
        position: relative;
        z-index: 1;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #ffffff 0%, #c4b5fd 60%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-header p {
        color: var(--text-secondary);
        font-size: 1rem;
        position: relative;
        z-index: 1;
        margin: 0;
    }

    /* ===== Glass Card ===== */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all var(--transition);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
        animation: fade-up 0.5s ease-out;
    }
    .glass-card:hover {
        border-color: var(--border-glow);
        box-shadow:
            0 8px 40px rgba(100, 80, 255, 0.08),
            0 0 60px rgba(100, 80, 255, 0.03);
        transform: translateY(-2px);
        background: var(--bg-card-hover);
    }
    .glass-card h3 {
        color: var(--text-primary);
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    /* ===== Progress Stages ===== */
    .progress-stage {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 14px 20px;
        border-radius: var(--radius-md);
        margin-bottom: 6px;
        font-size: 0.95rem;
        transition: all var(--transition);
        position: relative;
        overflow: hidden;
        animation: fade-up 0.4s ease-out;
    }
    .stage-pending {
        background: rgba(255, 255, 255, 0.015);
        color: var(--text-muted);
        border: 1px solid rgba(255, 255, 255, 0.03);
    }
    .stage-active {
        background: linear-gradient(135deg, rgba(80, 100, 255, 0.10), rgba(140, 60, 220, 0.10));
        color: #c4b5fd;
        border: 1px solid rgba(140, 100, 255, 0.25);
        box-shadow: 0 0 30px rgba(120, 80, 255, 0.08);
    }
    .stage-active::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(140, 100, 255, 0.12), transparent);
        animation: stage-sweep 2s ease-in-out infinite;
    }
    .stage-done {
        background: rgba(34, 197, 94, 0.04);
        color: var(--success);
        border: 1px solid rgba(34, 197, 94, 0.12);
    }
    .stage-error {
        background: rgba(239, 68, 68, 0.04);
        color: var(--error);
        border: 1px solid rgba(239, 68, 68, 0.12);
    }
    .stage-icon {
        font-size: 1.1rem;
        width: 24px;
        text-align: center;
    }

    /* ===== API Status ===== */
    .api-status-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        border-radius: var(--radius-sm);
        margin-bottom: 5px;
        font-size: 0.82rem;
        transition: all 0.3s ease;
    }
    .api-ok   { background: rgba(34,197,94,0.05);  color: var(--success); border: 1px solid rgba(34,197,94,0.10); }
    .api-warn { background: rgba(250,204,21,0.05); color: var(--warning); border: 1px solid rgba(250,204,21,0.10); }
    .api-err  { background: rgba(239,68,68,0.05);  color: var(--error);   border: 1px solid rgba(239,68,68,0.10); }
    .api-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }
    .dot-green  { background: var(--success); box-shadow: 0 0 10px rgba(74,222,128,0.5); animation: dot-pulse 2s ease-in-out infinite; }
    .dot-yellow { background: var(--warning); box-shadow: 0 0 10px rgba(251,191,36,0.5); animation: dot-pulse 2s ease-in-out infinite 0.5s; }
    .dot-red    { background: var(--error);   box-shadow: 0 0 10px rgba(248,113,113,0.5); animation: dot-pulse 2s ease-in-out infinite 1s; }

    /* ===== History Cards ===== */
    .history-card {
        background: var(--bg-card);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.3rem 1.5rem;
        margin-bottom: 0.8rem;
        transition: all var(--transition);
        position: relative;
        overflow: hidden;
        animation: fade-up 0.5s ease-out;
    }
    .history-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-blue), var(--neon-purple), var(--neon-magenta), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .history-card:hover {
        border-color: var(--border-glow);
        background: var(--bg-card-hover);
        transform: translateY(-2px);
        box-shadow: 0 8px 40px rgba(100, 80, 255, 0.08);
    }
    .history-card:hover::before { opacity: 1; }
    .history-title {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 6px;
    }
    .history-meta {
        color: var(--text-secondary);
        font-size: 0.8rem;
        line-height: 1.6;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    .badge-success { background: rgba(34,197,94,0.08); color: var(--success); border: 1px solid rgba(34,197,94,0.18); }
    .badge-partial { background: rgba(250,204,21,0.08); color: var(--warning); border: 1px solid rgba(250,204,21,0.18); }
    .badge-error   { background: rgba(239,68,68,0.08); color: var(--error);   border: 1px solid rgba(239,68,68,0.18); }

    /* ===== Section Titles ===== */
    .section-title {
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: -0.3px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(80, 100, 255, 0.25), rgba(140, 60, 220, 0.1), transparent);
        margin-left: 12px;
    }

    /* ===== Tag Pills ===== */
    .tag-pill {
        display: inline-block;
        background: rgba(80, 100, 255, 0.06);
        color: #a78bfa;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        margin: 3px;
        border: 1px solid rgba(80, 100, 255, 0.10);
        transition: all 0.3s ease;
    }
    .tag-pill:hover {
        background: rgba(80, 100, 255, 0.14);
        border-color: rgba(80, 100, 255, 0.25);
        box-shadow: 0 0 14px rgba(80, 100, 255, 0.08);
    }

    /* ===== Scene Badge ===== */
    .scene-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: var(--radius-sm);
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: capitalize;
    }

    /* ===== Metric Cards ===== */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        padding: 18px !important;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
        transition: all var(--transition) !important;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
        opacity: 0.5;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        border-color: var(--border-glow) !important;
        box-shadow: 0 8px 40px rgba(100, 80, 255, 0.08);
    }
    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }

    /* ===== Empty State ===== */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        background: var(--bg-card);
        border: 1px dashed rgba(100, 100, 255, 0.10);
        border-radius: var(--radius-xl);
        color: var(--text-secondary);
        backdrop-filter: blur(12px);
        animation: fade-up 0.6s ease-out;
    }
    .empty-state h3 {
        color: var(--text-primary);
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* ===== Buttons ===== */
    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #4338ca 0%, #7c3aed 50%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.2px;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(100, 60, 220, 0.30);
        position: relative;
        overflow: hidden;
    }
    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        box-shadow: 0 6px 32px rgba(100, 60, 220, 0.45) !important;
        transform: translateY(-1px) scale(1.015);
        filter: brightness(1.1);
    }
    .stButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active {
        transform: scale(0.98) !important;
        box-shadow: 0 2px 12px rgba(100, 60, 220, 0.25) !important;
    }
    /* Secondary / Download buttons */
    .stDownloadButton > button {
        background: rgba(80, 100, 255, 0.06) !important;
        color: #c4b5fd !important;
        border: 1px solid rgba(80, 100, 255, 0.14) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: none;
    }
    .stDownloadButton > button:hover {
        background: rgba(80, 100, 255, 0.14) !important;
        border-color: rgba(80, 100, 255, 0.30) !important;
        box-shadow: 0 4px 20px rgba(80, 100, 255, 0.10) !important;
    }

    /* ===== Inputs ===== */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stNumberInput > div > div > input,
    [data-baseweb="input"] input,
    [data-baseweb="input"] > div {
        background: rgba(10, 10, 32, 0.65) !important;
        border: 1px solid rgba(100, 100, 255, 0.10) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    }
    [data-baseweb="input"] {
        background: rgba(10, 10, 32, 0.65) !important;
        border-color: rgba(100, 100, 255, 0.10) !important;
        border-radius: var(--radius-md) !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus,
    .stNumberInput > div > div > input:focus,
    [data-baseweb="input"]:focus-within {
        border-color: var(--neon-purple) !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12), 0 0 24px rgba(139, 92, 246, 0.06) !important;
    }
    /* Number input stepper buttons */
    .stNumberInput button,
    [data-testid="stNumberInput"] button {
        background: rgba(80, 100, 255, 0.08) !important;
        border: 1px solid rgba(100, 100, 255, 0.12) !important;
        color: var(--text-primary) !important;
    }
    .stNumberInput button:hover,
    [data-testid="stNumberInput"] button:hover {
        background: rgba(80, 100, 255, 0.18) !important;
        border-color: rgba(100, 100, 255, 0.25) !important;
    }
    .stTextInput label, .stTextArea label, .stNumberInput label,
    .stSelectbox label, .stRadio label, .stSlider label, .stCheckbox label,
    [data-testid="stNumberInput"] label {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }


    /* Selectbox */
    [data-baseweb="select"] > div {
        background: rgba(10, 10, 32, 0.65) !important;
        border-color: rgba(100, 100, 255, 0.10) !important;
        border-radius: var(--radius-md) !important;
    }
    [data-baseweb="select"] > div:focus-within {
        border-color: var(--neon-purple) !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.12) !important;
    }
    /* Selected value text — make it clearly visible */
    [data-baseweb="select"] [data-testid="stMarkdownContainer"],
    [data-baseweb="select"] span,
    [data-baseweb="select"] .css-1dimb5e,
    [data-baseweb="select"] div[class*="ValueContainer"] > div,
    [data-baseweb="select"] [data-baseweb="tag"] > span,
    [data-baseweb="select"] > div > div > div > div,
    [data-baseweb="select"] > div > div > div,
    [data-baseweb="select"] > div div,
    .stSelectbox > div > div > div > div > div,
    .stSelectbox [data-baseweb="select"] * {
        color: #f0f0ff !important;
        -webkit-text-fill-color: #f0f0ff !important;
    }
    /* Selectbox dropdown arrow icon */
    [data-baseweb="select"] svg {
        fill: rgba(200, 200, 255, 0.6) !important;
        color: rgba(200, 200, 255, 0.6) !important;
    }
    /* Placeholder text in selectbox and inputs */
    [data-baseweb="select"] [data-baseweb="select-placeholder"],
    [data-baseweb="select"] div[aria-selected="false"],
    .stTextInput > div > div > input::placeholder,
    .stTextArea textarea::placeholder,
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="base-input"] input::placeholder {
        color: rgba(190, 190, 230, 0.6) !important;
        -webkit-text-fill-color: rgba(190, 190, 230, 0.6) !important;
        opacity: 1 !important;
    }
    /* Input text color */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    [data-baseweb="input"] input,
    [data-baseweb="base-input"] input {
        color: #f0f0ff !important;
        -webkit-text-fill-color: #f0f0ff !important;
    }


    /* Dropdown menu — dark background */
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] [data-baseweb="menu"],
    [data-baseweb="menu"],
    [data-baseweb="popover"] ul,
    ul[role="listbox"] {
        background: rgba(8, 8, 22, 0.97) !important;
        background-color: rgba(8, 8, 22, 0.97) !important;
        border: 1px solid rgba(100, 100, 255, 0.15) !important;
        border-radius: var(--radius-md) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6), 0 0 1px rgba(100, 80, 255, 0.2) !important;
    }
    /* Dropdown option items */
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] [role="option"],
    ul[role="listbox"] li,
    ul[role="listbox"] [role="option"],
    [data-baseweb="popover"] li {
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        background: transparent !important;
        transition: background 0.2s ease;
    }
    /* Dropdown option hover state */
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] [role="option"]:hover,
    ul[role="listbox"] li:hover,
    ul[role="listbox"] [role="option"]:hover,
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li[aria-selected="true"],
    ul[role="listbox"] [role="option"][aria-selected="true"] {
        background: rgba(80, 100, 255, 0.14) !important;
        color: #c4b5fd !important;
        -webkit-text-fill-color: #c4b5fd !important;
    }
    /* Highlighted / focused option */
    [data-baseweb="menu"] li[aria-selected="true"],
    [data-baseweb="menu"] [data-highlighted="true"],
    ul[role="listbox"] [data-highlighted="true"] {
        background: rgba(80, 100, 255, 0.12) !important;
    }


    /* Slider */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: var(--neon-purple) !important;
        box-shadow: 0 0 14px rgba(139, 92, 246, 0.45);
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
    }
    .stSlider [data-baseweb="slider"] > div > div:first-child {
        background: rgba(100, 100, 255, 0.12) !important;
    }
    .stSlider [data-baseweb="slider"] > div > div:first-child > div {
        background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple)) !important;
    }

    /* Checkbox */
    .stCheckbox [data-baseweb="checkbox"] {
        border-color: rgba(100, 100, 255, 0.2) !important;
    }

    /* ===== Expanders ===== */
    [data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    [data-testid="stExpander"] summary:hover {
        color: #c4b5fd !important;
    }

    /* ===== Forms ===== */
    [data-testid="stForm"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-lg) !important;
        padding: 2rem !important;
        backdrop-filter: blur(12px);
    }

    /* ===== Progress Bar ===== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple), var(--neon-magenta)) !important;
        border-radius: 4px;
    }
    .stProgress > div > div {
        background: rgba(100, 100, 255, 0.06) !important;
        border-radius: 4px;
    }

    /* ===== Alerts ===== */
    [data-testid="stAlert"] {
        border-radius: var(--radius-md) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ===== Dividers ===== */
    hr {
        border-color: rgba(100, 100, 255, 0.06) !important;
    }

    /* ===== Code blocks ===== */
    [data-testid="stCode"], .stCodeBlock {
        background: rgba(8, 8, 28, 0.65) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-sm) !important;
    }
    code {
        color: #c4b5fd !important;
    }

    /* ===== Video player ===== */
    video {
        border-radius: var(--radius-lg) !important;
        border: 1px solid var(--border-subtle);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.35);
    }

    /* ===== Spinner ===== */
    .stSpinner > div {
        border-top-color: var(--neon-purple) !important;
    }

    /* ===== Markdown links ===== */
    a {
        color: #818cf8 !important;
        text-decoration: none !important;
        transition: color 0.2s ease;
    }
    a:hover {
        color: #a78bfa !important;
        text-decoration: underline !important;
    }

    /* ===== Keyframe Animations ===== */
    @keyframes grid-scroll {
        from { transform: translate(0, 0); }
        to   { transform: translate(-55px, -55px); }
    }
    @keyframes orb-float {
        0%   { transform: translate(0, 0) scale(1); }
        33%  { transform: translate(40px, -60px) scale(1.08); }
        66%  { transform: translate(-30px, 40px) scale(0.92); }
        100% { transform: translate(0, 0) scale(1); }
    }
    @keyframes streak-fall {
        0%   { top: -200px; opacity: 0; }
        5%   { opacity: 0.6; }
        95%  { opacity: 0.6; }
        100% { top: calc(100vh + 200px); opacity: 0; }
    }
    @keyframes shimmer {
        0%, 100% { opacity: 0.4; }
        50%      { opacity: 1; }
    }
    @keyframes hero-drift {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50%      { transform: translateY(-6px) rotate(0.3deg); }
    }
    @keyframes stage-sweep {
        0%   { left: -100%; }
        100% { left: 100%; }
    }
    @keyframes dot-pulse {
        0%, 100% { opacity: 0.7; box-shadow: 0 0 6px currentColor; }
        50%      { opacity: 1;   box-shadow: 0 0 14px currentColor, 0 0 24px currentColor; }
    }
    @keyframes fade-up {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ===== Reduce Motion ===== */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01s !important;
            transition-duration: 0.01s !important;
        }
    }

    /* ===== Hide Streamlit Defaults ===== */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def inject_dynamic_background():
    """Inject animated neon grid with floating orbs and light streaks."""
    if not USER_SETTINGS.get("enable_transition_effects", True):
        return

    import random

    # Generate light streaks
    streaks_html = []
    for i in range(5):
        x = random.uniform(8, 92)
        h = random.randint(120, 280)
        dur = random.uniform(8, 16)
        delay = random.uniform(0, 12)
        colors = [
            "rgba(80, 100, 255, 0.22)",
            "rgba(140, 60, 220, 0.18)",
            "rgba(200, 50, 180, 0.15)",
            "rgba(100, 80, 255, 0.20)",
        ]
        hue = colors[i % len(colors)]
        streaks_html.append(
            f'<div class="streak" style="'
            f"left:{x}%;height:{h}px;"
            f"background:linear-gradient(to bottom, transparent, {hue}, transparent);"
            f'animation-duration:{dur}s;animation-delay:{delay}s;'
            f'"></div>'
        )

    st.markdown(f"""
    <div class="neon-grid-wrap">
        <div class="neon-grid-lines"></div>
        <div class="neon-color-wash"></div>
        <div class="glow-orb orb-blue"></div>
        <div class="glow-orb orb-purple"></div>
        <div class="glow-orb orb-magenta"></div>
        {"".join(streaks_html)}
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data Loading Utilities
# ---------------------------------------------------------------------------
def _load_history():
    """Load generations from MongoDB if enabled, otherwise fallback to local JSON."""
    try:
        from scripts.database import is_mongo_enabled, get_all_generations
        if is_mongo_enabled():
            projects = []
            db_gens = get_all_generations()
            for meta in db_gens:
                project_dir_str = meta.get("project_dir", "")
                if not project_dir_str:
                    continue
                folder = Path(project_dir_str)
                gen = meta.get("generation", {})
                projects.append({
                    "folder": folder,
                    "folder_name": folder.name,
                    "title": meta.get("script_title", "") or gen.get("topic", folder.name),
                    "topic": gen.get("topic", "Unknown"),
                    "timestamp": gen.get("timestamp", ""),
                    "duration": gen.get("duration", 0),
                    "status": gen.get("status", "unknown"),
                    "scene_count": meta.get("scene_count", 0),
                    "timing": gen.get("timing", {}),
                    "errors": gen.get("errors", []),
                    "youtube_meta": meta.get("youtube", {}),
                })
            return projects
    except ImportError:
        pass

    projects = []
    output_path = Path(USER_SETTINGS.get("output_folder", str(OUTPUT_DIR)))
    if not output_path.exists():
        return projects

    for folder in sorted(output_path.iterdir(), reverse=True):
        if not folder.is_dir() or not folder.name.startswith("video_"):
            continue
        meta_path = folder / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            gen = meta.get("generation", {})
            projects.append({
                "folder": folder,
                "folder_name": folder.name,
                "title": meta.get("script_title", "") or gen.get("topic", folder.name),
                "topic": gen.get("topic", "Unknown"),
                "timestamp": gen.get("timestamp", ""),
                "duration": gen.get("duration", 0),
                "status": gen.get("status", "unknown"),
                "scene_count": meta.get("scene_count", 0),
                "timing": gen.get("timing", {}),
                "errors": gen.get("errors", []),
                "youtube_meta": meta.get("youtube", {}),
            })
        except Exception:
            continue
    return projects

# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
def render_sidebar():
    """Sidebar: branding, navigation."""
    # Load and encode logo
    import base64
    logo_path = Path(__file__).parent / "assets" / "logo.png"
    logo_b64 = ""
    if logo_path.exists():
        with open(logo_path, "rb") as img_f:
            logo_b64 = base64.b64encode(img_f.read()).decode()

    with st.sidebar:
        if logo_b64:
            st.markdown(f"""
            <div class="sidebar-brand">
                <div class="logo-container">
                    <div class="logo-spinner"></div>
                    <div class="logo-glow"></div>
                    <img class="logo-img" src="data:image/png;base64,{logo_b64}" alt="MAiX-YT Studio Logo" />
                </div>
                <h2>MAiX-YT Studio</h2>
                <p class="brand-sub">AI Video Engine</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="sidebar-brand">
                <h2>MAiX-YT Studio</h2>
                <p class="brand-sub">AI Video Engine</p>
            </div>
            """, unsafe_allow_html=True)

        pages = {
            "🏠 Dashboard": "Dashboard",
            "🎬 Generate Video": "Generate Video",
            "💡 Idea Generator": "Idea Generator",
            "📜 Generation History": "Generation History",
            "🔄 n8n Workflow": "n8n Workflow",
            "🔑 API Status": "API Status",
            "⚙️ Settings": "Settings",
            "ℹ️ About": "About"
        }

        page = st.radio(
            "Navigation",
            options=list(pages.keys()),
            label_visibility="collapsed",
            key="nav_radio"
        )

        # System Status indicator
        st.markdown("""
        <div style="margin-top:1.5rem;padding:0.75rem 1rem;border-radius:var(--radius-md);
                    background:rgba(12, 12, 35, 0.5);border:1px solid rgba(74,222,128,0.1);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="display:inline-block;width:7px;height:7px;border-radius:50%;
                            background:var(--success);box-shadow:0 0 8px rgba(74,222,128,0.5);
                            animation:pulse-dot 2s ease-in-out infinite;"></span>
                <span style="color:var(--success);font-weight:600;font-size:0.78rem;">System Online</span>
            </div>
            <div style="color:var(--text-secondary);font-size:0.68rem;">All services operational</div>
        </div>
        """, unsafe_allow_html=True)
        
        if "clerk_user_id" in st.session_state:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚪 Sign Out", use_container_width=True):
                del st.session_state["clerk_user_id"]
                st.rerun()

        st.caption("v3.0 — MAiX-YT Studio")
    return pages[page]


# ---------------------------------------------------------------------------
# Page: Dashboard
# ---------------------------------------------------------------------------
def page_dashboard():
    """Render a rich, information-dense dashboard."""
    st.markdown("""
    <div class="hero-header">
        <h1>Dashboard</h1>
        <p>MAiX-YT Studio — Command Center</p>
    </div>
    """, unsafe_allow_html=True)

    projects = _load_history()

    total_videos = len(projects)
    total_topics = len(set([p["topic"] for p in projects]))

    today = datetime.now().strftime("%Y%m%d")
    today_generations = sum(1 for p in projects if p["timestamp"].startswith(today))

    avg_time = 0.0
    if projects:
        total_time = sum(sum(p.get("timing", {}).values()) for p in projects)
        avg_time = total_time / total_videos

    successful = sum(1 for p in projects if p.get("status") == "success")
    success_rate = (successful / total_videos * 100) if total_videos > 0 else 0

    # --- Metrics Row ---
    st.markdown('<div class="section-title">📊 System Metrics</div>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""<div class="glass-card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:2rem;">🎬</div>
            <div style="font-size:1.8rem;font-weight:800;color:var(--text-primary);">{total_videos}</div>
            <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">Total Videos</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="glass-card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:2rem;">📝</div>
            <div style="font-size:1.8rem;font-weight:800;color:var(--text-primary);">{total_topics}</div>
            <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">Unique Topics</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="glass-card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:2rem;">⚡</div>
            <div style="font-size:1.8rem;font-weight:800;color:var(--text-primary);">{today_generations}</div>
            <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">Today</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""<div class="glass-card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:2rem;">⏱️</div>
            <div style="font-size:1.8rem;font-weight:800;color:var(--text-primary);">{avg_time:.0f}s</div>
            <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">Avg Time</div>
        </div>""", unsafe_allow_html=True)
    with m5:
        st.markdown(f"""<div class="glass-card" style="text-align:center;padding:1.2rem;">
            <div style="font-size:2rem;">✅</div>
            <div style="font-size:1.8rem;font-weight:800;color:var(--text-primary);">{success_rate:.0f}%</div>
            <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">Success Rate</div>
        </div>""", unsafe_allow_html=True)

    # --- Main Content: two columns ---
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # Quick Generate
        st.markdown('<div class="section-title">🚀 Quick Generate</div>', unsafe_allow_html=True)
        qg_topic = st.text_input("Quick topic", placeholder="Enter a topic and hit Generate...", label_visibility="collapsed", key="dash_quick_topic")

        qc1, qc2, qc3, qc4, qc5 = st.columns(5)
        with qc1:
            qg_dur = st.selectbox("Duration", ["30s (Short)", "60s (Medium)", "180s (Extended)"], index=1, label_visibility="collapsed", key="dash_qg_dur")
        with qc2:
            qg_lang = st.selectbox("Language", ["English", "Hindi", "Gujarati"], index=0, label_visibility="collapsed", key="dash_qg_lang")
        with qc3:
            qg_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16"], index=0, label_visibility="collapsed", key="dash_qg_ratio")
        with qc4:
            qg_tone = st.selectbox("Tone", ["Neutral", "Friendly", "Serious", "Conversational", "Energetic", "Inspirational", "Dramatic", "Authoritative"], label_visibility="collapsed", key="dash_qg_tone")
        with qc5:
            qg_style = st.selectbox("Style", ["Documentary", "Educational Explainer", "Storytelling", "News", "Cinematic", "Entertainment", "Listicle", "Case Study"], label_visibility="collapsed", key="dash_qg_style")

        # Dynamic trending topic pills (fetched from Gemini, cached in session)
        if "dash_trending_topics" not in st.session_state:
            try:
                st.session_state["dash_trending_topics"] = discover_trends("general")[:6]
            except Exception:
                st.session_state["dash_trending_topics"] = [
                    "AI Trends 2026", "Future of Work", "Space Exploration",
                    "Electric Vehicles", "Quantum Computing",
                ]
        trending_icons = ["🔥", "🌍", "🚀", "⚡", "🧠", "💡", "🎯", "🌐", "📊", "🔬"]
        trending_pills = "".join(
            f'<span class="tag-pill">{trending_icons[i % len(trending_icons)]} {t}</span>'
            for i, t in enumerate(st.session_state["dash_trending_topics"])
        )
        st.markdown(f'<div style="margin:8px 0 4px;">{trending_pills}</div>', unsafe_allow_html=True)

        if st.button("🎬  Generate Video", type="primary", use_container_width=True, key="dash_gen_btn", disabled=not qg_topic):
            dur_map = {"30s (Short)": 30, "60s (Medium)": 60, "180s (Extended)": 180}
            qg_duration = dur_map.get(qg_dur, 60)
            st.markdown("---")
            result = _run_direct_with_progress(qg_topic, qg_tone, qg_duration, style=qg_style, language=qg_lang.lower(), aspect_ratio=qg_ratio)
            st.session_state["last_result"] = result
            _render_results(result)


        # Recent Activity Timeline
        st.markdown('<div class="section-title">📜 Recent Activity</div>', unsafe_allow_html=True)

        if not projects:
            st.markdown("""
            <div class="empty-state" style="padding:2rem;">
                <h3>No videos generated yet</h3>
                <p>Use Quick Generate above or go to <strong>Generate Video</strong> to create your first video!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for proj in projects[:5]:
                status = proj.get("status", "unknown")
                if status == "success":
                    badge_cls = "badge-success"
                    status_label = "SUCCESS"
                elif status == "partial":
                    badge_cls = "badge-partial"
                    status_label = "PARTIAL"
                else:
                    badge_cls = "badge-error"
                    status_label = status.upper()

                ts = proj.get("timestamp", "")
                display_time = ""
                if ts:
                    try:
                        from datetime import datetime as dt_cls
                        parsed = dt_cls.strptime(ts[:15], "%Y%m%d_%H%M%S")
                        display_time = parsed.strftime("%b %d, %H:%M")
                    except Exception:
                        display_time = ts[:15]

                timing = proj.get("timing", {})
                total_t = sum(timing.values())
                scenes = proj.get("scene_count", 0)

                st.markdown(f"""
                <div class="history-card" style="padding:1rem 1.3rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div class="history-title" style="margin-bottom:3px;">{proj['title'][:60]}</div>
                            <div class="history-meta">
                                🕐 {display_time} &nbsp;·&nbsp; ⏱ {total_t:.0f}s &nbsp;·&nbsp; 🎞 {scenes} scenes &nbsp;·&nbsp; 📏 {proj['duration']}s
                            </div>
                        </div>
                        <span class="status-badge {badge_cls}">{status_label}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with right_col:
        # API Status Panel
        st.markdown('<div class="section-title">🔌 API Status</div>', unsafe_allow_html=True)

        try:
            from scripts.api_status import check_all_apis
            statuses = check_all_apis()
        except Exception:
            statuses = {}

        api_icons = {
            "Gemini": "🤖",
            "Pexels": "📷",
            "Pixabay": "🖼️",
            "ElevenLabs": "🎙️",
            "FFmpeg": "🎥",
        }

        for name, info in statuses.items():
            status = info["status"]
            msg = info["message"]
            if status == "connected":
                dot_cls = "dot-green"
                row_cls = "api-ok"
            elif status == "missing_key":
                dot_cls = "dot-yellow"
                row_cls = "api-warn"
            else:
                dot_cls = "dot-red"
                row_cls = "api-err"

            icon = api_icons.get(name, "⚙️")
            st.markdown(f"""
            <div class="api-status-row {row_cls}">
                <span style="font-size:1.2rem;">{icon}</span>
                <div style="flex:1;">
                    <div style="font-weight:600;font-size:0.85rem;">{name}</div>
                    <div style="font-size:0.72rem;opacity:0.8;">{msg}</div>
                </div>
                <span class="api-dot {dot_cls}"></span>
            </div>
            """, unsafe_allow_html=True)

        # System Info
        st.markdown('<div class="section-title" style="margin-top:1.5rem;">⚙️ System</div>', unsafe_allow_html=True)

        output_dir = Path(USER_SETTINGS.get("output_folder", str(OUTPUT_DIR)))
        output_count = 0
        output_size = 0
        if output_dir.exists():
            for f in output_dir.rglob("*"):
                if f.is_file():
                    output_count += 1
                    output_size += f.stat().st_size

        size_mb = output_size / (1024 * 1024) if output_size > 0 else 0

        st.markdown(f"""
        <div class="glass-card" style="padding:1rem 1.2rem;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:var(--text-secondary);font-size:0.8rem;">Output Files</span>
                <span style="color:var(--text-primary);font-weight:600;font-size:0.85rem;">{output_count}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:var(--text-secondary);font-size:0.8rem;">Disk Usage</span>
                <span style="color:var(--text-primary);font-weight:600;font-size:0.85rem;">{size_mb:.1f} MB</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:var(--text-secondary);font-size:0.8rem;">Voice Engine</span>
                <span style="color:var(--text-primary);font-weight:600;font-size:0.85rem;">{USER_SETTINGS.get('default_voice', 'Edge-TTS')}</span>
            </div>
            <div style="display:flex;justify-content:space-between;">
                <span style="color:var(--text-secondary);font-size:0.8rem;">Default Style</span>
                <span style="color:var(--text-primary);font-weight:600;font-size:0.85rem;">{USER_SETTINGS.get('default_style', 'Documentary')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick Actions
        st.markdown('<div class="section-title" style="margin-top:1.5rem;">🎯 Quick Actions</div>', unsafe_allow_html=True)

        if st.button("📂  Open Output Folder", use_container_width=True, key="dash_open_output"):
            import subprocess as _sp
            try:
                _sp.Popen(["explorer", str(output_dir)])
            except Exception:
                st.info(f"Output folder: `{output_dir}`")

        if st.button("🔄  Refresh API Status", use_container_width=True, key="dash_refresh_api"):
            st.rerun()


# ---------------------------------------------------------------------------
# Page: Generate Video
# ---------------------------------------------------------------------------
def page_generate():

    """Main video generation page."""
    st.markdown("""
    <div class="hero-header">
        <h1>Generate Video</h1>
        <p>Create complete YouTube videos from a single topic</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Configuration ---
    st.markdown('<div class="section-title">Video Configuration</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Topic**")
        topic = st.text_input(
            "Enter your video topic",
            placeholder="e.g., How AI is Changing Education in 2026",
            label_visibility="collapsed",
        )
        
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            st.markdown("**Voice Engine**")
            voice_engine = st.selectbox(
                "Voice Engine", 
                ["Edge-TTS (Neural)", "gTTS (Standard)", "ElevenLabs (Premium)"],
                index=["Edge-TTS (Neural)", "gTTS (Standard)", "ElevenLabs (Premium)"].index(USER_SETTINGS.get("default_voice", "Edge-TTS (Neural)")) if USER_SETTINGS.get("default_voice") in ["Edge-TTS (Neural)", "gTTS (Standard)", "ElevenLabs (Premium)"] else 0,
                label_visibility="collapsed"
            )
        with c_v2:
            st.markdown("**Voice Gender**")
            gender_option = st.radio(
                "Voice Gender",
                ["Female 👩", "Male 👨"],
                index=0 if USER_SETTINGS.get("default_voice_gender", "female") == "female" else 1,
                horizontal=True,
                label_visibility="collapsed"
            )
            voice_gender = "female" if "Female" in gender_option else "male"
        
        st.markdown("**Style Selection**")
        style_opts = ["Documentary", "Educational Explainer", "Storytelling", "News", "Cinematic", "Entertainment", "Listicle", "Case Study"]
        def_style_val = USER_SETTINGS.get("default_style", "Documentary")
        style_def_idx = style_opts.index(def_style_val) if def_style_val in style_opts else 0
        style = st.selectbox(
            "Style", 
            style_opts,
            index=style_def_idx,
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("**Tone**")
        tones = ["Neutral", "Friendly", "Serious", "Conversational", "Energetic", "Inspirational", "Dramatic", "Authoritative"]
        default_tone = USER_SETTINGS.get("default_tone", "Neutral")
        tone = st.selectbox("Tone", tones, index=tones.index(default_tone) if default_tone in tones else 0, label_visibility="collapsed")
        
        st.markdown("**Duration Preset**")
        dur_presets = [
            "⚡ Min (Shorts / 30s)",
            "🎬 Medium (Standard / 60s)",
            "🔥 Max (Extended / 180s)"
        ]
        def_preset_key = USER_SETTINGS.get("default_duration_preset", "medium")
        def_idx = 1 if def_preset_key == "medium" else (0 if def_preset_key == "min" else 2)

        duration_preset = st.selectbox(
            "Duration Preset",
            options=dur_presets,
            index=def_idx,
            label_visibility="collapsed"
        )

        st.markdown("**Language & Aspect Ratio**")
        col_L1, col_L2 = st.columns(2)
        with col_L1:
            language = st.selectbox("Language", ["English", "Hindi", "Gujarati"], index=0, label_visibility="collapsed")
        with col_L2:
            aspect_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16"], index=0, label_visibility="collapsed")

        if "Min" in duration_preset:
            preset_key = "min"
        elif "Max" in duration_preset:
            preset_key = "max"
        else:
            preset_key = "medium"

        preset_info = get_duration_preset(preset_key)
        duration = preset_info["seconds"]
        scene_count = preset_info["scenes"]

    # Trending topics
    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_trends(niche_str):
        return discover_trends(niche_str)

    with st.expander("Browse trending topics"):
        niche_cols = st.columns(4)
        niches = ["technology", "science", "education", "general"]
        for i, niche in enumerate(niches):
            with niche_cols[i]:
                st.markdown(f"**{niche.title()}**")
                topics = cached_trends(niche)
                for t in topics[:3]:
                    if st.button(t, key=f"trend_{niche}_{t[:20]}", use_container_width=True):
                        st.session_state["selected_topic"] = t

    if "selected_topic" in st.session_state and not topic:
        topic = st.session_state["selected_topic"]
        st.info(f"Selected topic: **{topic}**")

    st.caption(
        f"⚡ Selected Preset: **{preset_info['label']}** "
        f"({duration}s video, {scene_count} scenes, ~{preset_info['min_words']}–{preset_info['max_words']} narration words, {voice_gender.title()} voice)."
    )

    # --- Generate ---
    st.markdown("---")
    
    st.markdown("**Execution Mode**")
    exec_mode = st.radio(
        "How do you want to generate the video?",
        ["Direct (Python)", "n8n Workflow"],
        index=1 if USER_SETTINGS.get("enable_n8n", False) else 0,
        horizontal=True,
        label_visibility="collapsed"
    )
    use_n8n = (exec_mode == "n8n Workflow")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_clicked = st.button(
            "Generate Video",
            type="primary",
            use_container_width=True,
            disabled=not topic,
        )

    if not topic and generate_clicked:
        st.warning("Please enter a topic first!")
        return

    if generate_clicked and topic:
        st.markdown("---")
        if use_n8n:
            result = _run_n8n_pipeline(topic, tone, duration, voice_engine, voice_gender, style, language.lower(), aspect_ratio)
        else:
            result = _run_direct_with_progress(topic, tone, duration, voice_gender, voice_engine, style, language.lower(), aspect_ratio)
        st.session_state["last_result"] = result
        _render_results(result)
    elif "last_result" in st.session_state:
        _render_results(st.session_state["last_result"])

def _run_direct_with_progress(topic: str, tone: str, duration: int, voice_gender: str = "female", voice_engine: str = "Edge-TTS (Neural)", style: str = "Documentary", language: str = "english", aspect_ratio: str = "16:9"):
    """Run pipeline with animated stage-by-stage progress."""
    stages = [
        ("Script Generation", "script_generation"),
        ("Voice Generation", "voice_generation"),
        ("Visual Collection", "visual_collection"),
        ("Video Rendering", "video_assembly"),
        ("Metadata Generation", "metadata_generation"),
    ]

    stage_placeholder = st.empty()
    current_step = {"value": 0}

    def render_stages(active_step):
        html = []
        for i, (label, _) in enumerate(stages):
            idx = i + 1
            if idx < active_step:
                cls, icon = "stage-done", "&#10004;"
            elif idx == active_step:
                cls, icon = "stage-active", "&#9881;"
            else:
                cls, icon = "stage-pending", "&#9711;"
            html.append(
                f'<div class="progress-stage {cls}">'
                f'<span class="stage-icon">{icon}</span>'
                f"<span>{label}</span></div>"
            )
        if active_step > len(stages):
            html.append(
                '<div class="progress-stage stage-done">'
                '<span class="stage-icon">&#10004;</span>'
                "<span><strong>Pipeline Complete</strong></span></div>"
            )
        stage_placeholder.markdown("\n".join(html), unsafe_allow_html=True)

    progress_bar = st.progress(0, text="Starting pipeline...")

    def progress_callback(step, total, message):
        current_step["value"] = step
        render_stages(step)
        progress_fraction = min(max(step / total, 0.0), 1.0)
        progress_bar.progress(progress_fraction, text=message)

    render_stages(0)

    import importlib
    import scripts.visual_generator
    import scripts.video_generator
    import scripts.pipeline
    importlib.reload(scripts.visual_generator)
    importlib.reload(scripts.video_generator)
    importlib.reload(scripts.pipeline)
    from scripts.pipeline import run_pipeline

    result = run_pipeline(
        topic=topic, tone=tone, duration=duration,
        voice_gender=voice_gender, voice_engine=voice_engine,
        style=style, language=language, aspect_ratio=aspect_ratio, progress_callback=progress_callback,
    )



    if result.get("status") == "error":
        progress_bar.progress(1.0, text="Pipeline failed")
    else:
        render_stages(6)
        progress_bar.progress(1.0, text="Complete!")

    return result

def _run_n8n_pipeline(topic: str, tone: str, duration: int, voice: str = "Edge-TTS (Neural)", voice_gender: str = "female", style: str = "Documentary", language: str = "english", aspect_ratio: str = "16:9"):
    """Trigger n8n workflow with all generation parameters."""
    st.info("Triggering n8n workflow...")
    try:
        webhook_url = get_n8n_webhook_url()
        payload = {
            "topic": topic,
            "tone": tone,
            "duration": duration,
            "voice": voice,
            "voice_gender": voice_gender,
            "style": style,
            "language": language,
            "aspect_ratio": aspect_ratio,
            "project_path": str(Path(__file__).resolve().parent),
        }
        st.caption(f"📤 Sending to n8n: topic=`{topic}`, tone=`{tone}`, duration=`{duration}s`, voice=`{voice}`, gender=`{voice_gender}`, style=`{style}`, language=`{language}`, ratio=`{aspect_ratio}`")
        response = requests.post(webhook_url, json=payload, timeout=300)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"n8n returned HTTP {response.status_code}: {response.text[:300]}")
            return {"status": "error", "error": f"HTTP {response.status_code}"}
    except requests.ConnectionError:
        st.error("❌ Cannot connect to n8n. Make sure n8n is running on port 5678.")

        return {"status": "error", "error": "n8n connection failed"}
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return {"status": "error", "error": str(e)}

def _render_results(result: dict):
    """Display results with premium styling."""
    status = result.get("status", "error")

    if status == "error":
        st.error(f"Pipeline failed: {result.get('error', 'Unknown error')}")
        errors = result.get("errors", [])
        if errors:
            with st.expander("Error Details"):
                for err in errors:
                    st.markdown(f"- {err}")
        return

    if status == "partial":
        st.warning("Video generated with some warnings. Check details below.")
    else:
        st.success("Video generated successfully!")

    st.markdown('<div class="section-title">Results</div>', unsafe_allow_html=True)
    
    aspect_ratio = result.get("aspect_ratio", "16:9")
    if aspect_ratio == "9:16":
        video_col, meta_col, _ = st.columns([1.5, 2.5, 1])
    else:
        video_col, meta_col = st.columns([3, 2])
        
    with video_col:
        video_path = result.get("video_path", "")
        if video_path and Path(video_path).is_file():
            st.video(video_path)
            with open(video_path, "rb") as f:
                st.download_button(
                    label="Download Video",
                    data=f.read(),
                    file_name=Path(video_path).name,
                    mime="video/mp4",
                    use_container_width=True,
                )
        else:
            st.warning("Video file not available.")


    with meta_col:
        st.markdown("**YouTube Metadata**")
        metadata = result.get("metadata", {})
        if metadata:
            st.markdown(f"**Title:** {metadata.get('title', 'N/A')}")
            st.text_area(
                "Description", value=metadata.get("description", ""),
                height=150, disabled=True, label_visibility="collapsed",
            )
            tags = metadata.get("tags", [])
            if tags:
                tag_html = "".join(f'<span class="tag-pill">{t}</span>' for t in tags)
                st.markdown(tag_html, unsafe_allow_html=True)

    timing = result.get("timing", {})
    if timing:
        st.markdown('<div class="section-title">Performance</div>', unsafe_allow_html=True)
        cols = st.columns(len(timing))
        labels = {
            "script_generation": "Script", "voice_generation": "Voice",
            "visual_collection": "Visuals", "video_assembly": "Video",
            "metadata_generation": "Metadata",
        }
        for i, (step, secs) in enumerate(timing.items()):
            with cols[i]:
                st.metric(label=labels.get(step, step), value=f"{secs:.1f}s")

    errors = result.get("errors", [])
    if errors:
        with st.expander("Warnings & Errors"):
            for err in errors:
                st.markdown(f"- {err}")

    script = result.get("script", {})
    if script:
        with st.expander("View Full Script"):
            for scene in script.get("scenes", []):
                scene_type = scene.get("scene_type", "")
                badge = ""
                if scene_type:
                    cmap = {
                        "hook": ("#f59e0b", "#f59e0b20"),
                        "introduction": ("#3b82f6", "#3b82f620"),
                        "main_content": ("#8b5cf6", "#8b5cf620"),
                        "conclusion": ("#10b981", "#10b98120"),
                        "cta": ("#ef4444", "#ef444420"),
                    }
                    c, bg = cmap.get(scene_type, ("#6b7280", "#6b728020"))
                    badge = (
                        f' <span class="scene-badge" style="color:{c};background:{bg};'
                        f'border:1px solid {c}30;">{scene_type.replace("_"," ")}</span>'
                    )
                st.markdown(
                    f"**Scene {scene['scene_number']}** "
                    f"({scene.get('duration_seconds', '?')}s){badge}",
                    unsafe_allow_html=True,
                )
                st.markdown(f"> {scene['narration']}")
                st.caption(f"Visual: {scene.get('visual_prompt', '')}")
                st.markdown("---")

    project_dir = result.get("project_dir", "")
    if project_dir:
        st.caption(f"Project folder: `{project_dir}`")


# ---------------------------------------------------------------------------
# Page: Generation History
# ---------------------------------------------------------------------------
def page_history():
    """Generation history with preview, download, script view, delete."""
    st.markdown("""
    <div class="hero-header">
        <h1>Generation History</h1>
        <p>Browse, preview, and manage your previously generated videos</p>
    </div>
    """, unsafe_allow_html=True)

    projects = _load_history()
    if not projects:
        st.markdown("""
        <div class="empty-state">
            <h3>No Videos Yet</h3>
            <p>You haven't generated any videos. Head over to <b>Generate Video</b> to start!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"**{len(projects)} video(s) found**")

    for i, proj in enumerate(projects):
        folder: Path = proj["folder"]
        video_path = folder / "final_video.mp4"
        script_path = folder / "script.md"

        status = proj["status"]
        badge_cls = {"success": "badge-success", "partial": "badge-partial"}.get(status, "badge-error")

        ts = proj["timestamp"]
        try:
            dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
            time_str = dt.strftime("%b %d, %Y at %I:%M %p")
        except Exception:
            time_str = ts

        total_time = sum(proj.get("timing", {}).values())

        st.markdown(
            f"""<div class="history-card">
                <div class="history-title">{proj['title']}</div>
                <div class="history-meta">
                    Topic: {proj['topic']} &nbsp;&bull;&nbsp;
                    Duration: {proj['duration']}s &nbsp;&bull;&nbsp;
                    Scenes: {proj['scene_count']} &nbsp;&bull;&nbsp;
                    {time_str} &nbsp;&bull;&nbsp;
                    {total_time:.1f}s
                    &nbsp;&nbsp;
                    <span class="status-badge {badge_cls}">{status.upper()}</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        cols = st.columns([1, 1, 1, 1, 1, 1, 1])

        with cols[0]:
            if video_path.exists():
                if st.button("Preview", key=f"prev_{i}", use_container_width=True):
                    st.session_state[f"sp_{i}"] = not st.session_state.get(f"sp_{i}", False)

        with cols[1]:
            if video_path.exists():
                with open(video_path, "rb") as f:
                    st.download_button(
                        "Download", data=f.read(),
                        file_name=f"{proj['folder_name']}.mp4", mime="video/mp4",
                        key=f"dl_{i}", use_container_width=True,
                    )

        with cols[2]:
            if st.button("Open Folder", key=f"fold_{i}", use_container_width=True):
                # Only works if local, a bit of a hack for Streamlit
                import subprocess, platform
                if platform.system() == "Windows":
                    os.startfile(str(folder))
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", str(folder)])
                else:
                    subprocess.Popen(["xdg-open", str(folder)])

        with cols[3]:
            if script_path.exists():
                if st.button("Script", key=f"scr_{i}", use_container_width=True):
                    st.session_state[f"ss_{i}"] = not st.session_state.get(f"ss_{i}", False)

        with cols[4]:
            if st.button("Metadata", key=f"mt_{i}", use_container_width=True):
                st.session_state[f"sm_{i}"] = not st.session_state.get(f"sm_{i}", False)

        with cols[5]:
            if st.button("Delete", key=f"del_{i}", use_container_width=True, type="secondary"):
                st.session_state[f"cd_{i}"] = True

        # Expanded content
        if st.session_state.get(f"sp_{i}", False) and video_path.exists():
            st.video(str(video_path))

        if st.session_state.get(f"ss_{i}", False) and script_path.exists():
            with open(script_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())

        if st.session_state.get(f"sm_{i}", False):
            yt = proj.get("youtube_meta", {})
            if yt:
                st.markdown(f"**Title:** {yt.get('title', 'N/A')}")
                st.text_area("Desc", value=yt.get("description", ""), height=100, disabled=True, key=f"d_{i}")
                tags = yt.get("tags", [])
                if tags:
                    st.markdown(f"**Tags:** {', '.join(tags)}")

        if st.session_state.get(f"cd_{i}", False):
            st.warning(f"Delete **{proj['title']}** and all files?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete", key=f"yd_{i}", type="primary"):
                    try:
                        shutil.rmtree(str(folder))
                        st.success("Deleted.")
                        st.session_state[f"cd_{i}"] = False
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            with c2:
                if st.button("Cancel", key=f"nd_{i}"):
                    st.session_state[f"cd_{i}"] = False
                    st.rerun()
        st.markdown("")


# ---------------------------------------------------------------------------
# Page: n8n Workflow
# ---------------------------------------------------------------------------
def page_n8n():
    """n8n Automation page."""
    st.markdown("""
    <div class="hero-header">
        <h1>n8n Workflow</h1>
        <p>Manage and monitor the automation engine</p>
    </div>
    """, unsafe_allow_html=True)

    enabled = USER_SETTINGS.get("enable_n8n", False)
    st.markdown('<div class="section-title">Workflow Status</div>', unsafe_allow_html=True)

    if enabled:
        st.success("✅ n8n is ENABLED in Settings. The app will dispatch generation requests to n8n.")
        st.code(f"Webhook URL: {get_n8n_webhook_url()}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Test Webhook Connection", use_container_width=True):
                try:
                    res = requests.post(get_n8n_webhook_url(), json={"test": True}, timeout=5)
                    if res.status_code == 200:
                        st.success("✅ Webhook is ACTIVE and responding! (HTTP 200)")
                    elif res.status_code == 404:
                        st.error(
                            "❌ HTTP 404 — Workflow NOT found in n8n.\n\n"
                            "n8n is running but the workflow is not imported or not activated. "
                            "Follow the setup guide below."
                        )
                    elif res.status_code == 503:
                        st.warning("⚠️ HTTP 503 — Workflow exists but is not ACTIVE. Go to n8n and turn on the Activate toggle.")
                    else:
                        st.warning(f"⚠️ HTTP {res.status_code} — Unexpected response. Body: {res.text[:300]}")
                except requests.ConnectionError:
                    st.error("❌ Cannot reach n8n. Make sure n8n is running on port 5678.")
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")
        with c2:
            if st.button("Open n8n UI", use_container_width=True):
                st.markdown("**[→ Click here to open n8n UI](http://localhost:5678)**", unsafe_allow_html=False)

        st.markdown("---")
        workflow_path = str(Path(__file__).resolve().parent / "n8n" / "workflow.json")
        st.markdown("### 📋 Workflow Setup Guide")
        st.info(
            "If you're getting **HTTP 404**, the workflow is not imported or not activated in n8n. "
            "Follow these steps:"
        )
        st.markdown(
            f"""
**Step 1.** Open [http://localhost:5678](http://localhost:5678) in your browser

**Step 2.** Click **Workflows** → **Import from file**

**Step 3.** Select this file from your project:
```
{workflow_path}
```

**Step 4.** Once imported, click the **Activate** toggle in the top-right corner to turn it **ON**

**Step 5.** Come back here and click **Test Webhook Connection** — you should now get ✅ HTTP 200
"""
        )
        st.warning(
            "⚡ The workflow must be **ACTIVE** (not just imported). "
            "The green toggle in n8n must be switched ON or the webhook returns 404."
        )
    else:
        st.warning("⚠️ n8n is DISABLED. The app is running in Direct Python mode.")
        st.info("To enable n8n workflow dispatch, go to **Settings** and enable 'n8n Workflow Dispatch'.")


# ---------------------------------------------------------------------------
# Page: API Status
# ---------------------------------------------------------------------------
def page_api_status():
    """Full API status dashboard."""
    st.markdown("""
    <div class="hero-header">
        <h1>API Dashboard</h1>
        <p>Real-time connectivity checks for all integrated services</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Connectivity Status</div>', unsafe_allow_html=True)

    from scripts.api_status import check_all_apis
    with st.spinner("Checking API statuses..."):
        statuses = check_all_apis()
        
    for name, info in statuses.items():
        status = info["status"]
        message = info["message"]
        if status == "connected":
            icon, color = "🟢", "#4ade80"
        elif status == "missing_key":
            icon, color = "🟡", "#fbbf24"
        else:
            icon, color = "🔴", "#f87171"

        st.markdown(
            f"""<div class="glass-card" style="display:flex;align-items:center;gap:14px;padding:1rem 1.3rem;">
                <span style="font-size:1.5rem;">{icon}</span>
                <div>
                    <div style="color:#e2e8f0;font-weight:700;">{name}</div>
                    <div style="color:{color};font-size:0.85rem;">{message}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    if st.button("Refresh API Status", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# Page: Settings
# ---------------------------------------------------------------------------
def page_settings():
    """Settings page."""
    st.markdown("""
    <div class="hero-header">
        <h1>Settings</h1>
        <p>Configure default behaviors and preferences</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("### Defaults")
        def_preset_opts = ["min", "medium", "max"]
        def_preset_key = USER_SETTINGS.get("default_duration_preset", "medium")
        def_preset = st.selectbox(
            "Default Duration Preset",
            ["Min (30s)", "Medium (60s)", "Max (180s)"],
            index=1 if def_preset_key == "medium" else (0 if def_preset_key == "min" else 2)
        )
        def_gender = st.selectbox(
            "Default Voice Gender",
            ["female", "male"],
            index=0 if USER_SETTINGS.get("default_voice_gender", "female") == "female" else 1
        )
        def_tone = st.selectbox("Default Tone", ["educational", "entertaining", "motivational"], index=["educational", "entertaining", "motivational"].index(USER_SETTINGS.get("default_tone", "educational")))
        def_voice_opts = ["Edge-TTS (Neural)", "gTTS (Standard)", "ElevenLabs (Premium)"]
        curr_v = USER_SETTINGS.get("default_voice", "Edge-TTS (Neural)")
        def_voice = st.selectbox(
            "Default Voice Engine",
            def_voice_opts,
            index=def_voice_opts.index(curr_v) if curr_v in def_voice_opts else 0
        )
        style_opts_s = ["Documentary", "Educational", "Entertainment", "Motivational"]
        curr_style = USER_SETTINGS.get("default_style", "Documentary")
        def_style = st.selectbox(
            "Default Style",
            style_opts_s,
            index=style_opts_s.index(curr_style) if curr_style in style_opts_s else 0
        )
        
        st.markdown("### Video Effects & Audio")
        en_motion = st.checkbox("Enable Image Motion Effects (Ken Burns Zoom/Pan)", value=USER_SETTINGS.get("enable_motion_effects", True))
        en_trans = st.checkbox("Enable Crossfade Scene Transitions", value=USER_SETTINGS.get("enable_transition_effects", True))
        en_hl = st.checkbox("Enable On-Screen Text Highlights", value=USER_SETTINGS.get("enable_text_highlights", True))
        en_subs = st.checkbox("Enable Narration Subtitles", value=USER_SETTINGS.get("enable_subtitles", False))
        en_music = st.checkbox("Enable Background Music", value=USER_SETTINGS.get("enable_bg_music", True))
        bg_vol = st.slider("Background Music Volume", min_value=0.02, max_value=0.25, value=float(USER_SETTINGS.get("bg_music_volume", 0.10)), step=0.01)

        st.markdown("### Output")
        out_folder = st.text_input("Output Folder Path", value=USER_SETTINGS.get("output_folder", str(OUTPUT_DIR)))
        
        st.markdown("### Advanced")
        en_n8n = st.checkbox("Enable n8n Workflow Dispatch", value=USER_SETTINGS.get("enable_n8n", False))
        en_fx = st.checkbox("Enable UI Transition Effects (Particles, Animations)", value=USER_SETTINGS.get("enable_transition_effects", True))
        
        submitted = st.form_submit_button("Save Settings")
        if submitted:
            new_preset_key = "min" if "Min" in def_preset else ("max" if "Max" in def_preset else "medium")
            new_settings = {
                "default_duration_preset": new_preset_key,
                "default_duration": get_duration_preset(new_preset_key)["seconds"],
                "default_voice_gender": def_gender,
                "default_tone": def_tone,
                "default_voice": def_voice,
                "default_style": def_style,
                "output_folder": out_folder,
                "enable_n8n": en_n8n,
                "enable_transition_effects": en_fx,
                "enable_motion_effects": en_motion,
                "enable_text_highlights": en_hl,
                "enable_subtitles": en_subs,
                "enable_bg_music": en_music,
                "bg_music_volume": bg_vol,
            }
            SettingsManager.save(new_settings)
            st.success("Settings saved! Reloading...")

            time.sleep(1)
            st.rerun()


# ---------------------------------------------------------------------------
# Page: About
# ---------------------------------------------------------------------------
def page_about():
    """About page."""
    st.markdown("""
    <div class="hero-header">
        <h1>About</h1>
        <p>MAiX-YT Studio — AI Video Automation</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### MAiX-YT Studio

    A professional-grade AI automation platform that generates complete YouTube videos
    from a single topic using advanced models and multimedia APIs.

    ---

    **Version:** 3.0 (Premium)

    **Architecture & Tech Stack:**
    - **Frontend:** Streamlit
    - **Database:** MongoDB Atlas
    - **Authentication:** Clerk
    - **Workflow Orchestration:** n8n
    - **Language Model:** Google Gemini 2.5 Flash
    - **Voice Generation:** Edge-TTS / ElevenLabs / gTTS
    - **Visuals:** Pexels (ranked multi-query pipeline)
    - **Video Rendering:** FFmpeg (via Python)
    - **Languages:** English, Hindi, Gujarati

    **Pipeline Steps:**
    1. AI Script Generation (dynamic storytelling)
    2. Multi-Language Text-to-Speech Narration
    3. Smart Visual Asset Collection & Ranking
    4. Dynamic Video Assembly with Effects
    5. SEO Metadata Generation

    ---
    *Built by MAiX — AI Automation & Video Creation Workflows.*
    """)


# ---------------------------------------------------------------------------
# Page: Idea Generator (placeholder — full implementation in Phase 4)
# ---------------------------------------------------------------------------
def page_idea_generator():
    """AI-powered idea brainstorming page."""
    st.markdown("""
    <div class="hero-header">
        <h1>💡 Idea Generator</h1>
        <p>AI-Powered Video Topic Brainstorming</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Generate Video Ideas</div>', unsafe_allow_html=True)

    niche = st.text_input("Enter a niche or keyword", placeholder="e.g., AI, cooking, fitness, history...")

    if st.button("🧠 Generate Ideas", type="primary", use_container_width=True, disabled=not niche):
        with st.spinner("Brainstorming ideas with AI..."):
            try:
                st.session_state["generated_ideas"] = discover_trends(niche)[:10]
            except Exception:
                st.session_state["generated_ideas"] = [
                    f"{niche}: Complete Beginner's Guide",
                    f"Top 10 {niche} Tips for 2026",
                    f"Why {niche} is the Future",
                    f"{niche} vs Traditional Methods",
                    f"How to Master {niche} in 30 Days",
                ]

    if "generated_ideas" in st.session_state:
        st.markdown('<div class="section-title">💡 Generated Ideas</div>', unsafe_allow_html=True)

        for i, idea in enumerate(st.session_state["generated_ideas"]):
            st.markdown(f'<span style="color:var(--neon-purple);font-weight:700;font-size:0.9rem;">Idea {i+1}</span>', unsafe_allow_html=True)
            st.code(idea, language="text")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Main app with page routing."""
    inject_css()
    inject_dynamic_background()

    # Authentication Gate
    if "clerk_user_id" not in st.session_state:
        st.markdown("""
        <div class="hero-header">
            <h1>🔒 Authentication Required</h1>
            <p>Welcome to MAiX-YT Studio. Please sign in to continue.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card" style="max-width:500px; margin: 0 auto; text-align: center;">', unsafe_allow_html=True)
        token = st.text_input("Enter your Clerk Session Token (JWT)", type="password", placeholder="eyJhbGciOiJSUzI1NiIs...")
        
        if st.button("Verify & Sign In", type="primary", use_container_width=True):
            if not token:
                st.error("Please enter a token.")
            elif token == "dev":
                st.session_state["clerk_user_id"] = "dev_local_user"
                st.success("Developer mode authenticated!")
                st.rerun()
            else:
                from scripts.auth import verify_clerk_session
                payload = verify_clerk_session(token)
                if payload and "sub" in payload:
                    st.session_state["clerk_user_id"] = payload["sub"]
                    st.success("Successfully authenticated!")
                    st.rerun()
                else:
                    st.error("Invalid or expired session token.")
        
        from scripts.auth import get_hosted_sign_in_url
        sign_in_url = get_hosted_sign_in_url()
        st.markdown(f'<p style="margin-top:20px; font-size:0.85rem; color:var(--text-secondary);">Don\'t have a token? <a href="{sign_in_url}" target="_blank" style="color:var(--neon-blue);">Sign in via Clerk</a></p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.75rem; color:var(--text-secondary);">Tip: Type <b>dev</b> to bypass auth for local testing.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    page = render_sidebar()

    if page == "Dashboard":
        page_dashboard()
    elif page == "Generate Video":
        page_generate()
    elif page == "Idea Generator":
        page_idea_generator()
    elif page == "Generation History":
        page_history()
    elif page == "n8n Workflow":
        page_n8n()
    elif page == "API Status":
        page_api_status()
    elif page == "Settings":
        page_settings()
    elif page == "About":
        page_about()

if __name__ == "__main__":
    main()
