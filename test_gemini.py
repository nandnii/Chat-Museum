from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key = API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Say hello in a creative way!"
)
print(response.text)