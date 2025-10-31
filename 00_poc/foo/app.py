from google import genai
from google.genai import types

google_client = genai.Client(api_key="AIzaSyAf8NARQmskJOPz4QJtGBNZbE1lS3H-CV8")

response = google_client.models.generate_content(
    model="gemma-3-27b-it",
    contents="你能帮我看看比亚迪的股票吗",
    #config=types.GenerateContentConfig(
    #    thinking_config=types.ThinkingConfig(thinking_budget=-1)
    #),
)

print(response.text)