#!/bin/bash
# start.sh — Entrypoint for Render Docker deployment

# Start the background worker process
# Redirect output to stderr (fd 2) so Render captures it in logs
python -m backend.worker 2>&1 &

# Start the FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
