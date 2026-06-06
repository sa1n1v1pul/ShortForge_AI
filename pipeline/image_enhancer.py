"""
ShortForge AI — Image Enhancer (Real-ESRGAN)
===============================================
Uses your existing PixelForge Real-ESRGAN engine to upscale images.
"""

import subprocess
import time
from pathlib import Path

from config import ESRGAN_ENGINE, ESRGAN_MODELS, TEMP_DIR


def enhance_image(
    input_path: str,
    scene_index: int,
    job_id: str,
    scale: int = 4,
    model: str = "realesrgan-x4plus",
) -> str:
    """
    Enhance a single image using Real-ESRGAN.

    Returns the path to the enhanced image.
    If enhancement fails, returns the original image path (graceful fallback).
    """
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        print(f"   ⚠️  Scene {scene_index + 1}: Image not found, skipping enhancement")
        return input_path

    output_path = str(TEMP_DIR / f"{job_id}_enhanced_{scene_index:03d}.png")

    # Check if engine exists
    engine = Path(ESRGAN_ENGINE)
    if not engine.exists():
        print(f"   ⚠️  Real-ESRGAN engine not found at {ESRGAN_ENGINE}")
        print(f"         Using original image (no enhancement)")
        return input_path

    print(f"   ✨ Scene {scene_index + 1}: Enhancing image ({scale}x)...")

    cmd = [
        str(engine),
        "-i", input_path,
        "-o", output_path,
        "-s", str(scale),
        "-n", model,
    ]

    # Add models directory if it exists
    models_dir = Path(ESRGAN_MODELS)
    if models_dir.is_dir():
        cmd += ["-m", str(models_dir)]

    try:
        start = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 min max per image
        )

        elapsed = time.time() - start

        if Path(output_path).exists():
            orig_kb = input_path_obj.stat().st_size // 1024
            new_kb = Path(output_path).stat().st_size // 1024
            print(f"         ✅ Enhanced! {orig_kb}KB → {new_kb}KB ({elapsed:.1f}s)")
            return output_path
        else:
            if result.stderr:
                print(f"         ⚠️  Engine error: {result.stderr[:200]}")
            print(f"         Using original image")
            return input_path

    except subprocess.TimeoutExpired:
        print(f"         ⚠️  Enhancement timed out, using original")
        return input_path
    except Exception as e:
        print(f"         ⚠️  Enhancement error: {e}")
        return input_path


def enhance_all_images(
    scenes: list[dict],
    job_id: str,
    scale: int = 4,
    enable_enhancement: bool = True,
) -> list[dict]:
    """
    Enhance all scene images using Real-ESRGAN.

    Modifies scenes in-place, adding 'enhanced_path' key.
    If enhancement is disabled or fails, enhanced_path = original media_path.
    """
    if not enable_enhancement:
        print(f"\n✨ Image enhancement: SKIPPED (disabled)")
        for scene in scenes:
            scene["enhanced_path"] = scene.get("media_path")
        return scenes

    print(f"\n✨ Enhancing {len(scenes)} images with Real-ESRGAN...")

    enhanced_count = 0
    for i, scene in enumerate(scenes):
        media_path = scene.get("media_path")
        if not media_path:
            scene["enhanced_path"] = None
            continue

        # Only enhance images, not videos
        if scene.get("media_type") == "video":
            scene["enhanced_path"] = media_path
            continue

        enhanced = enhance_image(media_path, i, job_id, scale)
        scene["enhanced_path"] = enhanced

        if enhanced != media_path:
            enhanced_count += 1

    print(f"   ✅ Enhanced {enhanced_count}/{len(scenes)} images")

    return scenes


if __name__ == "__main__":
    # Quick test with a sample image
    import sys
    if len(sys.argv) > 1:
        result = enhance_image(sys.argv[1], 0, "test001")
        print(f"Result: {result}")
    else:
        print("Usage: python image_enhancer.py <image_path>")
