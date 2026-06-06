"""
ShortForge AI — Media Fetcher v2
===================================
Generates AI cartoon images using Gemini, with Pexels stock fallback.
"""

import time
import requests
from pathlib import Path

from config import (
    GEMINI_API_KEY, GEMINI_API_KEY_FREE,
    PEXELS_API_KEY, TEMP_DIR,
    GEMINI_IMAGE_MODEL, IMAGE_STYLE_PREFIX,
    IMAGE_GEN_DELAY, NICHES,
    VIDEO_WIDTH, VIDEO_HEIGHT,
)


def generate_ai_image(prompt: str, output_path: str, niche: str = "") -> bool:
    """
    Generate a cartoon image using Gemini's image generation model.
    Returns True if image was saved successfully.
    """
    from google import genai
    from google.genai import types

    # Add niche-specific style to prompt
    niche_style = NICHES.get(niche, {}).get("image_style", "")
    full_prompt = f"{IMAGE_STYLE_PREFIX}, {niche_style}, {prompt}"

    # Try both keys
    for key_name, key_value in [("paid", GEMINI_API_KEY), ("free", GEMINI_API_KEY_FREE)]:
        try:
            client = genai.Client(api_key=key_value)
            response = client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=f"Generate this image: {full_prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            # Extract image data from response
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    img_data = part.inline_data.data
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    return True

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                continue
            elif "400" in err_str and "API_KEY_INVALID" in err_str:
                continue
            elif "400" in err_str and "safety" in err_str.lower():
                # Content safety filter — modify prompt and retry
                try:
                    safer_prompt = f"Beautiful artistic illustration: {prompt}, family friendly, cartoon style"
                    response = client.models.generate_content(
                        model=GEMINI_IMAGE_MODEL,
                        contents=f"Generate this artistic illustration: {safer_prompt}",
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                        ),
                    )
                    for part in response.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            with open(output_path, "wb") as f:
                                f.write(part.inline_data.data)
                            return True
                except Exception:
                    continue
            else:
                continue

    return False


def fetch_pexels_image(query: str, output_path: str) -> bool:
    """Fallback: download a stock image from Pexels API."""
    if not PEXELS_API_KEY or PEXELS_API_KEY == "YOUR_PEXELS_API_KEY_HERE":
        return False

    headers = {"Authorization": PEXELS_API_KEY}

    try:
        # Search for images
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={
                "query": query,
                "per_page": 5,
                "orientation": "portrait",
                "size": "medium",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("photos"):
            return False

        # Pick first suitable photo
        photo = data["photos"][0]
        img_url = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"]["original"]

        # Download
        img_resp = requests.get(img_url, timeout=30)
        img_resp.raise_for_status()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_resp.content)

        photographer = photo.get("photographer", "Unknown")
        size_kb = len(img_resp.content) / 1024
        print(f"         Pexels fallback: {size_kb:.0f} KB by {photographer}")
        return True

    except Exception as e:
        print(f"         Pexels error: {e}")
        return False


def fetch_all_media(
    scenes: list[dict],
    job_id: str,
    niche: str = "",
    media_type: str = "image",
) -> list[dict]:
    """
    Fetch/generate images for all scenes.
    Priority: AI generation > Pexels stock > Color background
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'🎨' if niche in ['radha_krishna','shiv_parvati','hanuman','mythology','moral_stories'] else '🖼️'}  Generating images for {len(scenes)} scenes...")

    for i, scene in enumerate(scenes):
        # Use image_prompt from script (AI-optimized) or fall back to image_query
        ai_prompt = scene.get("image_prompt", scene.get("image_query", "beautiful background"))
        pexels_query = scene.get("image_query", scene.get("image_prompt", "background").split(",")[0])

        output_path = str(TEMP_DIR / f"{job_id}_media_{i:03d}.png")

        print(f"   🎨 Scene {i + 1}: Generating cartoon image...")
        print(f"         \"{ai_prompt[:60]}...\"")

        # Method 1: AI image generation
        success = generate_ai_image(ai_prompt, output_path, niche)

        if success:
            print(f"         ✅ AI image generated!")
            scene["media_path"] = output_path
            scene["media_type"] = "ai_generated"

            # Rate limit delay between generations
            if i < len(scenes) - 1:
                time.sleep(IMAGE_GEN_DELAY)
            continue

        # Method 2: Pexels stock image fallback
        print(f"         ⚠️  AI generation unavailable, trying Pexels...")
        pexels_path = str(TEMP_DIR / f"{job_id}_media_{i:03d}.jpg")
        success = fetch_pexels_image(pexels_query, pexels_path)

        if success:
            print(f"         ✅ Pexels image downloaded")
            scene["media_path"] = pexels_path
            scene["media_type"] = "pexels"
            continue

        # Method 3: No image available
        print(f"         ⚠️  No image available, will use color background")
        scene["media_path"] = None
        scene["media_type"] = None

    ai_count = sum(1 for s in scenes if s.get("media_type") == "ai_generated")
    pexels_count = sum(1 for s in scenes if s.get("media_type") == "pexels")
    print(f"   ✅ Images ready: {ai_count} AI + {pexels_count} Pexels + {len(scenes) - ai_count - pexels_count} color bg")

    return scenes


if __name__ == "__main__":
    # Quick test
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    test_prompt = "Lord Krishna playing flute by the river Yamuna with peacocks, golden divine light"
    result = generate_ai_image(test_prompt, str(TEMP_DIR / "test_ai.png"), "radha_krishna")
    print(f"AI generation: {'SUCCESS' if result else 'FAILED (using Pexels fallback)'}")
