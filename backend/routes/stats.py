"""
stats.py — GET /api/stats

Returns dashboard metrics computed from the video_jobs collection:
  - total_videos (completed jobs)
  - unique_topics
  - today_count
  - avg_time (average pipeline duration in seconds)
  - success_rate (percentage)
  - recent (last 5 completed jobs for activity feed)
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from backend.services.auth_service import get_current_user
from scripts.database import _db, _use_mongo

router = APIRouter()


@router.get("/api/stats")
async def get_stats(user_id: str = Depends(get_current_user)):
    """
    Return dashboard metrics for the authenticated user.
    """
    if not _use_mongo or _db is None:
        return {
            "total_videos": 0,
            "unique_topics": 0,
            "today_count": 0,
            "avg_time": "—",
            "success_rate": "—",
            "recent": [],
        }

    try:
        # All jobs for this user
        all_jobs = list(
            _db.video_jobs.find({"user_id": user_id})
        )

        completed = [j for j in all_jobs if j.get("status") == "completed"]
        failed = [j for j in all_jobs if j.get("status") == "failed"]

        total_videos = len(completed)

        # Unique topics
        topics = set()
        for j in completed:
            topic = j.get("params", {}).get("topic") or j.get("topic", "")
            if topic:
                topics.add(topic.strip().lower())
        unique_topics = len(topics)

        # Today count
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = 0
        for j in completed:
            created = j.get("created_at", "")
            if isinstance(created, str) and created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if dt >= today_start:
                        today_count += 1
                except (ValueError, TypeError):
                    pass

        # Average time
        total_times = []
        for j in completed:
            timing = j.get("timing", {})
            if timing:
                t = sum(timing.values())
                if t > 0:
                    total_times.append(t)

        if total_times:
            avg_seconds = sum(total_times) / len(total_times)
            if avg_seconds >= 60:
                avg_time = f"{avg_seconds / 60:.1f}m"
            else:
                avg_time = f"{avg_seconds:.0f}s"
        else:
            avg_time = "—"

        # Success rate
        total_finished = len(completed) + len(failed)
        if total_finished > 0:
            rate = (len(completed) / total_finished) * 100
            success_rate = f"{rate:.0f}%"
        else:
            success_rate = "—"

        # Recent activity (last 5 completed jobs)
        recent_jobs = sorted(
            completed,
            key=lambda j: j.get("created_at", ""),
            reverse=True,
        )[:5]

        recent = []
        for j in recent_jobs:
            recent.append({
                "job_id": j.get("_id", ""),
                "title": j.get("video_title") or j.get("params", {}).get("topic", "Untitled"),
                "status": j.get("status", "unknown"),
                "created_at": j.get("created_at", ""),
                "timing": j.get("timing", {}),
            })

        return {
            "total_videos": total_videos,
            "unique_topics": unique_topics,
            "today_count": today_count,
            "avg_time": avg_time,
            "success_rate": success_rate,
            "recent": recent,
        }

    except Exception as e:
        print(f"[Stats] Error computing stats: {e}")
        return {
            "total_videos": 0,
            "unique_topics": 0,
            "today_count": 0,
            "avg_time": "—",
            "success_rate": "—",
            "recent": [],
        }
