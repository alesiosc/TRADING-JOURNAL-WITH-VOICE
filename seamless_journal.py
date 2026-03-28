import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json
from groq import Groq
from notion_client import Client
from token_tracker import log_tokens, get_usage_summary

GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"
WATCH_FILE = "./trading_notes/current_trade.txt"

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

last_content = ""

def process_trade(text):
    global last_content
    
    # Remove "save trade" trigger phrase
    text = text.replace("save trade", "").replace("Save trade", "").strip()
    
    if not text or text == last_content:
        return
    
    last_content = text
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing trade...")
    print(f"Text: {text[:80]}...")
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    
    usage = response.usage
    log_tokens(usage.prompt_tokens, usage.completion_tokens)
    
    data = json.loads(response.choices[0].message.content)
    
    properties = {
        "Name": {"title": [{"text": {"content": f"{data.get('Entry_Type', 'Entry')} - {datetime.now().strftime('%H:%M')}"}}]},
        "Transcript": {"rich_text": [{"text": {"content": text}}]},
        "Date": {"date": {"start": datetime.now().isoformat()}}
    }
    
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
    
    notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
    
    summary = get_usage_summary()
    print(f"SUCCESS! Tokens: {usage.total_tokens} (Today: {summary['today']}, Month: {summary['this_month']})")
    
    # Clear the file for next trade
    with open(WATCH_FILE, 'w', encoding='utf-8') as f:
        f.write("")

class FileWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('current_trade.txt'):
            time.sleep(0.3)
            with open(WATCH_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if "save trade" in content.lower():
                process_trade(content)

if __name__ == "__main__":
    os.makedirs("./trading_notes", exist_ok=True)
    
    # Create the file if it doesn't exist
    if not os.path.exists(WATCH_FILE):
        with open(WATCH_FILE, 'w', encoding='utf-8') as f:
            f.write("")
    
    # Open Notepad with the file
    os.system(f'start notepad "{os.path.abspath(WATCH_FILE)}"')
    
    summary = get_usage_summary()
    
    print("=" * 60)
    print("SEAMLESS TRADING JOURNAL")
    print("=" * 60)
    print(f"\nToken Usage - Today: {summary['today']}, Month: {summary['this_month']}")
    print("\nHOW TO USE:")
    print("1. Dictate into the Notepad window that just opened")
    print("2. Say 'save trade' when done")
    print("3. Auto-processes and updates Notion")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 60 + "\n")
    
    handler = FileWatcher()
    observer = Observer()
    observer.schedule(handler, "./trading_notes", recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        observer.stop()
    observer.join()
