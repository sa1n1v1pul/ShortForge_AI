"""
╔═══════════════════════════════════════════════════════════════╗
║  🎬 ShortForge AI — Automated Faceless Shorts Generator      ║
║  ─────────────────────────────────────────────────────────────║
║  One command → Ready-to-upload YouTube Shorts / Insta Reels   ║
║                                                               ║
║  Usage:                                                       ║
║    python main.py                           (interactive)     ║
║    python main.py --topic "5 amazing facts" (direct)          ║
║    python main.py --niche psychology --count 3 (batch)        ║
╚═══════════════════════════════════════════════════════════════╝
"""

import argparse
import sys
import uuid
import time
import shutil
from pathlib import Path
from datetime import datetime

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    GEMINI_API_KEY, PEXELS_API_KEY, NICHES,
    DEFAULT_LANGUAGE, DEFAULT_NICHE,
    TEMP_DIR, OUTPUT_DIR, FONTS_DIR, MUSIC_DIR,
)
from pipeline.script_writer import generate_script
from pipeline.voice_generator import generate_all_voices
from pipeline.media_fetcher import fetch_all_media
from pipeline.image_enhancer import enhance_all_images
from pipeline.caption_maker import generate_word_captions, generate_sentence_captions
from pipeline.video_assembler import assemble_final_video


# Fix Windows terminal encoding for Unicode characters
import io
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def print_banner():
    """Print the startup banner."""
    print()
    try:
        print("=" * 63)
        print("  ShortForge AI - Automated Faceless Shorts Generator")
        print("  Gemini AI + Real-ESRGAN + Edge-TTS + FFmpeg")
        print("  One command -> Ready-to-upload content")
        print("=" * 63)
    except Exception:
        print("  ShortForge AI - Ready!")
    print()


def check_prerequisites():
    """Check that all required tools and API keys are configured."""
    issues = []

    # Check API keys
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        issues.append("❌ GEMINI_API_KEY not set in config.py")

    if not PEXELS_API_KEY or PEXELS_API_KEY == "YOUR_PEXELS_API_KEY_HERE":
        issues.append("⚠️  PEXELS_API_KEY not set — images won't download (set in config.py)")

    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ver = result.stdout.split("\n")[0]
            print(f"  ✅ FFmpeg: {ver[:60]}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Check common locations
        found = False
        for p in [r"C:\ffmpeg\bin\ffmpeg.exe", r"D:\ffmpeg\bin\ffmpeg.exe"]:
            if Path(p).exists():
                print(f"  ✅ FFmpeg found: {p}")
                found = True
                break
        if not found:
            issues.append("❌ FFmpeg not found! Install from https://ffmpeg.org/download.html")

    # Check Real-ESRGAN
    from config import ESRGAN_ENGINE
    if Path(ESRGAN_ENGINE).exists():
        print(f"  ✅ Real-ESRGAN engine ready")
    else:
        issues.append(f"⚠️  Real-ESRGAN not found at {ESRGAN_ENGINE} — images won't be enhanced")

    # Print issues
    if issues:
        print()
        for issue in issues:
            print(f"  {issue}")
        print()

    # Only block on critical issues (Gemini key)
    critical = [i for i in issues if i.startswith("❌") and "GEMINI" in i]
    if critical:
        print("  🛑 Fix critical issues above before continuing!")
        return False

    return True


def create_single_video(
    niche: str = DEFAULT_NICHE,
    language: str = DEFAULT_LANGUAGE,
    topic: str | None = None,
    enhance_images: bool = True,
    caption_style: str = "word",  # "word" or "sentence"
) -> str | None:
    """
    Generate a single video from scratch.
    This is the main pipeline orchestrator.
    """
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    print(f"\n{'='*60}")
    print(f"  🎬 NEW VIDEO — Job: {job_id}")
    print(f"  Niche: {NICHES.get(niche, {}).get('name', niche)}")
    print(f"  Language: {language}")
    if topic:
        print(f"  Topic: {topic}")
    print(f"{'='*60}")

    try:
        # ── Step 1: Generate Script ──────────────────────────────
        script = generate_script(
            niche=niche,
            language=language,
            topic=topic,
        )
        scenes = script["scenes"]

        # ── Step 2: Generate Voices ──────────────────────────────
        scenes = generate_all_voices(
            scenes=scenes,
            job_id=job_id,
            language=language,
        )

        # ── Step 3: Fetch Background Images ──────────────────────
        has_pexels = PEXELS_API_KEY and PEXELS_API_KEY != "YOUR_PEXELS_API_KEY_HERE"
        if has_pexels:
            scenes = fetch_all_media(
                scenes=scenes,
                job_id=job_id,
                media_type="image",
            )
        else:
            print("\n⚠️  Pexels API key not set — using color backgrounds")
            for scene in scenes:
                scene["media_path"] = None
                scene["media_type"] = None

        # ── Step 4: Enhance Images ───────────────────────────────
        scenes = enhance_all_images(
            scenes=scenes,
            job_id=job_id,
            enable_enhancement=enhance_images and has_pexels,
        )

        # ── Step 5: Generate Captions ────────────────────────────
        if caption_style == "word":
            captions_path = generate_word_captions(scenes, job_id)
        else:
            captions_path = generate_sentence_captions(scenes, job_id)

        # ── Step 6: Assemble Final Video ─────────────────────────
        final_path = assemble_final_video(
            scenes=scenes,
            captions_path=captions_path,
            job_id=job_id,
            title=script.get("title", "video"),
            enable_music=True,
            enable_captions=True,
        )

        elapsed = time.time() - start_time

        if final_path:
            print(f"\n  🎉 VIDEO COMPLETE!")
            print(f"  ⏱️  Total time: {elapsed:.0f} seconds")
            print(f"  📁 Saved: {final_path}")
            print(f"  📝 Title: {script.get('title', 'N/A')}")
            print(f"  📋 Description: {script.get('description', 'N/A')}")
            print(f"  #️⃣  Hashtags: {script.get('hashtags', 'N/A')}")
            print(f"\n  📤 Ready to upload to YouTube / Instagram / Facebook!")
        else:
            print(f"\n  ❌ Video generation failed after {elapsed:.0f}s")

        return final_path

    except Exception as e:
        import traceback
        print(f"\n  ❌ Error: {e}")
        traceback.print_exc()
        return None

    finally:
        # Clean up temp files for this job
        _cleanup_temp(job_id)


def _cleanup_temp(job_id: str):
    """Remove temporary files for a specific job."""
    try:
        if TEMP_DIR.exists():
            for f in TEMP_DIR.glob(f"{job_id}_*"):
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception:
        pass


def interactive_mode():
    """Run in interactive mode — ask user what to generate."""
    print_banner()

    if not check_prerequisites():
        return

    print("\n📋 Available Niches:")
    niche_list = list(NICHES.items())
    for i, (key, info) in enumerate(niche_list, 1):
        print(f"   {i}. {info['emoji']} {info['name']}")

    print()
    choice = input("Choose niche (number or name) [1]: ").strip() or "1"

    try:
        idx = int(choice) - 1
        niche = niche_list[idx][0]
    except (ValueError, IndexError):
        niche = choice if choice in NICHES else DEFAULT_NICHE

    print(f"\n✅ Niche: {NICHES[niche]['name']}")

    # Language
    lang = input("\nLanguage (english/hindi/hinglish) [english]: ").strip() or "english"

    # Custom topic
    topic = input("\nCustom topic (or press Enter for auto): ").strip() or None

    # Number of videos
    count_str = input("\nHow many videos? [1]: ").strip() or "1"
    count = max(1, min(10, int(count_str)))

    # Enhancement
    enhance = input("\nEnhance images with Real-ESRGAN? (y/n) [y]: ").strip().lower() != "n"

    print(f"\n🚀 Generating {count} video(s)...")
    print(f"   Niche: {NICHES[niche]['name']}")
    print(f"   Language: {lang}")
    print(f"   Enhancement: {'ON' if enhance else 'OFF'}")

    results = []
    for i in range(count):
        if count > 1:
            print(f"\n{'━'*60}")
            print(f"  📹 Video {i + 1} of {count}")
            print(f"{'━'*60}")

        path = create_single_video(
            niche=niche,
            language=lang,
            topic=topic,
            enhance_images=enhance,
        )
        if path:
            results.append(path)

    # Summary
    print(f"\n\n{'═'*60}")
    print(f"  🎬 SESSION COMPLETE")
    print(f"{'═'*60}")
    print(f"  ✅ Generated: {len(results)}/{count} videos")
    for i, p in enumerate(results, 1):
        print(f"  {i}. {p}")
    print(f"{'═'*60}")


def main():
    parser = argparse.ArgumentParser(
        description="🎬 ShortForge AI — Automated Faceless Shorts Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    Interactive mode
  python main.py --topic "5 psychology facts"       Single video
  python main.py --niche tech_ai --count 5          Batch mode
  python main.py --niche horror --lang hindi         Hindi horror facts
        """,
    )
    parser.add_argument("--topic", "-t", help="Specific topic for the video")
    parser.add_argument("--niche", "-n", default=DEFAULT_NICHE,
                        choices=list(NICHES.keys()),
                        help=f"Content niche (default: {DEFAULT_NICHE})")
    parser.add_argument("--lang", "-l", default=DEFAULT_LANGUAGE,
                        choices=["english", "hindi", "hinglish"],
                        help=f"Language (default: {DEFAULT_LANGUAGE})")
    parser.add_argument("--count", "-c", type=int, default=1,
                        help="Number of videos to generate (default: 1)")
    parser.add_argument("--no-enhance", action="store_true",
                        help="Skip Real-ESRGAN image enhancement")
    parser.add_argument("--captions", default="word",
                        choices=["word", "sentence"],
                        help="Caption style (default: word)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Force interactive mode")

    args = parser.parse_args()

    print_banner()

    if not check_prerequisites():
        sys.exit(1)

    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1 or args.interactive:
        interactive_mode()
        return

    # Batch/direct mode
    print(f"\n🚀 Generating {args.count} video(s)...")

    results = []
    for i in range(args.count):
        if args.count > 1:
            print(f"\n{'━'*60}")
            print(f"  📹 Video {i + 1} of {args.count}")
            print(f"{'━'*60}")

        path = create_single_video(
            niche=args.niche,
            language=args.lang,
            topic=args.topic,
            enhance_images=not args.no_enhance,
            caption_style=args.captions,
        )
        if path:
            results.append(path)

    # Summary
    print(f"\n\n{'═'*60}")
    print(f"  🎬 BATCH COMPLETE")
    print(f"{'═'*60}")
    print(f"  ✅ Generated: {len(results)}/{args.count} videos")
    for i, p in enumerate(results, 1):
        print(f"  {i}. {p}")
    print(f"{'═'*60}")


if __name__ == "__main__":
    main()
