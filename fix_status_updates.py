# Also need to update the status label updates throughout the code

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all status_label.config(text=...) with proper Text widget updates
import re

# Find all status label updates
pattern = r'self\.status_label\.config\(text=f?"([^"]+)"(?:, fg="([^"]+)")?\)'

def replace_status(match):
    text = match.group(1)
    color = match.group(2) if match.group(2) else "green"
    return f'self.status_label.config(state="normal", fg="{color}")\n        self.status_label.delete("1.0", "end")\n        self.status_label.insert("1.0", f"{text}")\n        self.status_label.config(state="disabled")'

content = re.sub(pattern, replace_status, content)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated all status label updates to work with Text widget")
