import os
import time
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from groq import Groq
from notion_client import Client
from token_tracker import log_tokens, get_usage_summary

# Configuration
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"
WATCH_FOLDER = "./trading_notes"

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

def process_file(filepath):
    print(f"\nNew file: {filepath}")
    time.sleep(0.5)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    if not text:
        print("Empty file, skipping.")
        return
    
    print(f"Processing: {text[:80]}...")
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        response_format={"type": "json_object"}
    )
    
    # Log token usage
    usage = response.usage
    log_tokens(usage.prompt_tokens, usage.completion_tokens)
    
    data = json.loads(response.choices[0].message.content)
    print(f"Parsed: {json.dumps(data, indent=2)}")
    
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
    
    # Show token usage
    summary = get_usage_summary()
    print(f"SUCCESS! Tokens used: {usage.total_tokens} (Today: {summary['today']}, Month: {summary['this_month']})\n")
    
    archive_folder = os.path.join(WATCH_FOLDER, "processed")
    os.makedirs(archive_folder, exist_ok=True)
    archive_path = os.path.join(archive_folder, os.path.basename(filepath))
    os.rename(filepath, archive_path)

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            process_file(event.src_path)

if __name__ == "__main__":
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    
    summary = get_usage_summary()
    
    print("=" * 60)
    print("TRADING JOURNAL AUTO-WATCHER")
    print("=" * 60)
    print(f"\nWatching: {os.path.abspath(WATCH_FOLDER)}")
    print(f"\nToken Usage:")
    print(f"  Today: {summary['today']} tokens")
    print(f"  This Month: {summary['this_month']} tokens")
    print(f"  All Time: {summary['all_time']} tokens")
    print("\nHOW TO USE:")
    print("1. Dictate with Zavi (Right Ctrl) into Notepad")
    print("2. Save as .txt in trading_notes folder")
    print("3. Auto-processes and updates Notion")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 60 + "\n")
    
    handler = FileHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_FOLDER, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        observer.stop()
    observer.join()
    print("Stopped.\n")
