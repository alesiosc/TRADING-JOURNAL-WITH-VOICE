import json
import os
from datetime import datetime

TOKEN_LOG_FILE = "token_usage.json"

def load_token_log():
    if os.path.exists(TOKEN_LOG_FILE):
        with open(TOKEN_LOG_FILE, 'r') as f:
            return json.load(f)
    return {"daily": {}, "monthly": {}, "total": 0}

def save_token_log(log):
    with open(TOKEN_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def log_tokens(prompt_tokens, completion_tokens):
    log = load_token_log()
    total = prompt_tokens + completion_tokens
    
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    
    # Update daily
    if today not in log["daily"]:
        log["daily"][today] = {"prompt": 0, "completion": 0, "total": 0}
    log["daily"][today]["prompt"] += prompt_tokens
    log["daily"][today]["completion"] += completion_tokens
    log["daily"][today]["total"] += total
    
    # Update monthly
    if month not in log["monthly"]:
        log["monthly"][month] = {"prompt": 0, "completion": 0, "total": 0}
    log["monthly"][month]["prompt"] += prompt_tokens
    log["monthly"][month]["completion"] += completion_tokens
    log["monthly"][month]["total"] += total
    
    # Update total
    log["total"] += total
    
    save_token_log(log)
    return log

def get_usage_summary():
    log = load_token_log()
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    
    daily_usage = log["daily"].get(today, {"total": 0})
    monthly_usage = log["monthly"].get(month, {"total": 0})
    
    return {
        "today": daily_usage["total"],
        "this_month": monthly_usage["total"],
        "all_time": log["total"]
    }
