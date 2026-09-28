import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# New SDK: create one client, reuse it
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# Model names for the new SDK (Gemini 2.x family)
PRO_MODEL = "gemini-3.5-flash-lite"          # or "gemini-2.5-pro" if available on your key
FLASH_MODEL = "gemini-2.0-flash"


def generate_workout_gemini(user_input: dict) -> str:
    """
    Generate a personalized 7-day workout plan using Gemini.
    """
    goal = user_input.get("goal", "general fitness")
    intensity = user_input.get("intensity", "medium")

    prompt = f"""You are a professional fitness trainer. Create a personalized, structured 7-day workout plan for someone with the goal of **{goal}** and prefers **{intensity} intensity** workouts.

Each day must include:
- A warm-up (5-10 mins)
- Main workout (targeted exercises, sets & reps)
- Cooldown or recovery tip

Format:
Day 1:
Warm-up:
Main Workout:
Cooldown:
(Repeat for Day 2-7)
"""
    try:
        if client is None:
            raise RuntimeError("Gemini client not configured. Check GOOGLE_API_KEY in .env.")
        response = client.models.generate_content(
            model=PRO_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"