import tkinter as tk
from tkinter import scrolledtext
import threading
import json
from datetime import datetime
from groq import Groq
from notion_client import Client
from token_tracker import log_tokens, get_usage_summary

# Configuration
GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
NOTION_TOKEN = "YOUR_NOTION_TOKEN_HERE"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

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

class TradingJournalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Journal with Voice")
        self.root.geometry("800x600")
        
        # Token usage display
        summary = get_usage_summary()
        self.token_label = tk.Label(root, text=f"Tokens - Today: {summary['today']} | Month: {summary['this_month']}", 
                                     font=("Arial", 10), fg="blue")
        self.token_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(root, text="Use Zavi (Right Ctrl) to dictate below, then click 'Save Trade' or say 'save trade'", 
                               font=("Arial", 11))
        instructions.pack(pady=5)
        
        # Text input area
        self.text_area = scrolledtext.ScrolledText(root, width=90, height=20, font=("Arial", 12))
        self.text_area.pack(pady=10)
        
        # Auto-detect "save trade"
        self.text_area.bind('<KeyRelease>', self.check_for_trigger)
        
        # Save button
        self.save_btn = tk.Button(root, text="Save Trade", command=self.save_trade, 
                                  font=("Arial", 14), bg="#4CAF50", fg="white", padx=20, pady=10)
        self.save_btn.pack(pady=10)
        
        # Status display
        self.status_label = tk.Label(root, text="Ready to record...", font=("Arial", 10), fg="green")
        self.status_label.pack(pady=5)
        
    def check_for_trigger(self, event=None):
        text = self.text_area.get("1.0", tk.END).strip().lower()
        if "save trade" in text:
            self.save_trade()
    
    def save_trade(self):
        text = self.text_area.get("1.0", tk.END).strip()
        text = text.replace("save trade", "").replace("Save trade", "").strip()
        
        if not text:
            self.status_label.config(text="No text to save!", fg="red")
            return
        
        self.status_label.config(text="Processing...", fg="orange")
        self.save_btn.config(state="disabled")
        
        # Process in background thread
        thread = threading.Thread(target=self.process_trade, args=(text,))
        thread.start()
    
    def process_trade(self, text):
        try:
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
            self.root.after(0, self.update_success, usage.total_tokens, summary)
            
        except Exception as e:
            self.root.after(0, self.update_error, str(e))
    
    def update_success(self, tokens, summary):
        self.status_label.config(text=f"SUCCESS! Trade saved to Notion ({tokens} tokens)", fg="green")
        self.token_label.config(text=f"Tokens - Today: {summary['today']} | Month: {summary['this_month']}")
        self.text_area.delete("1.0", tk.END)
        self.save_btn.config(state="normal")
    
    def update_error(self, error):
        self.status_label.config(text=f"ERROR: {error}", fg="red")
        self.save_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingJournalApp(root)
    root.mainloop()
