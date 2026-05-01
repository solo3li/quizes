import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
print(f"Using key: {api_key}")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents="Say hello",
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
