# Test API keys
from dotenv import load_dotenv
import os

load_dotenv()

print("Testing API keys from .env...")
print(f"GROQ_API_KEY: {os.getenv('GROQ_API_KEY')[:20]}..." if os.getenv('GROQ_API_KEY') else "MISSING")
print(f"NOTION_TOKEN: {os.getenv('NOTION_TOKEN')[:20]}..." if os.getenv('NOTION_TOKEN') else "MISSING")
print(f"DATABASE_ID: {os.getenv('DATABASE_ID')}")

# Test Groq
try:
    from groq import Groq
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    print("\nGroq API: OK")
except Exception as e:
    print(f"\nGroq API ERROR: {e}")

# Test Notion
try:
    from notion_client import Client
    notion = Client(auth=os.getenv('NOTION_TOKEN'))
    db = notion.databases.retrieve(database_id=os.getenv('DATABASE_ID'))
    print(f"Notion API: OK - Connected to '{db['title'][0]['plain_text']}'")
except Exception as e:
    print(f"Notion API ERROR: {e}")
