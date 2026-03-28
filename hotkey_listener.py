import keyboard
import pyperclip
from datetime import datetime
import time

print("=== TRADING JOURNAL HOTKEY LISTENER ===")
print("Press Ctrl+Shift+T after dictating to auto-save")
print("Press Ctrl+C to exit\n")

def save_trade():
    text = pyperclip.paste().strip()
    if text:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./trading_notes/trade_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved: {filename}")
    else:
        print("No text in clipboard")

keyboard.add_hotkey('ctrl+shift+t', save_trade)

try:
    keyboard.wait()
except KeyboardInterrupt:
    print("\nStopped.")
