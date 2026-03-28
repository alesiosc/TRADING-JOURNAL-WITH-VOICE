# Update button colors
with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace colors
content = content.replace('("Entry", "entry", "#2196F3")', '("Entry", "entry", "#4CAF50")')
content = content.replace('("Close", "close", "#4CAF50")', '("Close", "close", "#F44336")')
content = content.replace('("Post-Close", "post_close", "#607D8B")', '("Post-Close", "post_close", "#424242")')

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Button colors updated!")
print("Entry: Green (#4CAF50)")
print("Close: Red (#F44336)")
print("Post-Close: Dark Grey (#424242)")
print("Define Crop: Black (already done)")
