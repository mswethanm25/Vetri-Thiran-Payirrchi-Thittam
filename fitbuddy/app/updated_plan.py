import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

PRO_MODEL = "gemini-3.5-flash-lite"  # or "gemini-2.5-pro"


def update_workout_plan(original_plan: str, user_feedback: str) -> str:
    """
    Update the workout plan based on user feedback using Gemini.
    """
    prompt = f"""You are a professional fitness trainer assistant.

Here's the original 7-day workout plan:
{original_plan}

User Feedback: "{user_feedback}"

Based on the feedback, revise the relevant parts of the workout plan. Keep the format and rest of the plan unchanged if not needed.
"""
    try:
        if client is None:
            raise RuntimeError("Gemini client not configured. Check GOOGLE_API_KEY in .env.")
        response = client.models.generate_content(
            model=PRO_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Error updating plan: {e}"