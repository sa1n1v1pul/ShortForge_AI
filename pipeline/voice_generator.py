"""
ShortForge AI — Voice Generator (Edge-TTS)
=============================================
Converts text to natural-sounding speech using Microsoft Edge TTS (FREE).
Also extracts word-level timing for subtitle sync.
"""

import asyncio
import json
import re
from pathlib import Path

import edge_tts

from config import (
    VOICE_ID_ENGLISH,
    VOICE_ID_HINDI,
    VOICE_RATE,
    VOICE_VOLUME,
    TEMP_DIR,
)


def _get_voice_id(language: str) -> str:
    """Get the Edge-TTS voice ID for the given language."""
    voices = {
        "english": VOICE_ID_ENGLISH,
        "hindi": VOICE_ID_HINDI,
        "hinglish": VOICE_ID_HINDI,  # Hinglish uses Hindi voice
    }
    return voices.get(language, VOICE_ID_ENGLISH)


async def _generate_voice_async(
    text: str,
    output_path: str,
    voice_id: str,
    rate: str = VOICE_RATE,
    volume: str = VOICE_VOLUME,
) -> list[dict]:
    """
    Generate voice audio and return word-level timing data.
    Returns list of dicts: [{"word": "Hello", "start": 0.5, "end": 0.8}, ...]
    """
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume)

    word_timings = []

    # Write audio and collect timing via SubMaker
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,  # Convert from 100ns to seconds
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })

    return word_timings


def generate_scene_voice(
    text: str,
    scene_index: int,
    job_id: str,
    language: str = "english",
) -> tuple[str, float, list[dict]]:
    """
    Generate voice for a single scene.

    Returns:
        (audio_path, duration_seconds, word_timings)
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    output_path = str(TEMP_DIR / f"{job_id}_scene_{scene_index:03d}.mp3")
    voice_id = _get_voice_id(language)

    print(f"   🗣️  Scene {scene_index + 1}: Generating voice...")

    # Run async TTS
    word_timings = asyncio.run(
        _generate_voice_async(text, output_path, voice_id)
    )

    # Calculate duration from last word timing, or from file
    if word_timings:
        duration = word_timings[-1]["end"] + 0.3  # Add small padding
    else:
        # Fallback: estimate from text length (avg 3 words/sec)
        word_count = len(text.split())
        duration = word_count / 2.8

    preview = text[:50] + "..." if len(text) > 50 else text
    print(f"         \"{preview}\"")
    print(f"         Duration: {duration:.1f}s | Words: {len(word_timings)}")

    return output_path, duration, word_timings


def generate_all_voices(
    scenes: list[dict],
    job_id: str,
    language: str = "english",
) -> list[dict]:
    """
    Generate voice for all scenes.

    Returns list of scene info dicts with audio paths, durations, and timings.
    """
    print(f"\n🗣️  Generating voices for {len(scenes)} scenes...")

    results = []
    for i, scene in enumerate(scenes):
        audio_path, duration, word_timings = generate_scene_voice(
            text=scene["text"],
            scene_index=i,
            job_id=job_id,
            language=language,
        )
        results.append({
            "index": i,
            "text": scene["text"],
            "image_query": scene.get("image_query", "abstract background"),
            "audio_path": audio_path,
            "duration": duration,
            "word_timings": word_timings,
        })

    total_duration = sum(r["duration"] for r in results)
    print(f"   ✅ All voices generated! Total duration: {total_duration:.1f}s")

    return results


if __name__ == "__main__":
    # Quick test
    test_scenes = [
        {"text": "Did you know that honey never spoils? Archaeologists have found 3000 year old honey in Egyptian tombs.", "image_query": "honey jar"},
        {"text": "Octopuses have three hearts and blue blood.", "image_query": "octopus underwater"},
    ]
    results = generate_all_voices(test_scenes, "test001", "english")
    for r in results:
        print(f"Scene {r['index']}: {r['duration']:.1f}s -> {r['audio_path']}")
