"""
ShortForge AI — Sample Config (TEMPLATE)
==========================================
Copy this file as config.py and fill in your actual API keys.
DO NOT commit config.py to GitHub!
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  API KEYS — Fill in your actual keys below
# ═══════════════════════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "YOUR_PEXELS_API_KEY_HERE")

# ... rest of config same as config.py
