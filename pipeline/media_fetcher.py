"""
ShortForge AI — Media Fetcher (Pexels API)
=============================================
Downloads high-quality stock images and videos from Pexels (FREE API).
"""

import os
import time
import requests
from pathlib import Path

from config import PEXELS_API_KEY, TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT


PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"
PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"

HEADERS = {
    "Authorization": PEXELS_API_KEY,
}


def fetch_image(query: str, scene_index: int, job_id: str) -> str | None:
    """
    Fetch a high-quality portrait image from Pexels.

    Returns the local file path of the downloaded image, or None on failure.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"   🖼️  Scene {scene_index + 1}: Searching \"{query}\"...")

    try:
        params = {
            "query": query,
            "orientation": "portrait",  # Vertical for shorts
            "size": "large",
            "per_page": 5,
            "page": 1,
        }

        resp = requests.get(PEXELS_PHOTO_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        photos = data.get("photos", [])
        if not photos:
            print(f"         ⚠️  No results for \"{query}\", trying fallback...")
            # Try simpler query (first 2 words)
            simple_query = " ".join(query.split()[:2])
            params["query"] = simple_query
            resp = requests.get(PEXELS_PHOTO_URL, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            photos = data.get("photos", [])

        if not photos:
            print(f"         ❌ No images found for \"{query}\"")
            return None

        # Pick the best photo (first result is usually most relevant)
        # Use scene_index to vary results slightly
        photo = photos[scene_index % len(photos)]

        # Get the "large2x" or "large" size for best quality
        img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large") or photo.get("src", {}).get("original")

        if not img_url:
            print(f"         ❌ No image URL found")
            return None

        # Download the image
        output_path = str(TEMP_DIR / f"{job_id}_img_{scene_index:03d}.jpg")
        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(img_resp.content)

        size_kb = len(img_resp.content) // 1024
        photographer = photo.get("photographer", "Unknown")
        print(f"         ✅ Downloaded ({size_kb} KB) by {photographer}")

        return output_path

    except requests.exceptions.RequestException as e:
        print(f"         ❌ Pexels API error: {e}")
        return None


def fetch_video(query: str, scene_index: int, job_id: str, min_duration: float = 5) -> str | None:
    """
    Fetch a stock video from Pexels.

    Returns the local file path of the downloaded video, or None on failure.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"   🎥 Scene {scene_index + 1}: Searching video \"{query}\"...")

    try:
        params = {
            "query": query,
            "orientation": "portrait",
            "size": "medium",
            "per_page": 5,
            "page": 1,
        }

        resp = requests.get(PEXELS_VIDEO_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        videos = data.get("videos", [])
        if not videos:
            print(f"         ⚠️  No video results for \"{query}\"")
            return None

        # Pick a video
        video = videos[scene_index % len(videos)]

        # Find the best quality video file (prefer HD, portrait)
        video_files = video.get("video_files", [])
        best_file = None
        for vf in sorted(video_files, key=lambda x: x.get("height", 0), reverse=True):
            if vf.get("height", 0) >= 720:
                best_file = vf
                break
        if not best_file and video_files:
            best_file = video_files[0]

        if not best_file:
            print(f"         ❌ No video file found")
            return None

        video_url = best_file.get("link")
        if not video_url:
            return None

        # Download
        output_path = str(TEMP_DIR / f"{job_id}_vid_{scene_index:03d}.mp4")
        vid_resp = requests.get(video_url, timeout=60, stream=True)
        vid_resp.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in vid_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = os.path.getsize(output_path) // 1024
        print(f"         ✅ Downloaded video ({size_kb} KB)")

        return output_path

    except requests.exceptions.RequestException as e:
        print(f"         ❌ Pexels video API error: {e}")
        return None


def fetch_all_media(
    scenes: list[dict],
    job_id: str,
    media_type: str = "image",
) -> list[dict]:
    """
    Fetch media for all scenes.

    Args:
        scenes: List of scene dicts (must have 'image_query')
        job_id: Unique job identifier
        media_type: "image" or "video"

    Returns list of scene dicts with 'media_path' added.
    """
    print(f"\n🖼️  Fetching {media_type}s for {len(scenes)} scenes...")

    for i, scene in enumerate(scenes):
        query = scene.get("image_query", "abstract background")

        if media_type == "video":
            path = fetch_video(query, i, job_id)
        else:
            path = fetch_image(query, i, job_id)

        scene["media_path"] = path
        scene["media_type"] = media_type if path else None

        # Small delay to respect rate limits
        if i < len(scenes) - 1:
            time.sleep(0.3)

    success = sum(1 for s in scenes if s.get("media_path"))
    print(f"   ✅ Fetched {success}/{len(scenes)} {media_type}s")

    return scenes


if __name__ == "__main__":
    # Quick test
    test_scenes = [
        {"image_query": "honey jar golden"},
        {"image_query": "octopus underwater"},
    ]
    results = fetch_all_media(test_scenes, "test001", "image")
    for r in results:
        print(f"  {r['image_query']} -> {r.get('media_path', 'FAILED')}")
