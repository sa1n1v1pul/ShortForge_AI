import asyncio
import edge_tts
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
from config import VOICE_PROFILES

async def main():
    out_dir = Path(r"D:\ShortForge-AI\web\static\samples")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    texts = {
        "hindi": {
            "female": "नमस्ते, मैं आपकी कहानी सुनाऊंगी।",
            "male": "नमस्ते, मैं आपकी कहानी सुनाऊंगा।",
            "child_girl": "नमस्ते, मैं एक छोटी बच्ची हूँ और मुझे कहानियाँ सुनना पसंद है।",
            "baby_boy": "नमस्ते, मैं एक छोटा बच्चा हूँ।",
            "deep_male": "मैं महादेव की आवाज़ हूँ, सृष्टि के कण कण में मेरा वास है।"
        },
        "english": {
            "female": "Hello, I will be narrating your story.",
            "male": "Hello, I will be the voice of your story.",
            "child_girl": "Hi there! I am a little girl and I love listening to stories.",
            "baby_boy": "Hi! I am a little boy.",
            "deep_male": "I am the deep voice, echoing through the cosmos."
        }
    }
    
    tasks = []
    for lang, profiles in VOICE_PROFILES.items():
        for key, profile in profiles.items():
            text = texts[lang][key]
            file_name = f"{lang}_{key}.mp3"
            print(f"Generating {file_name}...")
            comm = edge_tts.Communicate(text=text, voice=profile["voice_id"], pitch=profile["pitch"])
            tasks.append(comm.save(str(out_dir / file_name)))
            
    await asyncio.gather(*tasks)
    print("Done")

asyncio.run(main())
