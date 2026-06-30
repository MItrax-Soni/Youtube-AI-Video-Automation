"""
upload.py — YouTube Upload Integration Helper

Handles preparing and formatting video payloads for YouTube upload via n8n workflows.
"""

import json
import os
import sys
from pathlib import Path


def upload_video(video_path: str, metadata: dict) -> dict:
    """
    Simulate or trigger YouTube video upload payload formatting for n8n.

    Args:
        video_path: Absolute path to the MP4 video file.
        metadata:   Dict with title, description, tags, and thumbnail text.

    Returns:
        A dict with upload status information and formatted payload.
    """
    abs_video_path = str(Path(video_path).resolve())
    
    title = metadata.get("title", "Untitled Video")
    description = metadata.get("description", "")
    tags = metadata.get("tags", [])

    print(f"  [INFO] Preparing YouTube upload payload:")
    print(f"    Video File:  {abs_video_path}")
    print(f"    Video Title: {title}")
    print(f"    Tags Count:  {len(tags)}")

    return {
        "status": "ready_for_n8n",
        "video_path": abs_video_path,
        "payload": {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "27",  # Education category ID by default
            },
            "status": {
                "privacyStatus": "private",  # Safe default for automated uploads
                "selfDeclaredMadeForKids": False,
            }
        },
        "message": "Upload payload prepared successfully for n8n workflow node."
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument(
        "--video", type=str, required=True, help="Path to video file"
    )
    parser.add_argument(
        "--metadata-file", type=str, required=True, help="Path to metadata JSON"
    )
    args = parser.parse_args()

    with open(args.metadata_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    result = upload_video(args.video, meta)
    print(json.dumps(result, indent=2, ensure_ascii=False))
