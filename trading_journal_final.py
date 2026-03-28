import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq
from notion_client import Client
from api_tracker import log_request, get_stats
from vocabulary_trainer import find_match, add_phrase, load_vocab
import mss
from PIL import Image, ImageGrab

# Configuration
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

groq_client = Groq(api_key=GROQ_API_KEY)
notion = Client(auth=NOTION_TOKEN)

SYSTEM_PROMPT = """You are a trading journal parser. Extract structured data from voice transcript.

FIELD MAPPINGS:
- M5_Pattern: Hammer, Shooting Star, Bullish Engulfing, Bearish Engulfing (can be multiple)
- M1_Confirm: Yes, No
- M5_Form: Perfect, Well-Formed, Decent, Questionable, Poor
- Entry_Direction: Buy, Sell
- Emotions: Zen, Anxious, FOMO, Revenge
- Impulse: 1-10 (number)
- Patience_Score: 1-10 (number, 1-3=strong, 7-10=weak)

SPECIAL LOGIC:
- "engulfing" without bullish/bearish → check Entry_Direction to determine
- Numbers need context: "impulse 7" vs "patience 4"

Return JSON only with fields found:
{
  "M5_Pattern": ["Hammer", "Shooting Star", "Bullish Engulfing", "Bearish Engulfing"],
  "M1_Confirm": "Yes|No",
  "M5_Form": "Perfect|Well-Formed|Decent|Questionable|Poor",
  "Entry_Direction": "Buy|Sell",
  "Emotions": "Zen|Anxious|FOMO|Revenge",
  "Impulse": 1-10,
  "Patience_Score": 1-10,
  "Summary": "Brief summary"
}"""

class ScreenshotManager:
    def __init__(self):
        self.screenshot_folder = "./screenshots"
        os.makedirs(self.screenshot_folder, exist_ok=True)
        self.sct = mss.mss()
        self.current_trade_id = None
        self.screenshots = {}
        self.crop_regions = {}
        self.crop_mode = False
        
    def start_new_trade(self):
        self.current_trade_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshots = {}
        return self.current_trade_id
    
    def set_crop_region(self, monitor_num, x1, y1, x2, y2):
        self.crop_regions[monitor_num] = (x1, y1, x2, y2)
    
    def capture(self, stage, monitor_num, use_crop=False):
        if not self.current_trade_id:
            self.start_new_trade()
        
        timestamp = datetime.now().strftime("%H%M%S")
        
        if monitor_num == 0:
            screenshot = self.sct.grab(self.sct.monitors[0])
        else:
            screenshot = self.sct.grab(self.sct.monitors[monitor_num])
        
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Apply crop if enabled and region defined
        if use_crop and monitor_num in self.crop_regions:
            x1, y1, x2, y2 = self.crop_regions[monitor_num]
            img = img.crop((x1, y1, x2, y2))
        
        filename = f"Trade_{self.current_trade_id}_{stage}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_folder, filename)
        img.save(filepath)
        
        self.screenshots[stage] = {
            "path": filepath,
            "timestamp": datetime.now().isoformat()
        }
        return filepath
    
    def get_all_screenshots(self):
        return self.screenshots

class TradingJournalFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Journal Pro - Final")
        self.root.geometry("1100x800")
        
        self.screenshot_mgr = ScreenshotManager()
        self.selected_monitor = tk.IntVar(value=0)
        self.crop_mode = tk.BooleanVar(value=False)
        self.checklist_items = {}
        
        # Main container
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Checklist
        left_panel = tk.Frame(main_frame, width=250, bg="#f5f5f5", relief="ridge", bd=2)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Checklist title
        tk.Label(left_panel, text="Trade Checklist", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(pady=10)
        
        # Checklist items
        checklist_data = [
            ("Level Types", "LIS/AVWAP/etc"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience Score", "1-10 [1-3=Strong]"),
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("Entry Direction", "Buy/Sell"),
            ("5m Form", "Perfect→Poor"),
            ("M1 Confirm", "Yes/No"),
            ("Screenshots", "Captured")
        ]
        
        for item, hint in checklist_data:
            frame = tk.Frame(left_panel, bg="#f5f5f5")
            frame.pack(fill="x", padx=10, pady=4)
            
            var = tk.BooleanVar()
            self.checklist_items[item] = var
            
            # Checkbox on left
            cb = tk.Checkbutton(frame, variable=var, bg="#f5f5f5")
            cb.pack(side="left", anchor="n", pady=2)
            
            # Text container
            text_frame = tk.Frame(frame, bg="#f5f5f5")
            text_frame.pack(side="left", fill="x", expand=True)
            
            # Title (bigger)
            tk.Label(text_frame, text=item, font=("Arial", 10, "bold"), bg="#f5f5f5", anchor="w").pack(anchor="w")
            # Hint underneath
            tk.Label(text_frame, text=hint, font=("Arial", 8), fg="#666", bg="#f5f5f5", anchor="w").pack(anchor="w")
        
        # Reminders section
        tk.Label(left_panel, text="\nReminders:", font=("Arial", 10, "bold"), bg="#f5f5f5").pack(pady=(15, 5))
        reminders = [
            "• Impulse 1-3 = Strong",
            "• Impulse 7-10 = Weak",
            "• Patience 1-3 = Good",
            "• Patience 7-10 = Chased"
        ]
        for reminder in reminders:
            tk.Label(left_panel, text=reminder, font=("Arial", 8), fg="#333", bg="#f5f5f5", anchor="w").pack(padx=10)
        
        # Right panel - Main content
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side="left", fill="both", expand=True)
        
        # Stats display
        stats = get_stats()
        stats_frame = tk.Frame(right_panel, bg="#e3f2fd", pady=8)
        stats_frame.pack(fill="x")
        
        self.stats_label = tk.Label(
            stats_frame,
            text=f"Requests: Today {stats['today_requests']} | Month {stats['month_requests']} | Total {stats['total_requests']}\n"
                 f"Tokens: Today {stats['today_tokens']:,} | Month {stats['month_tokens']:,} | Total {stats['total_tokens']:,}",
            font=("Arial", 9),
            bg="#e3f2fd",
            fg="#1976d2"
        )
        self.stats_label.pack()
        
        # Monitor & Screenshot controls
        control_frame = tk.Frame(right_panel)
        control_frame.pack(pady=8)
        
        # Monitor selection
        tk.Label(control_frame, text="Monitor:", font=("Arial", 10)).grid(row=0, column=0, padx=5)
        for i in range(5):
            label = "All" if i == 0 else str(i)
            tk.Radiobutton(control_frame, text=label, variable=self.selected_monitor, value=i, font=("Arial", 9)).grid(row=0, column=i+1, padx=2)
        
        # Crop mode toggle
        tk.Checkbutton(control_frame, text="Crop Chart Only", variable=self.crop_mode, font=("Arial", 9)).grid(row=0, column=6, padx=10)
        tk.Button(control_frame, text="Define Crop", command=self.define_crop_region, font=("Arial", 8), bg="#000000", fg="white").grid(row=0, column=7, padx=5)
        
        # Screenshot buttons
        screenshot_frame = tk.Frame(right_panel)
        screenshot_frame.pack(pady=8)
        
        stages = [
            ("Pre-Entry", "pre_entry", "#9C27B0"),
            ("Entry", "entry", "#4CAF50"),
            ("During", "during", "#FF9800"),
            ("Close", "close", "#F44336"),
            ("Post-Close", "post_close", "#424242")
        ]
        
        for label, stage, color in stages:
            tk.Button(
                screenshot_frame,
                text=label,
                command=lambda s=stage: self.take_screenshot(s),
                font=("Arial", 9),
                bg=color,
                fg="white",
                padx=8,
                pady=4
            ).pack(side="left", padx=3)
        
        self.screenshot_status = tk.Label(screenshot_frame, text="", font=("Arial", 8), fg="#666")
        self.screenshot_status.pack(side="left", padx=10)
        
        # Instructions
        tk.Label(right_panel, text="Dictate with Zavi (Right Ctrl), then say 'save trade'", font=("Arial", 10)).pack(pady=5)
        
        # Text area
        self.text_area = scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11))
        self.text_area.pack(pady=8)
        self.text_area.bind('<KeyRelease>', self.check_text_and_update_checklist)
        
        # Action buttons
        button_frame = tk.Frame(right_panel)
        button_frame.pack(pady=8)
        
        self.save_btn = tk.Button(button_frame, text="Save Trade", command=self.save_trade, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8)
        self.save_btn.pack(side="left", padx=5)
        
        tk.Button(button_frame, text="Edit Last Trade", command=self.edit_last_trade, font=("Arial", 10), bg="#2196F3", fg="white", padx=15, pady=8).pack(side="left", padx=5)
        
        # Status
        self.status_label = tk.Label(right_panel, text="Ready...", font=("Arial", 9), fg="green")
        self.status_label.pack(pady=5)
    
    def define_crop_region(self):
        monitor = self.selected_monitor.get()
        if monitor == 0:
            messagebox.showinfo("Info", "Please select a specific monitor (1-4) to define crop region")
            return
        
        messagebox.showinfo("Crop Region", "Click OK, then:\n1. Click top-left corner of chart\n2. Click bottom-right corner of chart")
        
        # Simple crop region capture (you'll need to implement click capture)
        # For now, placeholder
        self.status_label.config(text="Crop region feature - coming soon!", fg="blue")
    
    def check_text_and_update_checklist(self, event=None):
        text = self.text_area.get("1.0", tk.END).strip().lower()
        
        # Auto-check checklist items based on text
        checks = {
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"]),
            "M5 Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            : any(word in text for word in ["lis", "avwap", "level", "upper", "lower"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Patience": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "Why trade?": len(text) > 20
        }
        
        for item, checked in checks.items():
            if item in self.checklist_items:
                self.checklist_items[item].set(checked)
        
        # Check for "save trade" trigger
        if "save trade" in text:
            self.save_trade()
    
    def take_screenshot(self, stage):
        monitor = self.selected_monitor.get()
        use_crop = self.crop_mode.get()
        
        filepath = self.screenshot_mgr.capture(stage, monitor, use_crop)
        
        stage_names = {
            "pre_entry": "Pre-Entry",
            "entry": "Entry",
            "during": "During",
            "close": "Close",
            "post_close": "Post-Close"
        }
        
        captured = [stage_names[s] for s in self.screenshot_mgr.screenshots.keys()]
        self.screenshot_status.config(text=f"✓ {', '.join(captured)}", fg="green")
        self.status_label.config(text=f"Screenshot: {stage_names[stage]}", fg="blue")
    
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
    
    def edit_last_trade(self):
        self.status_label.config(text="Edit last trade - feature coming soon!", fg="blue")
    
    def process_trade(self, text):
        try:
            # Use vocabulary trainer to enhance text
            vocab = load_vocab()
            
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
            
            # Build properties
            properties = {
                "Name": {"title": [{"text": {"content": f"Trade - {datetime.now().strftime('%H:%M')}"}}]},
                "Transcript": {"rich_text": [{"text": {"content": text}}]},
                "Date": {"date": {"start": datetime.now().isoformat()}}
            }
            
            if "M5_Pattern" in data and isinstance(data["M5_Pattern"], list):
                properties["M5_Pattern"] = {"multi_select": [{"name": pattern} for pattern in data["M5_Pattern"]]}
            if "M1_Confirm" in data:
                properties["M1_Confirm"] = {"select": {"name": data["M1_Confirm"]}}
            if "M5_Form" in data:
                properties["M5_Form"] = {"select": {"name": data["M5_Form"]}}
            
            if "Entry_Direction" in data:
                properties["Entry_Direction"] = {"select": {"name": data["Entry_Direction"]}}
            if "Emotions" in data:
                properties["Emotions"] = {"select": {"name": data["Emotions"]}}
            if "Impulse" in data:
                properties["Impulse"] = {"number": int(data["Impulse"])}
            if "Patience_Score" in data:
                properties["Patience_Score"] = {"number": int(data["Patience_Score"])}
            
            if "Summary" in data:
                properties["AI_Analysis"] = {"rich_text": [{"text": {"content": data["Summary"]}}]}
            
            # Add screenshot timestamps
            screenshots = self.screenshot_mgr.get_all_screenshots()
            if "pre_entry" in screenshots:
                properties["Screenshot_PreEntry_Time"] = {"date": {"start": screenshots["pre_entry"]["timestamp"]}}
            if "entry" in screenshots:
                properties["Screenshot_Entry_Time"] = {"date": {"start": screenshots["entry"]["timestamp"]}}
            if "during" in screenshots:
                properties["Screenshot_During_Time"] = {"date": {"start": screenshots["during"]["timestamp"]}}
            if "close" in screenshots:
                properties["Screenshot_Close_Time"] = {"date": {"start": screenshots["close"]["timestamp"]}}
            if "post_close" in screenshots:
                properties["Screenshot_PostClose_Time"] = {"date": {"start": screenshots["post_close"]["timestamp"]}}
            
            notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
            
            stats = get_stats()
            screenshot_count = len(screenshots)
            
            self.root.after(0, self.update_success, usage.total_tokens, stats, screenshot_count)
            
        except Exception as e:
            self.root.after(0, self.update_error, str(e))
    
    def update_success(self, tokens, stats, screenshot_count):
        self.status_label.config(text=f"SUCCESS! ({tokens} tokens, {screenshot_count} screenshots)", fg="green")
        
        self.stats_label.config(
            text=f"Requests: Today {stats['today_requests']} | Month {stats['month_requests']} | Total {stats['total_requests']}\n"
                 f"Tokens: Today {stats['today_tokens']:,} | Month {stats['month_tokens']:,} | Total {stats['total_tokens']:,}"
        )
        
        self.text_area.delete("1.0", tk.END)
        self.save_btn.config(state="normal")
        
        # Reset checklist
        for var in self.checklist_items.values():
            var.set(False)
        
        # Reset for next trade
        self.screenshot_mgr.start_new_trade()
        self.screenshot_status.config(text="", fg="#666")
    
    def update_error(self, error):
        self.status_label.config(text=f"ERROR: {error}", fg="red")
        self.save_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingJournalFinal(root)
    root.mainloop()
