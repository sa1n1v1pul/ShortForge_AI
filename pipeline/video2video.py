"""
ShortForge AI — Video-to-Video Pipeline (Advanced Mode)
=======================================================
Handles the V2V workflow: video upload -> frame extraction -> 
prompt modification via Veo -> new AI audio -> final video assembly.
"""

import os
import uuid
import time
import subprocess
import json
from pathlib import Path

from config import TEMP_DIR, OUTPUT_DIR, get_scene_count, GEMINI_API_KEY, GEMINI_API_KEY_FREE
from pipeline.script_writer import _call_gemini
from pipeline.voice_generator import generate_all_voices
from pipeline.video_animator import animate_all_scenes
from pipeline.video_assembler import assemble_final_video


def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 10.0  # Fallback


def extract_frames(video_path: str, interval: int, job_id: str) -> list[str]:
    """Extract frames from video at specific interval (seconds)."""
    frames = []
    duration = get_video_duration(video_path)
    
    num_frames = int(duration / interval)
    if num_frames == 0:
        num_frames = 1
        
    for i in range(num_frames):
        timestamp = i * interval
        out_path = str(TEMP_DIR / f"{job_id}_frame_{i:03d}.jpg")
        
        cmd = [
            "ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
            "-frames:v", "1", "-q:v", "2", out_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        if Path(out_path).exists():
            frames.append(out_path)
            
    return frames


def generate_v2v_script(prompt: str, language: str, num_frames: int, frames: list[str] = None, api_key_mode: str = "1") -> dict:
    """Generate a narration script based on the user's V2V prompt and video frames."""
    sys_prompt = (
        f"You are a master storyteller and a premium short-form video script writer. "
        f"I am providing you with {num_frames} frames extracted from a video. "
        f"Your task is to write ONE continuous, fluid narration script for the ENTIRE video in {language}.\n\n"
        f"CRITICAL INSTRUCTIONS:\n"
        f"1. Write the script as a single, continuous paragraph in engaging, conversational {language}.\n"
        f"2. DO NOT split the script into multiple scenes. Return exactly ONE scene in the JSON.\n"
        f"3. Make it emotional and captivating. Aim for about 100-150 words depending on the video's apparent duration.\n"
    )

    if prompt:
        sys_prompt += (
            f"4. The user has provided this custom prompt/guidance: '{prompt}'.\n"
            f"   Use this purely as a THEMATIC GUIDE. DO NOT speak this literal text! Weave the core idea of their prompt naturally into the story.\n"
        )
    else:
        sys_prompt += (
            f"4. The user did not provide a custom prompt. Just invent a captivating story based entirely on what you see in the frames.\n"
        )

    sys_prompt += (
        f"\nReturn ONLY a JSON object in this exact format:\n"
        f"{{\n"
        f"  \"title\": \"Catchy Title\",\n"
        f"  \"description\": \"Video description\",\n"
        f"  \"hashtags\": \"#tags\",\n"
        f"  \"scenes\": [\n"
        f"    {{\n"
        f"      \"text\": \"The entire continuous narration text here...\",\n"
        f"      \"image_prompt\": \"Overall visual description\"\n"
        f"    }}\n"
        f"  ]\n"
        f"}}\n"
        f"CRITICAL: Ensure the output is 100% valid JSON. Do NOT use unescaped quotes inside strings."
    )
    
    for attempt in range(2):
        try:
            raw_text = None
            keys_to_try = []
            if api_key_mode == "1":
                keys_to_try = [("paid", GEMINI_API_KEY)]
            else:
                keys_to_try = [("free", GEMINI_API_KEY_FREE)]

            for key_name, key_value in keys_to_try:
                try:
                    raw_text = _call_gemini(sys_prompt + "\n\nUser Prompt: " + prompt, key_value, frames)
                    break
                except Exception as e:
                    print(f"Key {key_name} failed: {e}")
                    
            if not raw_text:
                raise ValueError(f"API key mode {api_key_mode} failed for V2V script generation.")
                
            # Clean JSON
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
                
            # Clean control characters that break JSON
            import re
            raw_text = re.sub(r'[\x00-\x1F]+', ' ', raw_text)
            
            script = json.loads(raw_text.strip())
            return script
        except Exception as e:
            print(f"Attempt {attempt+1} Error generating V2V script: {e}")
            if attempt == 1:
                # Fallback
                return {
                    "title": "V2V Generated Video",
                    "scenes": [{"text": prompt, "image_prompt": prompt} for _ in range(num_frames)]
                }


def process_v2v_pipeline(
    video_path: str,
    v2v_prompt: str,
    remove_audio: bool,
    generate_voice: bool,
    language: str,
    voice_profile: str,
    original_volume: float,
    animate: bool,
    api_key_mode: str = "1",
    progress_callback=None
) -> str | None:
    """
    Main pipeline for Advanced Mode (Video-to-Video).
    """
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    def _progress(step: str, msg: str):
        if progress_callback:
            progress_callback(step, msg)
            
    print(f"\n{'='*60}")
    print(f"  🚀 NEW V2V JOB: {job_id}")
    print(f"  Prompt: {v2v_prompt}")
    print(f"  Generate Voice: {generate_voice}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Extract frames (scenes)
        _progress("script", "Analyzing video & extracting scenes...")
        frames = extract_frames(video_path, interval=5, job_id=job_id)
        num_scenes = len(frames)
        
        # Step 2: Generate script & voice
        scenes = []
        if generate_voice:
            _progress("script", "Analyzing video and writing matching script...")
            script = generate_v2v_script(v2v_prompt, language, len(frames), frames=frames, api_key_mode=api_key_mode)
            
            # Make sure we don't have more script scenes than frames
            script_scenes = script.get("scenes", [])
            for i, frame in enumerate(frames):
                text = script_scenes[i]["text"] if i < len(script_scenes) else ""
                iprompt = script_scenes[i]["image_prompt"] if i < len(script_scenes) else v2v_prompt
                scenes.append({
                    "text": text,
                    "image_prompt": f"{iprompt}. {v2v_prompt}", # combine user prompt
                    "media_path": frame,
                    "media_type": "image",
                    "duration": 5
                })
                
            _progress("voice", "Synthesizing audio...")
            scenes = generate_all_voices(
                scenes=scenes,
                job_id=job_id,
                language=language,
                niche="custom",
                voice_profile=voice_profile
            )
        else:
            # No voice generated, just use frames and prompt
            for i, frame in enumerate(frames):
                scenes.append({
                    "text": "",
                    "image_prompt": v2v_prompt,
                    "media_path": frame,
                    "media_type": "image",
                    "duration": 5,
                    "audio_path": None
                })
                
        # If animate=False, we bypass Veo completely and just add audio to the original video
        if not animate:
            if not generate_voice:
                # User just wants to remove audio? Let's just output it
                _progress("assembly", "Applying audio changes to original video...")
                final_output_path = str(TEMP_DIR / f"{job_id}_final_v2v.mp4")
                if remove_audio:
                    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-c", "copy", "-an", final_output_path], capture_output=True)
                else:
                    import shutil
                    shutil.copy2(video_path, final_output_path)
            else:
                _progress("assembly", "Merging new audio with original video...")
                # We need to precisely align the generated audio clips to their scenes (1 scene = 5 seconds)
                valid_scenes = [s for s in scenes if s.get("audio_path")]
                combined_audio = str(TEMP_DIR / f"{job_id}_combined_audio.m4a")
                
                if valid_scenes:
                    if len(valid_scenes) == 1:
                        # Only 1 scene (continuous script), just copy it directly
                        import shutil
                        shutil.copy2(valid_scenes[0]["audio_path"], combined_audio)
                    else:
                        inputs = []
                        filter_parts = []
                        mix_inputs = []
                        for idx, scene in enumerate(valid_scenes):
                            inputs.extend(["-i", scene["audio_path"]])
                            # Scene 0 starts at 0, Scene 1 at 5s, etc.
                            delay_ms = idx * 5 * 1000 
                            filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[a{idx}]")
                            mix_inputs.append(f"[a{idx}]")
                            
                        # amix reduces volume by number of inputs, so we multiply volume by number of inputs to restore
                        filter_complex = ";".join(filter_parts) + ";" + "".join(mix_inputs) + f"amix=inputs={len(valid_scenes)}:duration=longest:dropout_transition=2,volume={len(valid_scenes)}[aout]"
                        
                        cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex, "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", combined_audio]
                        res = subprocess.run(cmd, capture_output=True)
                        if res.returncode != 0:
                            print(f"Audio merge failed: {res.stderr.decode('utf-8', errors='ignore')}")
                else:
                    # Fallback empty audio
                    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "5", "-c:a", "aac", combined_audio], capture_output=True)
                
                final_output_path = str(TEMP_DIR / f"{job_id}_final_v2v.mp4")
                
                if remove_audio:
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", combined_audio,
                        "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k",
                        final_output_path
                    ]
                else:
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", combined_audio,
                        "-filter_complex", f"[0:a]volume={original_volume}[orig_a];[orig_a][1:a]amix=inputs=2:duration=longest:dropout_transition=2,volume=2.0[aout]",
                        "-map", "0:v", "-map", "[aout]",
                        "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k",
                        final_output_path
                    ]
                res = subprocess.run(cmd, capture_output=True)
                if res.returncode != 0:
                    print(f"Video merge failed: {res.stderr.decode('utf-8', errors='ignore')}")
                
            if Path(final_output_path).exists():
                from datetime import date
                import shutil
                today_dir = OUTPUT_DIR / date.today().isoformat()
                today_dir.mkdir(parents=True, exist_ok=True)
                import unicodedata
                safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in v2v_prompt[:20])
                safe_title = safe_title.strip().replace(" ", "_") or "v2v_audio_swap"
                existing = len(list(today_dir.glob(f"{safe_title}*.mp4")))
                final_saved = str(today_dir / f"{safe_title}_{existing+1:03d}.mp4")
                shutil.copy2(final_output_path, final_saved)
                _progress("complete", f"V2V Complete! {Path(final_saved).name}")
                return final_saved
            else:
                _progress("error", "Failed to merge audio.")
                return None

        # Step 3: Animate with Veo (If animate is True)
        _progress("animation", f"Applying V2V transformation with Veo ({len(scenes)} scenes)...")
        scenes = animate_all_scenes(scenes, job_id, niche="custom")
        
        # Ensure fallback if Veo fails (though it defeats the purpose of V2V)
        # animate_all_scenes will leave animated_path as None if it fails.
        
        # Step 4: Assemble final video
        _progress("assembly", "Assembling transformed video...")
        
        # If the user didn't want to remove original audio, and we didn't generate new voice
        # we might want to attach original audio. But for simplicity, we assume V2V creates
        # entirely new scenes, so original audio alignment might be broken anyway.
        # We'll use the generated audio.
        
        final_path = assemble_final_video(
            scenes=scenes,
            captions_path=None,  # skip captions for now to save time
            job_id=job_id,
            title="v2v_transformation",
            enable_music=False, # User requested no background music
            enable_captions=False
        )
        
        if final_path:
            _progress("complete", f"V2V Complete! {Path(final_path).name}")
            return final_path
        else:
            _progress("error", "Video assembly failed.")
            return None
            
    except Exception as e:
        _progress("error", f"V2V Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
