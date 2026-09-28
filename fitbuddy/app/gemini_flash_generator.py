import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

FLASH_MODEL = "gemini-3.5-flash-lite"


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """
    Generate a nutrition or recovery tip using Gemini Flash based on the user's fitness goal.
    """
    prompt = (
        f"Give one clear, helpful nutrition or recovery tip for someone focused on '{goal}'. "
        "The tip should be practical, friendly, and easy to understand."
    )
    try:
        if client is None:
            raise RuntimeError("Gemini client not configured. Check GOOGLE_API_KEY in .env.")
        response = client.models.generate_content(
            model=FLASH_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Error generating tip: {str(e)}"