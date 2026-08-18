"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import Sidebar from "@/components/Sidebar";
import NeonBackground from "@/components/NeonBackground";
import GlassCard from "@/components/GlassCard";
import { getSettings, updateSettings, getDriveStatus, getDriveAuthUrl, disconnectDrive } from "@/lib/api";
import type { UserSettings } from "@/lib/types";

const DEFAULT_SETTINGS: UserSettings = {
  default_duration: 60,
  default_tone: "educational",
  default_voice: "Edge-TTS (Neural)",
  default_voice_gender: "female",
  default_style: "Documentary",
  enable_transition_effects: true,
  enable_motion_effects: true,
  enable_text_highlights: true,
  enable_subtitles: false,
  enable_bg_music: true,
  bg_music_volume: 0.1,
};

export default function SettingsPage() {
  const { getToken } = useAuth();
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  
  // Google Drive State
  const [driveStatus, setDriveStatus] = useState<any>(null);
  const [loadingDrive, setLoadingDrive] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const token = await getToken();
        if (!token) return;
        
        // Fetch settings
        const data = await getSettings(token);
        setSettings(data.settings);
        
        // Fetch drive status
        const driveData = await getDriveStatus(token);
        setDriveStatus(driveData);
      } catch (err) {
        console.error("Failed to fetch settings data:", err);
      } finally {
        setLoadingDrive(false);
      }
    }
    fetchData();
  }, [getToken]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const token = await getToken();
      if (!token) return;
      await updateSettings(settings, token);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("Failed to save settings:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleConnectDrive = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const res = await getDriveAuthUrl(token);
      if (res.auth_url) {
        window.location.href = res.auth_url;
      }
    } catch (err) {
      console.error("Failed to get drive auth url:", err);
      alert("Failed to start Google Drive connection.");
    }
  };

  const handleDisconnectDrive = async () => {
    try {
      setLoadingDrive(true);
      const token = await getToken();
      if (!token) return;
      await disconnectDrive(token);
      setDriveStatus({ ...driveStatus, connected: false });
    } catch (err) {
      console.error("Failed to disconnect drive:", err);
    } finally {
      setLoadingDrive(false);
    }
  };

  const updateField = <K extends keyof UserSettings>(key: K, value: UserSettings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <>
      <NeonBackground />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <div className="hero-header">
            <h1>Settings</h1>
            <p>Configure your default generation preferences</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            {/* Defaults */}
            <GlassCard>
              <h3>Generation Defaults</h3>

              <label className="input-label" style={{ marginTop: "1rem" }}>Default Duration</label>
              <select
                className="select-field"
                value={settings.default_duration}
                onChange={(e) => updateField("default_duration", Number(e.target.value))}
              >
                <option value={30}>30s (Short)</option>
                <option value={60}>60s (Medium)</option>
                <option value={180}>180s (Extended)</option>
              </select>

              <label className="input-label" style={{ marginTop: "1rem" }}>Default Tone</label>
              <input
                className="input-field"
                value={settings.default_tone}
                onChange={(e) => updateField("default_tone", e.target.value)}
              />

              <label className="input-label" style={{ marginTop: "1rem" }}>Default Style</label>
              <select
                className="select-field"
                value={settings.default_style}
                onChange={(e) => updateField("default_style", e.target.value)}
              >
                {["Documentary", "Educational Explainer", "Storytelling", "News", "Cinematic", "Entertainment", "Listicle", "Case Study"].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>

              <label className="input-label" style={{ marginTop: "1rem" }}>Default Voice Engine</label>
              <select
                className="select-field"
                value={settings.default_voice}
                onChange={(e) => updateField("default_voice", e.target.value)}
              >
                <option value="Edge-TTS (Neural)">Edge-TTS (Neural)</option>
                <option value="ElevenLabs (Premium)">ElevenLabs (Premium)</option>
                <option value="gTTS (Standard)">gTTS (Standard)</option>
              </select>
            </GlassCard>

            {/* Effects */}
            <GlassCard>
              <h3>Video Effects</h3>

              {([
                ["enable_transition_effects", "Transition Effects"],
                ["enable_motion_effects", "Motion Effects (Ken Burns)"],
                ["enable_text_highlights", "Text Highlights"],
                ["enable_subtitles", "Subtitles"],
                ["enable_bg_music", "Background Music"],
              ] as [keyof UserSettings, string][]).map(([key, label]) => (
                <label key={key} style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "10px 0",
                  borderBottom: "1px solid rgba(100, 100, 255, 0.06)",
                  cursor: "pointer",
                  color: "var(--text-primary)",
                  fontSize: "0.9rem",
                }}>
                  <input
                    type="checkbox"
                    checked={settings[key] as boolean}
                    onChange={(e) => updateField(key, e.target.checked as never)}
                    style={{ accentColor: "var(--neon-purple)" }}
                  />
                  {label}
                </label>
              ))}

              {settings.enable_bg_music && (
                <div style={{ marginTop: "1rem" }}>
                  <label className="input-label">
                    Music Volume: {(settings.bg_music_volume * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="0.5"
                    step="0.01"
                    value={settings.bg_music_volume}
                    onChange={(e) => updateField("bg_music_volume", Number(e.target.value))}
                    style={{ width: "100%", accentColor: "var(--neon-purple)" }}
                  />
                </div>
              )}
            </GlassCard>
          </div>

          <div style={{ marginTop: "1.5rem" }}>
            <GlassCard>
              <h3>Integrations</h3>
              
              <div style={{ marginTop: "1rem", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div>
                  <h4 style={{ margin: "0 0 0.5rem 0", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    Google Drive
                    {driveStatus?.connected && <span className="status-badge badge-success" style={{ fontSize: "0.7rem", padding: "2px 6px" }}>Connected</span>}
                  </h4>
                  <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                    Automatically upload generated videos to a "MAiX-YT" folder in your Drive.
                  </p>
                  {driveStatus?.connected && driveStatus?.email && (
                    <p style={{ margin: "0.5rem 0 0 0", fontSize: "0.85rem", color: "var(--text-primary)" }}>
                      Connected as: <strong>{driveStatus.email}</strong>
                    </p>
                  )}
                </div>
                
                <div>
                  {loadingDrive ? (
                    <button className="btn-secondary" disabled>Loading...</button>
                  ) : driveStatus?.connected ? (
                    <button className="btn-secondary" onClick={handleDisconnectDrive} style={{ border: "1px solid rgba(255,100,100,0.3)", color: "#ff8888" }}>
                      Disconnect
                    </button>
                  ) : (
                    <button className="btn-primary" onClick={handleConnectDrive}>
                      Connect Google Drive
                    </button>
                  )}
                </div>
              </div>
              
              {!driveStatus?.configured && !loadingDrive && (
                <div style={{ marginTop: "1rem", padding: "0.75rem", backgroundColor: "rgba(255, 100, 100, 0.1)", color: "#ff8888", borderRadius: "var(--radius-sm)", fontSize: "0.85rem" }}>
                  ⚠️ Google Drive API is not configured on the server. Please check the setup guide.
                </div>
              )}
            </GlassCard>
          </div>

          <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", alignItems: "center" }}>
            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? "⏳ Saving..." : "💾 Save Settings"}
            </button>
            {saved && (
              <span style={{ color: "var(--success)", fontSize: "0.85rem" }}>
                ✅ Settings saved successfully
              </span>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
