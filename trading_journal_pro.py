import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import json
import os
from datetime import datetime
from groq import Groq
from notion_client import Client
from api_tracker import log_request, get_stats
import mss
from PIL import Image

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

class ScreenshotManager:
    def __init__(self):
        self.screenshot_folder = "./screenshots"
        os.makedirs(self.screenshot_folder, exist_ok=True)
        self.sct = mss.mss()
        self.current_trade_id = None
        self.screenshots = {}
        
    def start_new_trade(self):
        self.current_trade_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshots = {}
        return self.current_trade_id
    
    def capture(self, stage, monitor_num):
        if not self.current_trade_id:
            self.start_new_trade()
        
        timestamp = datetime.now().strftime("%H%M%S")
        
        if monitor_num == 0:
            screenshot = self.sct.grab(self.sct.monitors[0])
        else:
            screenshot = self.sct.grab(self.sct.monitors[monitor_num])
        
        filename = f"Trade_{self.current_trade_id}_{stage}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_folder, filename)
        
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img.save(filepath)
        
        self.screenshots[stage] = filepath
        return filepath
    
    def get_all_screenshots(self):
        return list(self.screenshots.values())

class TradingJournalPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Journal Pro")
        self.root.geometry("900x700")
        
        self.screenshot_mgr = ScreenshotManager()
        self.selected_monitor = tk.IntVar(value=0)
        
        # Stats display
        stats = get_stats()
        stats_frame = tk.Frame(root, bg="#f0f0f0", pady=10)
        stats_frame.pack(fill="x")
        
        self.stats_label = tk.Label(
            stats_frame,
            text=f"Requests: Today {stats['today_requests']} | Month {stats['month_requests']} | Total {stats['total_requests']}\n"
                 f"Tokens: Today {stats['today_tokens']:,} | Month {stats['month_tokens']:,} | Total {stats['total_tokens']:,}",
            font=("Arial", 10),
            bg="#f0f0f0",
            fg="#333"
        )
        self.stats_label.pack()
        
        # Monitor selection
        monitor_frame = tk.Frame(root)
        monitor_frame.pack(pady=10)
        
        tk.Label(monitor_frame, text="Capture Monitor:", font=("Arial", 11)).pack(side="left", padx=5)
        
        for i in range(5):
            label = "All" if i == 0 else str(i)
            tk.Radiobutton(
                monitor_frame,
                text=label,
                variable=self.selected_monitor,
                value=i,
                font=("Arial", 10)
            ).pack(side="left", padx=5)
        
        # Screenshot buttons
        screenshot_frame = tk.Frame(root)
        screenshot_frame.pack(pady=10)
        
        tk.Label(screenshot_frame, text="Screenshots:", font=("Arial", 11, "bold")).pack()
        
        button_frame = tk.Frame(screenshot_frame)
        button_frame.pack(pady=5)
        
        self.screenshot_buttons = {}
        stages = [
            ("Pre-Entry", "pre_entry", "#9C27B0"),
            ("Entry", "entry", "#2196F3"),
            ("During", "during", "#FF9800"),
            ("Close", "close", "#4CAF50"),
            ("Post-Close", "post_close", "#607D8B")
        ]
        
        for label, stage, color in stages:
            btn = tk.Button(
                button_frame,
                text=label,
                command=lambda s=stage: self.take_screenshot(s),
                font=("Arial", 10),
                bg=color,
                fg="white",
                padx=10,
                pady=5
            )
            btn.pack(side="left", padx=5)
            self.screenshot_buttons[stage] = btn
        
        # Screenshot status
        self.screenshot_status = tk.Label(
            screenshot_frame,
            text="No screenshots captured yet",
            font=("Arial", 9),
            fg="#666"
        )
        self.screenshot_status.pack(pady=5)
        
        # Instructions
        instructions = tk.Label(
            root,
            text="Use Zavi (Right Ctrl) to dictate below, then say 'save trade'",
            font=("Arial", 11)
        )
        instructions.pack(pady=5)
        
        # Text input area
        self.text_area = scrolledtext.ScrolledText(
            root,
            width=100,
            height=15,
            font=("Arial", 12)
        )
        self.text_area.pack(pady=10)
        self.text_area.bind('<KeyRelease>', self.check_for_trigger)
        
        # Save button
        self.save_btn = tk.Button(
            root,
            text="Save Trade + Screenshots",
            command=self.save_trade,
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        self.save_btn.pack(pady=10)
        
        # Status display
        self.status_label = tk.Label(
            root,
            text="Ready to record...",
            font=("Arial", 10),
            fg="green"
        )
        self.status_label.pack(pady=5)
    
    def take_screenshot(self, stage):
        monitor = self.selected_monitor.get()
        filepath = self.screenshot_mgr.capture(stage, monitor)
        
        # Update button to show captured
        stage_names = {
            "pre_entry": "Pre-Entry",
            "entry": "Entry",
            "during": "During",
            "close": "Close",
            "post_close": "Post-Close"
        }
        
        captured = [stage_names[s] for s in self.screenshot_mgr.screenshots.keys()]
        status_text = f"Captured: {', '.join(captured)}" if captured else "No screenshots captured yet"
        self.screenshot_status.config(text=status_text, fg="green")
        
        self.status_label.config(text=f"Screenshot saved: {stage_names[stage]}", fg="blue")
    
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
            log_request(usage.prompt_tokens, usage.completion_tokens)
            
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
            
            stats = get_stats()
            screenshots = self.screenshot_mgr.get_all_screenshots()
            
            self.root.after(0, self.update_success, usage.total_tokens, stats, len(screenshots))
            
        except Exception as e:
            self.root.after(0, self.update_error, str(e))
    
    def update_success(self, tokens, stats, screenshot_count):
        self.status_label.config(
            text=f"SUCCESS! Trade saved to Notion ({tokens} tokens, {screenshot_count} screenshots)",
            fg="green"
        )
        
        self.stats_label.config(
            text=f"Requests: Today {stats['today_requests']} | Month {stats['month_requests']} | Total {stats['total_requests']}\n"
                 f"Tokens: Today {stats['today_tokens']:,} | Month {stats['month_tokens']:,} | Total {stats['total_tokens']:,}"
        )
        
        self.text_area.delete("1.0", tk.END)
        self.save_btn.config(state="normal")
        
        # Reset for next trade
        self.screenshot_mgr.start_new_trade()
        self.screenshot_status.config(text="No screenshots captured yet", fg="#666")
    
    def update_error(self, error):
        self.status_label.config(text=f"ERROR: {error}", fg="red")
        self.save_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingJournalPro(root)
    root.mainloop()
