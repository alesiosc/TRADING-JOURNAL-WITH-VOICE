import pyperclip
from datetime import datetime
import os

# Get whatever was just dictated (from clipboard)
text = pyperclip.paste().strip()

if text:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"./trading_notes/trade_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"Auto-saved to: {filename}")
    print("Processing will happen automatically...")
else:
    print("No text to save")
