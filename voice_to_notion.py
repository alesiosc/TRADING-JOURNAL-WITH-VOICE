import json
from datetime import datetime
from groq import Groq
from notion_client import Client

# Configuration
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
notion = Client(auth=NOTION_TOKEN)

SYSTEM_PROMPT = """You are a trading journal parser. Extract structured data from voice transcript.

MAPPINGS:
- "hammer" -> M5_Anchor: "Hammer"
- "shooting star" -> M5_Anchor: "Shooting Star"
- "blue level", "ludwig blue" -> Level_Type: "Ludwig Blue"
- "red level", "ludwig red" -> Level_Type: "Ludwig Red"
- "LIS", "LIS level" -> Level_Type: "LIS"
- "BKBrown", "BK Brown" -> Level_Type: "BKBrown"
- "calm", "zen" -> Internal_State: "Zen"
- "anxious", "nervous" -> Internal_State: "Anxious"
- "FOMO" -> Internal_State: "FOMO"
- "revenge", "tilted" -> Internal_State: "Revenge"
- "chased" -> Patience_Grade: "F"
- "waited", "patient" -> Patience_Grade: "A"
- "impulse [number]" -> Impulse: [number]
- "confirmed", "M1 confirmed" -> M1_Confirm: true
- "I'm in", "entered" -> Status: "Active"
- "watching", "waiting" -> Status: "Watching"
- "closed", "out" -> Status: "Closed"

Return JSON only with fields found:
{
  "Entry_Type": "Trade|Observation|Pass|Mindset Check|Pre-Market",
  "M5_Anchor": "Hammer|Shooting Star",
  "Level_Type": "Ludwig Blue|Ludwig Red|LIS|BKBrown",
  "M1_Confirm": true|false,
  "Internal_State": "Zen|Anxious|FOMO|Revenge",
  "Impulse": 1-10,
  "Patience_Grade": "A|B|C|D|F",
  "Status": "Watching|Active|Closed",
  "Summary": "Brief summary"
}"""

def parse_and_upload(text):
    print(f"\nProcessing: {text[:80]}...")
    
    # Parse with Groq AI
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    
    data = json.loads(response.choices[0].message.content)
    print(f"Parsed: {json.dumps(data, indent=2)}")
    
    # Build Notion properties
    properties = {
        "Name": {"title": [{"text": {"content": f"{data.get('Entry_Type', 'Entry')} - {datetime.now().strftime('%H:%M')}"}}]},
        "Transcript": {"rich_text": [{"text": {"content": text}}]},
        "Date": {"date": {"start": datetime.now().isoformat()}}
    }
    
    # Add optional fields
    if "Entry_Type" in data:
        properties["Entry_Type"] = {"select": {"name": data["Entry_Type"]}}
    if "M5_Anchor" in data:
        properties["M5_Anchor"] = {"select": {"name": data["M5_Anchor"]}}
    if "Level_Type" in data:
        properties["Level_Type"] = {"select": {"name": data["Level_Type"]}}
    if "M1_Confirm" in data:
        properties["M1_Confirm"] = {"checkbox": data["M1_Confirm"]}
    if "Internal_State" in data:
        properties["Internal_State"] = {"select": {"name": data["Internal_State"]}}
    if "Impulse" in data:
        properties["Impulse"] = {"number": int(data["Impulse"])}
    if "Patience_Grade" in data:
        properties["Patience_Grade"] = {"select": {"name": data["Patience_Grade"]}}
    if "Status" in data:
        properties["Status"] = {"select": {"name": data["Status"]}}
    if "Summary" in data:
        properties["AI_Analysis"] = {"rich_text": [{"text": {"content": data["Summary"]}}]}
    
    # Create Notion entry
    notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
    print("SUCCESS! Entry added to Notion.\n")

# Interactive mode
if __name__ == "__main__":
    print("=== VOICE TO NOTION ===")
    print("Paste your voice transcript and press Enter twice:\n")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    text = " ".join(lines).strip()
    
    if text:
        parse_and_upload(text)
    else:
        print("No text entered. Exiting.")
