# 🎬 ShortForge AI

**Automated Faceless YouTube Shorts / Instagram Reels Generator**

One command → Ready-to-upload viral content. No face, no editing, no hassle.

## 🔥 What It Does

```
Topic → Gemini AI Script → AI Voice → Stock Images → Image Enhancement → Captions → Final Video
```

- **Gemini AI** writes viral scripts per niche
- **Edge-TTS** generates natural AI voice (FREE)
- **Pexels API** fetches HD stock images (FREE)
- **Real-ESRGAN** enhances images to crystal clear 4x quality
- **FFmpeg** assembles final 9:16 vertical video with Ken Burns effect
- **Word-by-word captions** in viral style (karaoke effect)

## ⚡ Quick Start

```bash
# Generate your first video
python main.py --topic "5 amazing psychology facts"

# Interactive mode
python main.py

# Batch mode (5 videos at once)
python main.py --niche tech_ai --count 5

# Hindi content
python main.py --niche motivation --lang hindi
```

## 📋 Available Niches

| # | Niche | Emoji |
|---|-------|-------|
| 1 | Amazing Facts | 🤯 |
| 2 | Psychology Tricks | 🧠 |
| 3 | Tech & AI Facts | 🤖 |
| 4 | Motivational | 💪 |
| 5 | Scary Facts | 👻 |
| 6 | History Facts | 📜 |
| 7 | Science Facts | 🔬 |
| 8 | Money & Finance | 💰 |

## 🛠️ Setup

### Prerequisites
1. **Python 3.12+**
2. **FFmpeg** — `winget install Gyan.FFmpeg`
3. **Gemini API Key** — from Google AI Studio
4. **Pexels API Key** — FREE at https://www.pexels.com/api/

### Install
```bash
pip install google-genai edge-tts requests Pillow
```

### Configure
Edit `config.py` and set your API keys:
```python
GEMINI_API_KEY = "your-actual-gemini-key"
PEXELS_API_KEY = "your-actual-pexels-key"
```

## 📁 Project Structure

```
ShortForge-AI/
├── main.py                 # Entry point
├── config.py               # All settings & API keys
├── pipeline/
│   ├── script_writer.py    # Gemini AI script generation
│   ├── voice_generator.py  # Edge-TTS voice synthesis
│   ├── media_fetcher.py    # Pexels stock images/videos
│   ├── image_enhancer.py   # Real-ESRGAN 4x upscaling
│   ├── caption_maker.py    # ASS subtitle generation
│   └── video_assembler.py  # FFmpeg video assembly
├── templates/
│   ├── prompts.py          # Gemini prompt templates
│   └── styles.py           # Caption style presets
├── assets/
│   ├── fonts/              # Custom fonts
│   └── music/              # Background music
├── output/                 # Generated videos
└── temp/                   # Temporary files
```

## 💰 Revenue Strategy

Upload to **3 platforms simultaneously**:
- YouTube Shorts
- Instagram Reels  
- Facebook Reels (fastest monetization!)

Daily 5-10 videos → 150-300 videos/month → Revenue in 1-3 months

## 📝 License

Personal use. Built with ❤️ by a developer who refused to stay behind.
