"""
visual_generator.py — Visual Asset Collection

Collects images for each scene from the Pexels stock photo API.

Phase 1: Created colored placeholder images with Pillow.
Phase 3: Fetches real stock photos from Pexels. Falls back to placeholders
         if the API key is missing or the request fails.

Supports dynamic scene counts driven by config.get_scene_count().
Avoids duplicate images by tracking used Pexels photo IDs and requesting
multiple results per query. When the API cannot provide enough unique
results, it intelligently reuses existing images with visual variation.

Pexels API docs: https://www.pexels.com/api/documentation/
"""

import json
import random
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from scripts.config import ASSETS_DIR, get_pexels_api_key

# ---------------------------------------------------------------------------
# Pexels API configuration
# ---------------------------------------------------------------------------
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"

# Target image dimensions (YouTube 16:9)
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720

# How many Pexels results to request per query (more = better dedup pool)
PEXELS_PER_PAGE = 15

# ---------------------------------------------------------------------------
# Placeholder color palette (fallback)
# ---------------------------------------------------------------------------
SCENE_COLORS = [
    (41, 98, 255),    # Vivid blue
    (0, 200, 83),     # Green
    (255, 109, 0),    # Orange
    (156, 39, 176),   # Purple
    (0, 184, 212),    # Cyan
    (255, 61, 0),     # Red-orange
    (76, 175, 80),    # Medium green
    (63, 81, 181),    # Indigo
    (233, 30, 99),    # Pink
    (121, 85, 72),    # Brown
    (0, 150, 136),    # Teal
    (255, 193, 7),    # Amber
]


def _search_pexels(
    query: str,
    api_key: str,
    exclude_ids: set[int] | None = None,
    page: int = 1,
) -> tuple[str | None, int | None]:
    """
    Search Pexels for a photo matching the query.

    Args:
        query:       Search keywords.
        api_key:     Pexels API key.
        exclude_ids: Set of Pexels photo IDs already used (for deduplication).
        page:        Page number for pagination (1-indexed).

    Returns:
        A tuple of (photo_url, photo_id), or (None, None) if no unique result found.
    """
    if exclude_ids is None:
        exclude_ids = set()

    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": PEXELS_PER_PAGE,
        "page": page,
        "orientation": "landscape",
        "size": "large",
    }

    response = requests.get(
        PEXELS_SEARCH_URL,
        headers=headers,
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    photos = data.get("photos", [])

    # Find the first photo not already used
    for photo in photos:
        photo_id = photo.get("id")
        if photo_id not in exclude_ids:
            src = photo.get("src", {})
            url = src.get("large2x") or src.get("large")
            if url:
                return url, photo_id

    return None, None


def _download_image(url: str, save_path: str) -> bool:
    """
    Download an image from a URL and save it as JPEG.

    Returns True on success, False on failure.
    """
    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        # Open with Pillow to resize to exact YouTube dimensions and re-save
        from io import BytesIO
        img = Image.open(BytesIO(response.content)).convert("RGB")

        # Crop to 16:9 aspect ratio then resize
        target_ratio = IMAGE_WIDTH / IMAGE_HEIGHT
        w, h = img.size
        current_ratio = w / h

        if current_ratio > target_ratio:
            # Image is wider -- crop the sides
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            # Image is taller -- crop top and bottom
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))

        img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        img.save(save_path, "JPEG", quality=90)
        return True

    except Exception as e:
        print(f"  [WARN] Failed to download image: {e}")
        return False


def _reuse_existing_image(
    source_path: str,
    save_path: str,
) -> bool:
    """
    Create a visually varied copy of an existing image.

    Applies a slight crop offset to make the reused image look different
    from the original without requiring another API call.

    Returns True on success, False on failure.
    """
    try:
        img = Image.open(source_path).convert("RGB")
        w, h = img.size

        # Apply a random crop offset (5-10% from a random edge)
        offset_x = random.randint(int(w * 0.03), int(w * 0.10))
        offset_y = random.randint(int(h * 0.03), int(h * 0.10))
        side = random.choice(["left", "right", "top", "bottom"])

        if side == "left":
            img = img.crop((offset_x, 0, w, h))
        elif side == "right":
            img = img.crop((0, 0, w - offset_x, h))
        elif side == "top":
            img = img.crop((0, offset_y, w, h))
        else:
            img = img.crop((0, 0, w, h - offset_y))

        img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        img.save(save_path, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"  [WARN] Failed to reuse image: {e}")
        return False


def _create_placeholder_image(
    path: str,
    scene_number: int,
    visual_prompt: str,
):
    """
    Create a colored placeholder image with scene info text.

    Used as fallback when Pexels is unavailable.
    """
    bg_color = SCENE_COLORS[(scene_number - 1) % len(SCENE_COLORS)]
    dark_color = tuple(max(0, c - 40) for c in bg_color)

    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    rect_top = IMAGE_HEIGHT * 2 // 3
    draw.rectangle([0, rect_top, IMAGE_WIDTH, IMAGE_HEIGHT], fill=dark_color)

    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_small = font_large

    label = f"Scene {scene_number}"
    bbox = draw.textbbox((0, 0), label, font=font_large)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((IMAGE_WIDTH - text_width) // 2, IMAGE_HEIGHT // 3),
        label,
        fill="white",
        font=font_large,
    )

    prompt_display = visual_prompt[:80] + "..." if len(visual_prompt) > 80 else visual_prompt
    bbox2 = draw.textbbox((0, 0), prompt_display, font=font_small)
    text_width2 = bbox2[2] - bbox2[0]
    draw.text(
        ((IMAGE_WIDTH - text_width2) // 2, rect_top + 30),
        prompt_display,
        fill="white",
        font=font_small,
    )

    img.save(path, "JPEG", quality=90)


def _build_search_query(visual_prompt: str) -> str:
    """
    Distill the visual prompt into a short Pexels search query.

    Pexels works best with 2-4 keyword phrases rather than full sentences.
    We take the first 6 words and strip filler words.
    """
    filler = {"a", "an", "the", "of", "for", "in", "on", "with", "and", "or", "shot", "showing"}
    words = visual_prompt.lower().split()
    keywords = [w for w in words if w not in filler][:6]
    return " ".join(keywords)


def collect_visuals(script: dict, output_dir: str = None) -> list[str]:
    """
    Collect visual assets for each scene from Pexels.

    Handles dynamic scene counts by:
    - Tracking used Pexels photo IDs to avoid duplicate images across scenes.
    - Requesting multiple results per query and picking the first unused one.
    - When the API cannot provide a unique image, intelligently reusing an
      existing downloaded image with a visual crop variation.

    Args:
        script:     The script dict from script_generator.generate_script().
        output_dir: Directory to save images. Defaults to assets/.

    Returns:
        A list of file paths to the collected images, one per scene.
    """
    if output_dir is None:
        output_dir = str(ASSETS_DIR)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Try to get Pexels API key -- if missing, all scenes use placeholders
    try:
        api_key = get_pexels_api_key()
        use_pexels = True
    except ValueError:
        print("  [INFO] PEXELS_API_KEY not configured, using placeholder images")
        use_pexels = False

    image_files = []
    used_photo_ids: set[int] = set()         # Track Pexels photo IDs for deduplication
    downloaded_paths: list[str] = []          # Track successfully downloaded files for reuse

    scenes = script.get("scenes", [])
    total = len(scenes)

    for scene in scenes:
        scene_num = scene["scene_number"]
        visual_prompt = scene.get("visual_prompt", f"Scene {scene_num}")

        filename = f"scene_{scene_num:02d}_visual.jpg"
        filepath = str(out_path / filename)

        downloaded = False

        if use_pexels:
            query = _build_search_query(visual_prompt)
            try:
                # Try page 1 first, then page 2 if all results are dupes
                for page in range(1, 3):
                    photo_url, photo_id = _search_pexels(query, api_key, used_photo_ids, page)
                    if photo_url:
                        downloaded = _download_image(photo_url, filepath)
                        if downloaded:
                            used_photo_ids.add(photo_id)
                            downloaded_paths.append(filepath)
                            print(f"  [OK] Visual for scene {scene_num}/{total}: {filename} (Pexels: '{query}')")
                            break
                    else:
                        break  # No more results available

                # If Pexels had no unique result, try reusing an existing image
                if not downloaded and downloaded_paths:
                    source = downloaded_paths[scene_num % len(downloaded_paths)]
                    downloaded = _reuse_existing_image(source, filepath)
                    if downloaded:
                        print(f"  [OK] Visual for scene {scene_num}/{total}: {filename} (reused with variation)")

            except Exception as e:
                print(f"  [WARN] Pexels fetch failed for scene {scene_num}: {e}")
                # Try reusing existing image before falling to placeholder
                if downloaded_paths:
                    source = downloaded_paths[scene_num % len(downloaded_paths)]
                    downloaded = _reuse_existing_image(source, filepath)
                    if downloaded:
                        print(f"  [OK] Visual for scene {scene_num}/{total}: {filename} (reused after error)")

        if not downloaded:
            # Fallback: colored placeholder
            _create_placeholder_image(filepath, scene_num, visual_prompt)
            print(f"  [OK] Visual for scene {scene_num}/{total}: {filename} (placeholder)")

        image_files.append(filepath)

    return image_files


# ---------------------------------------------------------------------------
# CLI entry point -- allows calling from n8n via:
#   python -m scripts.visual_generator --script-file assets/script.json
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect visuals for scenes")
    parser.add_argument(
        "--script-file",
        type=str,
        required=True,
        help="Path to script JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save image files",
    )
    args = parser.parse_args()

    with open(args.script_file, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    files = collect_visuals(script_data, args.output_dir)
    print(json.dumps({"image_files": files}, indent=2))
