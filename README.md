# 🎬 AI YouTube Automation Platform

An AI-powered platform that automates YouTube video creation — from topic selection to final video assembly.

Built with **Streamlit**, **n8n**, **Google Gemini**, **gTTS**, **Pexels**, and **FFmpeg**.

---

## Architecture

```
Streamlit (UI)
    → n8n (Workflow Orchestrator)
        → Python Scripts (AI Processing)
            → Gemini API (Script & Metadata)
            → Pexels API (Stock Visuals)
            → gTTS (Voice Narration)
            → FFmpeg (Video Assembly)
        → output/ (Final Video)
    → Streamlit (Preview & Download)
```

---

## Quick Start

### 1. Clone & Install

```bash
cd youtube-automation
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Run the App

```bash
streamlit run app.py
```

### 4. (Optional) Start n8n

```bash
npx n8n
# Then import n8n/workflow.json into the n8n editor
```

---

## Project Structure

```
youtube-automation/
├── app.py                      # Streamlit dashboard
├── n8n/
│   └── workflow.json           # n8n workflow (importable)
├── scripts/
│   ├── config.py               # Centralized configuration
│   ├── trend.py                # Trending topic discovery
│   ├── script_generator.py     # AI script writing (Gemini)
│   ├── voice_generator.py      # Text-to-speech (gTTS)
│   ├── visual_generator.py     # Image collection (Pexels)
│   ├── video_generator.py      # Video assembly (FFmpeg)
│   ├── metadata_generator.py   # Title/description/tags (Gemini)
│   ├── upload.py               # YouTube upload (optional)
│   └── pipeline.py             # End-to-end orchestrator
├── assets/                     # Intermediate files (audio, images)
├── output/                     # Final generated videos
├── requirements.txt
├── .env.example
└── README.md
```

---

## Development Phases

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Project setup, UI, n8n workflow, stubs | ✅ |
| 2 | Gemini integration, script generation | ⬜ |
| 3 | Voice generation, visual collection | ⬜ |
| 4 | Video assembly with FFmpeg | ⬜ |
| 5 | Metadata generation, YouTube upload | ⬜ |

---

## Requirements

- Python 3.10+
- FFmpeg (on PATH) — needed for Phase 4
- n8n (optional) — for workflow orchestration
- Google Gemini API key — needed from Phase 2
- Pexels API key — needed from Phase 3

---

## License

This is a college/university final-year engineering project.
