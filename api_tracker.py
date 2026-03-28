import json
import os
from datetime import datetime

TRACKER_FILE = "api_tracker.json"

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"daily": {}, "monthly": {}, "total_requests": 0, "total_tokens": 0}

def save_tracker(data):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_request(prompt_tokens, completion_tokens):
    tracker = load_tracker()
    total = prompt_tokens + completion_tokens
    
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    
    # Update daily
    if today not in tracker["daily"]:
        tracker["daily"][today] = {"requests": 0, "tokens": 0}
    tracker["daily"][today]["requests"] += 1
    tracker["daily"][today]["tokens"] += total
    
    # Update monthly
    if month not in tracker["monthly"]:
        tracker["monthly"][month] = {"requests": 0, "tokens": 0}
    tracker["monthly"][month]["requests"] += 1
    tracker["monthly"][month]["tokens"] += total
    
    # Update totals
    tracker["total_requests"] += 1
    tracker["total_tokens"] += total
    
    save_tracker(tracker)
    return tracker

def get_stats():
    tracker = load_tracker()
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    
    daily = tracker["daily"].get(today, {"requests": 0, "tokens": 0})
    monthly = tracker["monthly"].get(month, {"requests": 0, "tokens": 0})
    
    return {
        "today_requests": daily["requests"],
        "today_tokens": daily["tokens"],
        "month_requests": monthly["requests"],
        "month_tokens": monthly["tokens"],
        "total_requests": tracker["total_requests"],
        "total_tokens": tracker["total_tokens"]
    }
