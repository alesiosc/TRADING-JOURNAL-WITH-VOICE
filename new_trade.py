# Create a simple text file that Zavi can dictate into
# This file will be watched and auto-processed
import os
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"./trading_notes/trade_{timestamp}.txt"

# Create empty file
with open(filename, 'w', encoding='utf-8') as f:
    f.write("")

print(f"Created: {filename}")
print("Now use Zavi to dictate into this file!")

# Open the file in Notepad
os.system(f'notepad "{filename}"')
