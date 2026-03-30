import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import threading
import json
import os
import csv
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq
from notion_client import Client
from api_tracker import log_request, get_stats
from vocabulary_trainer import find_match, add_phrase, load_vocab
from screenshot_upload_manager import add_screenshots_as_blocks
from draggable_checklist import DraggableChecklist
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
- Five_M_Form: Perfect, Well-Formed, Decent, Questionable, Poor
- Entry_Direction: Buy, Sell
- Emotions: Zen, Anxious, FOMO, Revenge
- Impulse: 1-10 (number)
- Patience_Score: 1-10 (number, 1-3=strong patience, 7-10=weak patience/impatient)

NATURAL LANGUAGE RECOGNITION:
- "5 minute form", "5m form", "five minute form", "candle form", "pattern form" → Five_M_Form
- "perfect", "well formed", "decent", "questionable", "poor" → Five_M_Form values
- "FOMO" can be misheard as "foam", "foam wall", "formal" - always interpret as FOMO emotion
- "one" or "1" after "patience" = Patience_Score: 1
- "engulfing" without bullish/bearish → check Entry_Direction to determine
- Numbers need context: "impulse 7" vs "patience 4"
- When user says they were patient or "give myself a one/two/three" = low Patience_Score (1-3 = strong patience)

Return JSON only with fields found:
{
  "M5_Pattern": ["Hammer", "Shooting Star", "Bullish Engulfing", "Bearish Engulfing"],
  "M1_Confirm": "Yes|No",
  "Five_M_Form": "Perfect|Well-Formed|Decent|Questionable|Poor",
  "Entry_Direction": "Buy|Sell",
  "Emotions": "Zen|Anxious|FOMO|Revenge",
  "Impulse": 1-10,
  "Patience_Score": 1-10,
  "Summary": "Brief summary"
}"""

class ScreenshotManager:
    def __init__(self):
        self.screenshot_folder = r"D:\MyPythonProjects_2\TRADING JOURNAL WITH VOICE\screenshots"
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
        
        # Get the monitor to capture
        monitor = self.sct.monitors[monitor_num]
        screenshot = self.sct.grab(monitor)
        
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Apply crop if enabled and region defined
        if use_crop and monitor_num in self.crop_regions:
            x1, y1, x2, y2 = self.crop_regions[monitor_num]
            
            # Convert absolute screen coordinates to monitor-relative coordinates
            crop_x1 = x1 - monitor["left"]
            crop_y1 = y1 - monitor["top"]
            crop_x2 = x2 - monitor["left"]
            crop_y2 = y2 - monitor["top"]
            
            # Ensure coordinates are within bounds
            crop_x1 = max(0, crop_x1)
            crop_y1 = max(0, crop_y1)
            crop_x2 = min(monitor["width"], crop_x2)
            crop_y2 = min(monitor["height"], crop_y2)
            
            img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        
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
        # Map numeric values to method names
        upload_map = {"1": "local", "2": "cloudinary", "3": "notion_blocks"}
        upload_value = os.getenv("SCREENSHOT_UPLOAD_METHOD", "1")
        self.upload_method = tk.StringVar(value=upload_map.get(upload_value, "local"))
        self.checklist_items = {}
        
        # Track which stage button is in crop mode
        self.crop_stage = None
        self.stage_buttons = {}
        
        # Main container
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Checklist
        left_panel = tk.Frame(main_frame, width=250, bg="#f5f5f5", relief="ridge", bd=2)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Checklist title
        tk.Label(left_panel, text="Trade Checklist", font=("Arial", 12, "bold"), bg="#f5f5f5").pack(pady=10)
        
        # Checklist items (draggable)
        checklist_data = [
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("5m Form", "Perfect->Poor"),
            ("Level Types", "LIS/AVWAP/etc"),
            ("M1 Confirm", "Yes/No"),
            ("Entry Direction", "Buy/Sell"),
            ("Patience Score", "1-10 [1-3=Strong]"),
            ("Screenshots", "Captured")
        ]
        
        # Create draggable checklist
        self.draggable_checklist = DraggableChecklist(left_panel, bg="#f5f5f5")
        self.draggable_checklist.pack(fill="both", expand=True)
        
        for item, hint in checklist_data:
            var = tk.BooleanVar()
            self.checklist_items[item] = var
            self.draggable_checklist.add_item(item, hint, var)
        
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
        
        # Vocabulary warning banner container (always exists, but may be empty)
        self.warning_banner_container = tk.Frame(right_panel)
        self.warning_banner_container.pack(fill="x", pady=(5, 0))
        
        # Initial check for unknown phrases
        self.refresh_warning_banner()
        
        # Periodically check for updates (every 2 seconds)
        self.check_warning_banner_updates()
        
        # Monitor & Screenshot controls
        control_frame = tk.Frame(right_panel)
        control_frame.pack(pady=8)
        
        # Monitor selection
        tk.Label(control_frame, text="Monitor:", font=("Arial", 10)).grid(row=0, column=0, padx=5)
        for i in range(5):
            label = "All" if i == 0 else str(i)
            tk.Radiobutton(control_frame, text=label, variable=self.selected_monitor, value=i, font=("Arial", 9)).grid(row=0, column=i+1, padx=2)
        
        # Define Crop button removed - now integrated into screenshot buttons
        
        # Clear Crop button
        tk.Button(control_frame, text="Clear Crop", command=self.clear_crop_region, font=("Arial", 8), bg="#666666", fg="white").grid(row=0, column=7, padx=5)
        
        # Upload method dropdown
        tk.Label(control_frame, text="Upload:", font=("Arial", 9)).grid(row=0, column=8, padx=(15, 5))
        
        # Store actual methods internally (can be multiple)
        self.actual_upload_methods = tk.StringVar(value="local,cloudinary")  # Default: Local + Cloudinary
        
        upload_dropdown = ttk.Combobox(control_frame, textvariable=self.upload_method, 
                                       values=["1 - Local Only", 
                                               "2 - Cloudinary Only", 
                                               "3 - Notion Blocks Only",
                                               "1+2 - Local + Cloudinary",
                                               "1+3 - Local + Notion Blocks",
                                               "2+3 - Cloudinary + Notion Blocks",
                                               "All - Local + Cloudinary + Notion"], 
                                       width=22, state="readonly", font=("Arial", 9))
        upload_dropdown.grid(row=0, column=9, padx=5)
        
        # Map display values back to method names when saving
        def on_upload_change(event):
            display_value = self.upload_method.get()
            method_map = {
                "1 - Local Only": "local",
                "2 - Cloudinary Only": "cloudinary",
                "3 - Notion Blocks Only": "notion_blocks",
                "1+2 - Local + Cloudinary": "local,cloudinary",
                "1+3 - Local + Notion Blocks": "local,notion_blocks",
                "2+3 - Cloudinary + Notion Blocks": "cloudinary,notion_blocks",
                "All - Local + Cloudinary + Notion": "local,cloudinary,notion_blocks"
            }
            self.actual_upload_methods.set(method_map.get(display_value, "local,cloudinary"))
        
        upload_dropdown.bind("<<ComboboxSelected>>", on_upload_change)
        
        # Set initial display value
        self.upload_method.set("1+2 - Local + Cloudinary")
        self.actual_upload_methods.set("local,cloudinary")  # Initialize to Local + Cloudinary
        
        # Folder chooser button
        tk.Button(control_frame, text="📁 Save Folder", command=self.choose_screenshot_folder, font=("Arial", 8), bg="#607D8B", fg="white").grid(row=0, column=10, padx=5)
        
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
            btn = tk.Button(
                screenshot_frame,
                text=label,
                command=lambda s=stage: self.take_screenshot(s),
                font=("Arial", 9),
                bg=color,
                fg="white",
                padx=8,
                pady=4
            )
            btn.pack(side="left", padx=3)
            self.stage_buttons[stage] = {"button": btn, "original_color": color, "original_text": label}
        
        self.screenshot_status = tk.Label(screenshot_frame, text="", font=("Arial", 8), fg="#666")
        self.screenshot_status.pack(side="left", padx=10)
        
        # Instructions
        tk.Label(right_panel, text="Dictate with Zavi (Right Ctrl), then say 'save trade'", font=("Arial", 10)).pack(pady=5)
        
        # Text area
        self.text_area = scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11), wrap="word")
        self.text_area.pack(pady=8)
        self.text_area.bind('<KeyRelease>', self.check_text_and_update_checklist)
        
        # Action buttons
        button_frame = tk.Frame(right_panel)
        button_frame.pack(pady=8)
        
        self.save_btn = tk.Button(button_frame, text="Save Trade", command=self.save_trade, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8)
        self.save_btn.pack(side="left", padx=5)
        
        tk.Button(button_frame, text="Edit Last Trade", command=self.edit_last_trade, font=("Arial", 10), bg="#2196F3", fg="white", padx=15, pady=8).pack(side="left", padx=5)
        
        # Status
        self.status_label = tk.Text(right_panel, height=2, font=("Arial", 9), fg="green", bg="#f0f0f0", relief="flat", wrap="word")
        self.status_label.insert("1.0", "Ready...")
        self.status_label.config(state="disabled")
        self.status_label.pack(pady=5)
    
    def clear_crop_region(self):
        monitor = self.selected_monitor.get()
        if monitor in self.screenshot_mgr.crop_regions:
            del self.screenshot_mgr.crop_regions[monitor]
            self.status_label.config(state="normal", fg="orange")
            self.status_label.delete("1.0", "end")
            self.status_label.insert("1.0", f"✓ Crop region cleared for Monitor {monitor}")
            self.status_label.config(state="disabled")
        else:
            self.status_label.config(state="normal", fg="red")
            self.status_label.delete("1.0", "end")
            self.status_label.insert("1.0", f"No crop region defined for Monitor {monitor}")
            self.status_label.config(state="disabled")
    
    def define_crop_region_and_capture(self, stage):
        """Define crop region and automatically capture screenshot on release"""
        try:
            # Create transparent overlay window spanning ALL monitors
            crop_window = tk.Toplevel(self.root)
            crop_window.withdraw()  # Hide initially
            crop_window.attributes('-topmost', True)
            crop_window.attributes('-alpha', 0.2)  # Lighter/more transparent
            crop_window.config(bg='black')
            crop_window.overrideredirect(True)  # Remove window decorations
            
            # Get total screen dimensions across all monitors
            import ctypes
            user32 = ctypes.windll.user32
            total_width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            total_height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            left = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            top = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            
            # Position window to cover all monitors
            crop_window.geometry(f"{total_width}x{total_height}+{left}+{top}")
            
            canvas = tk.Canvas(crop_window, cursor="cross", bg='black', highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            
            crop_window.deiconify()  # Show window
            
            rect = {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0, 'id': None}
            
            def on_press(event):
                rect['x1'], rect['y1'] = event.x, event.y
                if rect['id']:
                    canvas.delete(rect['id'])
                rect['id'] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=3)
            
            def on_drag(event):
                if rect['id']:
                    canvas.coords(rect['id'], rect['x1'], rect['y1'], event.x, event.y)
            
            def on_release(event):
                rect['x2'], rect['y2'] = event.x, event.y
                x1, y1, x2, y2 = min(rect['x1'], rect['x2']), min(rect['y1'], rect['y2']), max(rect['x1'], rect['x2']), max(rect['y1'], rect['y2'])
                
                # Convert canvas coordinates to absolute screen coordinates
                abs_x1 = x1 + left
                abs_y1 = y1 + top
                abs_x2 = x2 + left
                abs_y2 = y2 + top
                
                # Auto-detect which monitor this region is on
                center_x = (abs_x1 + abs_x2) / 2
                center_y = (abs_y1 + abs_y2) / 2
                
                monitors = self.screenshot_mgr.sct.monitors[1:]  # Skip monitor 0 (all monitors)
                detected_monitor = None
                for i, mon in enumerate(monitors, start=1):
                    if (mon["left"] <= center_x < mon["left"] + mon["width"] and
                        mon["top"] <= center_y < mon["top"] + mon["height"]):
                        detected_monitor = i
                        break
                
                if detected_monitor:
                    # Auto-select the detected monitor
                    self.selected_monitor.set(detected_monitor)
                    
                    # Save the crop region
                    self.screenshot_mgr.set_crop_region(detected_monitor, abs_x1, abs_y1, abs_x2, abs_y2)
                    crop_window.destroy()
                    
                    # Automatically capture screenshot with the crop
                    self.capture_screenshot_with_crop(stage, detected_monitor)
                else:
                    crop_window.destroy()
                    messagebox.showerror("Error", "Could not detect monitor. Draw region within a single monitor.")
                    # Reset button appearance
                    btn_info = self.stage_buttons[stage]
                    btn_info["button"].config(
                        bg=btn_info["original_color"],
                        text=btn_info["original_text"]
                    )
                    self.crop_stage = None
            
            canvas.bind("<Button-1>", on_press)
            canvas.bind("<B1-Motion>", on_drag)
            canvas.bind("<ButtonRelease-1>", on_release)
            crop_window.bind("<Escape>", lambda e: (crop_window.destroy(), self.reset_crop_button(stage)))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to define crop region: {str(e)}")
            self.reset_crop_button(stage)
    
    def reset_crop_button(self, stage):
        """Reset button appearance after crop is cancelled"""
        if stage in self.stage_buttons:
            btn_info = self.stage_buttons[stage]
            btn_info["button"].config(
                bg=btn_info["original_color"],
                text=btn_info["original_text"]
            )
        self.crop_stage = None
    
    def capture_screenshot_with_crop(self, stage, monitor):
        """Capture screenshot after crop region is defined"""
        # Reset button appearance
        btn_info = self.stage_buttons[stage]
        btn_info["button"].config(
            bg=btn_info["original_color"],
            text=btn_info["original_text"]
        )
        self.crop_stage = None
        
        # Capture screenshot with crop
        use_crop = monitor in self.screenshot_mgr.crop_regions
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
        self.status_label.config(state="normal", fg="blue")
        self.status_label.delete("1.0", "end")
        crop_info = f" (cropped)" if use_crop else ""
        self.status_label.insert("1.0", f"Screenshot: {stage_names[stage]} - Monitor {monitor}{crop_info}")
        self.status_label.config(state="disabled")
    
    def choose_screenshot_folder(self):
        folder = filedialog.askdirectory(title="Choose Screenshot Save Folder", initialdir=self.screenshot_mgr.screenshot_folder)
        if folder:
            self.screenshot_mgr.screenshot_folder = folder
            messagebox.showinfo("Folder Updated", f"Screenshots will be saved to:\n{folder}")
    
    def open_vocabulary_trainer(self):
        """Open vocabulary trainer window to categorize unknown phrases"""
        try:
            import subprocess
            import sys
            # Try to run vocabulary_trainer.py if it exists
            trainer_path = os.path.join(os.path.dirname(__file__), "vocabulary_trainer_ui.py")
            if os.path.exists(trainer_path):
                subprocess.Popen([sys.executable, trainer_path])
            else:
                messagebox.showinfo("Vocabulary Trainer", 
                    "Vocabulary trainer UI not found.\nPlease manually edit vocabulary_training.json")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open vocabulary trainer: {str(e)}")
    
    def check_text_and_update_checklist(self, event=None):
        text = self.text_area.get("1.0", tk.END).strip().lower()
        
        # Auto-check checklist items based on text
        checks = {
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            "Level Types": any(word in text for word in ["lis", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "Patience Score": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "Screenshots": len(self.screenshot_mgr.screenshots) > 0
        }
        
        for item, checked in checks.items():
            if item in self.checklist_items:
                self.checklist_items[item].set(checked)
        
        # Check for "save trade" trigger
        if "save trade" in text:
            self.save_trade()
    
    def take_screenshot(self, stage):
        # Reset any other button that was in crop mode
        if self.crop_stage:
            old_btn_info = self.stage_buttons[self.crop_stage]
            old_btn_info["button"].config(
                bg=old_btn_info["original_color"],
                text=old_btn_info["original_text"]
            )
        
        # Set this button to crop mode
        self.crop_stage = stage
        btn_info = self.stage_buttons[stage]
        btn_info["button"].config(
            bg="#FF6B6B",
            text=f"📐 {btn_info['original_text']}"
        )
        
        # Open crop definition window with callback to capture screenshot
        self.define_crop_region_and_capture(stage)
        
        # Update status
        self.status_label.config(state="normal", fg="orange")
        self.status_label.delete("1.0", "end")
        self.status_label.insert("1.0", f"Draw crop region for {btn_info['original_text']} screenshot...")
        self.status_label.config(state="disabled")
    
    def save_trade(self):
        text = self.text_area.get("1.0", tk.END).strip()
        text = text.replace("save trade", "").replace("Save trade", "").strip()
        
        if not text:
            self.status_label.config(state="normal", fg="red")
            self.status_label.delete("1.0", "end")
            self.status_label.insert("1.0", f"No text to save!")
            self.status_label.config(state="disabled")
            return
        
        self.status_label.config(state="normal", fg="orange")
        self.status_label.delete("1.0", "end")
        self.status_label.insert("1.0", f"Processing...")
        self.status_label.config(state="disabled")
        self.save_btn.config(state="disabled")
        
        thread = threading.Thread(target=self.process_trade, args=(text,))
        thread.start()
    
    def edit_last_trade(self):
        self.status_label.config(state="normal", fg="blue")
        self.status_label.delete("1.0", "end")
        self.status_label.insert("1.0", f"Edit last trade - feature coming soon!")
        self.status_label.config(state="disabled")
    
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
                "Name": {"title": [{"text": {"content": f"Trade - {datetime.now().strftime('%H:%M:%S')}"}}]},
                "Transcript": {"rich_text": [{"text": {"content": text}}]},
                "Date": {"date": {"start": datetime.now().isoformat()}}
            }
            
            if "M5_Pattern" in data and isinstance(data["M5_Pattern"], list):
                properties["M5_Pattern"] = {"multi_select": [{"name": pattern} for pattern in data["M5_Pattern"]]}
            if "M1_Confirm" in data:
                properties["M1_Confirm"] = {"select": {"name": data["M1_Confirm"]}}
            if "Five_M_Form" in data:
                properties["5m Form"] = {"select": {"name": data["Five_M_Form"]}}
            
            if "Entry_Direction" in data:
                properties["Entry_Direction"] = {"select": {"name": data["Entry_Direction"]}}
            if "Emotions" in data:
                properties["Emotions"] = {"select": {"name": data["Emotions"]}}
            if "Impulse" in data and data["Impulse"] is not None:
                properties["Impulse"] = {"number": int(data["Impulse"])}
            if "Patience_Score" in data and data["Patience_Score"] is not None:
                properties["Patience_Score"] = {"number": int(data["Patience_Score"])}
            
            if "Summary" in data:
                properties["AI_Analysis"] = {"rich_text": [{"text": {"content": data["Summary"]}}]}
            
            # Get screenshots
            screenshots = self.screenshot_mgr.get_all_screenshots()
            
            # Create Notion page
            page = notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
            page_id = page['id']
            page_url = page['url']
            
            # Upload screenshots based on selected method(s)
            if screenshots:
                upload_methods = self.actual_upload_methods.get().split(',')
                print(f"DEBUG: Upload methods selected: {upload_methods}")
                print(f"DEBUG: Screenshots to upload: {list(screenshots.keys())}")
                
                all_uploaded_urls = {}
                
                # Process each method
                for method in upload_methods:
                    method = method.strip()
                    print(f"DEBUG: Processing method: {method}")
                    
                    uploaded_urls = add_screenshots_as_blocks(notion, page_id, screenshots, method)
                    
                    # Merge URLs from all methods (Cloudinary URLs take priority)
                    if uploaded_urls:
                        for stage_name, url in uploaded_urls.items():
                            # Only add if not already present, or if this is a Cloudinary URL (http)
                            if stage_name not in all_uploaded_urls or url.startswith("http"):
                                all_uploaded_urls[stage_name] = url
                
                # If Cloudinary URLs or local paths were returned, update the Screenshots property with text links
                if all_uploaded_urls:
                    # Color mapping for stage names (matches button colors)
                    stage_colors = {
                        "Pre-Entry": "purple_background",
                        "Entry": "green_background",
                        "During": "orange_background",
                        "Close": "red_background",
                        "Post-Close": "gray_background"  # Black background with white text
                    }
                    
                    # Create rich text with clickable colored links (e.g., "Entry | Close | Pre-Entry")
                    links_text = []
                    for stage_name, url in all_uploaded_urls.items():
                        if links_text:
                            links_text.append({"type": "text", "text": {"content": " | "}})
                        
                        # Add colored link with background
                        color = stage_colors.get(stage_name, "default")
                        
                        # For Cloudinary URLs, make them clickable; for local paths, just show text
                        if url.startswith("http"):
                            links_text.append({
                                "type": "text",
                                "text": {"content": stage_name, "link": {"url": url}},
                                "annotations": {"color": color}
                            })
                        else:
                            # Local path - just colored text, no link
                            links_text.append({
                                "type": "text",
                                "text": {"content": stage_name},
                                "annotations": {"color": color}
                            })
                    
                    # Update the page with the Screenshots property as rich text
                    notion.pages.update(
                        page_id=page_id,
                        properties={"Screenshots": {"rich_text": links_text}}
                    )
                    print(f"Added {len(all_uploaded_urls)} screenshot links to Screenshots column")
            
            # Save to CSV with Media/Link column
            self.save_to_csv(data, page_url, text)
            
            stats = get_stats()
            screenshot_count = len(screenshots)
            
            self.root.after(0, self.update_success, usage.total_tokens, stats, screenshot_count)
            
        except Exception as e:
            self.root.after(0, self.update_error, str(e))
    
    def update_success(self, tokens, stats, screenshot_count):
        self.status_label.config(state="normal", fg="green")
        self.status_label.delete("1.0", "end")
        self.status_label.insert("1.0", f"SUCCESS! ({tokens} tokens, {screenshot_count} screenshots)")
        self.status_label.config(state="disabled")
        
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
        self.status_label.config(state="normal", fg="red")
        self.status_label.delete("1.0", "end")
        self.status_label.insert("1.0", f"ERROR: {error}")
        self.status_label.config(state="disabled")
        self.save_btn.config(state="normal")
    
    def save_to_csv(self, data, page_url, transcript):
        """Save trade data to CSV with Media/Link column"""
        csv_file = "trading_journal.csv"
        file_exists = os.path.exists(csv_file)
        
        # Prepare row data
        row = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "M5_Pattern": ", ".join(data.get("M5_Pattern", [])) if isinstance(data.get("M5_Pattern"), list) else "",
            "M1_Confirm": data.get("M1_Confirm", ""),
            "5m_Form": data.get("Five_M_Form", ""),
            "Entry_Direction": data.get("Entry_Direction", ""),
            "Emotions": data.get("Emotions", ""),
            "Impulse": data.get("Impulse", ""),
            "Patience_Score": data.get("Patience_Score", ""),
            "Summary": data.get("Summary", ""),
            "Transcript": transcript,
            "Media/Link": page_url
        }
        
        # Write to CSV
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    
    def open_vocabulary_trainer(self):
        """Open vocabulary trainer window"""
        try:
            import subprocess
            import sys
            # Launch vocabulary trainer in a separate process
            subprocess.Popen([sys.executable, "vocabulary_trainer_ui.py"])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open vocabulary trainer: {e}")
    
    def refresh_warning_banner(self):
        """Refresh the warning banner based on current unknown phrases"""
        # Clear existing content
        for widget in self.warning_banner_container.winfo_children():
            widget.destroy()
        
        try:
            from vocabulary_trainer import has_unknown_phrases, get_unknown_phrases
            if has_unknown_phrases():
                unknown_count = len(get_unknown_phrases())
                warning_frame = tk.Frame(self.warning_banner_container, bg="#FFF3CD", pady=8, relief="solid", bd=1)
                warning_frame.pack(fill="x")
                
                warning_text = f"⚠️ {unknown_count} unknown phrase{'s' if unknown_count != 1 else ''} need{'s' if unknown_count == 1 else ''} categorization"
                tk.Label(
                    warning_frame,
                    text=warning_text,
                    font=("Arial", 10, "bold"),
                    bg="#FFF3CD",
                    fg="#856404"
                ).pack(side="left", padx=10)
                
                tk.Button(
                    warning_frame,
                    text="Review Now",
                    command=self.open_vocabulary_trainer,
                    font=("Arial", 9),
                    bg="#FFC107",
                    fg="#000",
                    padx=10
                ).pack(side="right", padx=10)
        except ImportError:
            pass  # vocabulary_trainer not available
    
    def check_warning_banner_updates(self):
        """Periodically check if warning banner needs updating"""
        self.refresh_warning_banner()
        # Check again in 2 seconds
        self.root.after(2000, self.check_warning_banner_updates)

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingJournalFinal(root)
    root.mainloop()
