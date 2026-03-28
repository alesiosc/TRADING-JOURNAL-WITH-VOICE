import pyperclip
import time
from datetime import datetime

# Get text from clipboard (what Zavi just dictated)
text = pyperclip.paste()

if text:
    # Auto-generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"./trading_notes/trade_{timestamp}.txt"
    
    # Save automatically
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"Saved: {filename}")
else:
    print("No text in clipboard")
