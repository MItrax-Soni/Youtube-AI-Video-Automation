#!/bin/bash
# start.sh — Entrypoint for Railway / Render Docker deployment

# Start the background worker process
python -m backend.worker &

# Start the FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
