"""
ShortForge AI — Gemini Prompt Templates
=========================================
Carefully crafted prompts per niche that generate viral short-form content.
"""


def get_script_prompt(niche: str, language: str, num_scenes: int = 5, topic: str | None = None) -> str:
    """
    Build the Gemini prompt for a given niche.
    Returns a prompt that asks Gemini to generate a structured JSON script.
    """
    lang_instruction = {
        "english": "Write everything in English. Use simple, conversational English that hooks viewers.",
        "hindi": "Write the narration text in Hindi (Hinglish is ok). Use conversational Hindi that hooks viewers. Keep image_query in English.",
        "hinglish": "Write narration in Hinglish (Hindi written in English script). Keep image_query in English.",
    }.get(language, "Write everything in English.")

    niche_context = {
        "amazing_facts": "amazing and mind-blowing facts that most people don't know. Focus on surprising, counter-intuitive facts that make people say 'wow'.",
        "psychology": "psychology tricks, mind hacks, and human behavior facts. Focus on practical psychological tricks people can use in daily life.",
        "tech_ai": "technology and AI facts, new inventions, and futuristic tech. Focus on things that blow people's minds about how advanced tech is getting.",
        "motivation": "powerful motivational messages, success stories, and life lessons. Focus on actionable advice and inspiring stories.",
        "horror": "creepy, scary, and mysterious facts. Real-world horror, unsolved mysteries, and disturbing historical events. Keep it factual but eerie.",
        "history": "fascinating historical facts, forgotten events, and surprising stories from the past. Focus on 'they never taught you this in school' type content.",
        "science": "mind-blowing science facts, space discoveries, and nature phenomena. Focus on visual and dramatic science facts.",
        "money": "money facts, wealth building psychology, and financial secrets. Focus on surprising money facts and rich people habits.",
    }.get(niche, "interesting and viral-worthy facts.")

    topic_line = ""
    if topic:
        topic_line = f'\nSPECIFIC TOPIC: Make the video specifically about: "{topic}"\n'

    return f"""You are a viral short-form content scriptwriter. Your scripts get millions of views on YouTube Shorts, Instagram Reels, and Facebook.

NICHE: {niche_context}
{lang_instruction}
{topic_line}
Generate a script for a 45-60 second vertical video (YouTube Short / Instagram Reel).

RULES:
1. Start with a HOOK — the first sentence must grab attention instantly. Use patterns like:
   - "Did you know that..."
   - "Scientists just discovered..."
   - "This will change how you think about..."
   - "99% of people don't know this..."
   - "Here's something they never told you..."
2. Each scene should be 6-12 seconds of narration
3. Make it dramatic and engaging — use power words
4. End with a call-to-action: "Follow for more" or "Share this with someone"
5. The image_query should describe a vivid, specific image that matches the narration

Return ONLY valid JSON in this exact format (no markdown, no code blocks, just raw JSON):
{{
  "title": "Catchy title for the video (max 70 chars)",
  "scenes": [
    {{
      "text": "Narration text for this scene (6-12 seconds when spoken)",
      "image_query": "specific descriptive search query for background image (English only, 3-5 words)"
    }},
    {{
      "text": "Next scene narration...",
      "image_query": "descriptive image search query"
    }}
  ],
  "description": "Short video description for YouTube/Instagram (2-3 lines)",
  "hashtags": "relevant hashtags separated by spaces"
}}

Generate exactly {num_scenes} scenes. Make it VIRAL-WORTHY.
"""
