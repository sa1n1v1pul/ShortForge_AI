"""
ShortForge AI — Video Animator (Google Veo)
=============================================
Animates AI-generated images into short video clips using Google Veo.
Converts static cartoon images into animated scenes with character movement.
"""

import time
from pathlib import Path
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY, GEMINI_API_KEY_FREE,
    TEMP_DIR, NICHES,
)

# Veo model priority (try lite/fast first for speed, fallback to full)
VEO_MODELS = [
    "veo-3.1-lite-generate-preview",   # Fastest, free preview
    "veo-3.1-fast-generate-preview",   # Fast, good quality
    "veo-3.0-fast-generate-001",       # Stable, fast
    "veo-2.0-generate-001",            # Stable baseline
]

# Max time to wait for video generation (seconds)
VEO_TIMEOUT = 180  # 3 minutes max per clip
VEO_POLL_INTERVAL = 10  # Check every 10 seconds


def _get_animation_prompt(scene_text: str, image_prompt: str, niche: str) -> str:
    """Build animation prompt for Veo from scene description."""
    niche_motion = {
        "radha_krishna": "gentle divine movement, soft wind in clothes, peacock feathers swaying, golden particles floating, serene magical atmosphere",
        "shiv_parvati": "powerful divine aura, trident glowing, hair flowing in cosmic wind, sacred fire flickering, mystical mountain backdrop",
        "hanuman": "heroic powerful movement, divine strength, wind flowing, golden aura pulsing, clouds moving in sky",
        "mythology": "epic cinematic movement, divine weapons glowing, dramatic wind, cosmic energy flowing",
        "moral_stories": "gentle character movement, village life animation, birds flying, trees swaying, warm sunlight",
    }

    motion = niche_motion.get(niche, "subtle natural movement, gentle wind, soft lighting changes")

    return (
        f"Animate this scene: {image_prompt}. "
        f"Animation style: 3D Indian cartoon animation, Pixar quality, smooth movement. "
        f"Motion: {motion}. "
        f"Camera: slow cinematic movement. "
        f"Keep the art style consistent, vibrant divine colors."
    )


def animate_image_with_veo(
    image_path: str,
    scene_text: str,
    image_prompt: str,
    output_path: str,
    niche: str = "",
    duration: int = 4,
) -> bool:
    """
    Animate a static image into a video clip using Google Veo.
    
    Args:
        image_path: Path to the source image
        scene_text: The narration text for context
        image_prompt: Original image prompt for animation guidance
        output_path: Where to save the video clip
        niche: Content niche for style-specific animation
        duration: Video duration in seconds (4-8)
    
    Returns:
        True if video was generated and saved
    """
    animation_prompt = _get_animation_prompt(scene_text, image_prompt, niche)

    # Try both API keys
    for key_name, key_value in [("paid", GEMINI_API_KEY), ("free", GEMINI_API_KEY_FREE)]:
        client = genai.Client(api_key=key_value)

        for model in VEO_MODELS:
            try:
                # If we have a source image, use image-to-video
                if image_path and Path(image_path).exists():
                    # Read image as bytes and create Image object
                    with open(image_path, "rb") as f:
                        img_bytes = f.read()

                    # Detect mime type
                    ext = Path(image_path).suffix.lower()
                    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                            "webp": "image/webp"}.get(ext.lstrip("."), "image/png")

                    img_obj = types.Image(image_bytes=img_bytes, mime_type=mime)

                    op = client.models.generate_videos(
                        model=model,
                        prompt=animation_prompt,
                        image=img_obj,
                        config={
                            "number_of_videos": 1,
                            "duration_seconds": duration,
                            "aspect_ratio": "9:16",
                        },
                    )
                else:
                    # Text-to-video (no source image)
                    op = client.models.generate_videos(
                        model=model,
                        prompt=animation_prompt,
                        config={
                            "number_of_videos": 1,
                            "duration_seconds": duration,
                            "aspect_ratio": "9:16",
                        },
                    )

                # Poll for completion
                for i in range(VEO_TIMEOUT // VEO_POLL_INTERVAL):
                    time.sleep(VEO_POLL_INTERVAL)
                    op = client.operations.get(operation=op)
                    if op.done:
                        break

                if op.done and op.response:
                    vid = op.response.generated_videos[0]
                    vid_data = client.files.download(file=vid.video)

                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(vid_data)

                    size_kb = len(vid_data) / 1024
                    return True

                elif op.done and op.error:
                    continue

            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err or "exhausted" in err.lower():
                    break  # Try next key, not next model
                elif "400" in err and ("billing" in err.lower() or "FAILED_PRECONDITION" in err):
                    break  # This key doesn't have billing
                elif "INVALID_ARGUMENT" in err:
                    continue  # Try next model
                else:
                    continue  # Unknown error, try next

    return False


def animate_all_scenes(
    scenes: list[dict],
    job_id: str,
    niche: str = "",
) -> list[dict]:
    """
    Animate all scene images into video clips using Veo.
    Falls back to static images if Veo is unavailable.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n🎥 Animating {len(scenes)} scenes with AI (Veo)...")

    animated_count = 0
    for i, scene in enumerate(scenes):
        image_path = scene.get("media_path")
        image_prompt = scene.get("image_prompt", scene.get("image_query", ""))
        scene_text = scene.get("text", "")

        output_path = str(TEMP_DIR / f"{job_id}_animated_{i:03d}.mp4")

        print(f"   🎥 Scene {i + 1}: Animating...")
        preview = image_prompt[:55] + "..." if len(image_prompt) > 55 else image_prompt
        print(f"         \"{preview}\"")

        # Calculate ideal clip duration (match audio, capped at 8 sec)
        scene_duration = min(8, max(4, int(scene.get("duration", 5))))

        success = animate_image_with_veo(
            image_path=image_path or "",
            scene_text=scene_text,
            image_prompt=image_prompt,
            output_path=output_path,
            niche=niche,
            duration=scene_duration,
        )

        if success:
            scene["animated_path"] = output_path
            animated_count += 1
            size_kb = Path(output_path).stat().st_size / 1024
            print(f"         ✅ Animated! ({size_kb:.0f} KB)")
        else:
            scene["animated_path"] = None
            print(f"         ⚠️  Veo unavailable, will use static image")

    print(f"   ✅ Animation complete: {animated_count}/{len(scenes)} scenes animated")
    if animated_count == 0:
        print(f"   ℹ️  Veo requires active quota. Static images will be used with Ken Burns effect.")

    return scenes


if __name__ == "__main__":
    # Quick test
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    result = animate_image_with_veo(
        image_path="",
        scene_text="Krishna playing flute",
        image_prompt="Lord Krishna playing divine flute by river Yamuna, peacocks, golden sunset",
        output_path=str(TEMP_DIR / "test_veo.mp4"),
        niche="radha_krishna",
    )
    print(f"Veo animation: {'SUCCESS' if result else 'UNAVAILABLE (quota/billing needed)'}")
