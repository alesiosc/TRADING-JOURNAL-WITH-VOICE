# Update checklist to match Notion column order

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace checklist_data
old_checklist = '''checklist_data = [
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("M1 Confirm", "Yes/No"),
            ("M5 Form", "Perfect→Poor"),
            ("Entry Direction", "Buy/Sell"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience", "1-10 [1-3=Strong]"),
            ("Why trade?", "Reason")
        ]'''

# New order matching Notion (excluding Name, Date, AI_Analysis, Transcript, Screenshots)
new_checklist = '''checklist_data = [
            ("Level Types", "LIS/AVWAP/etc"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience Score", "1-10 [1-3=Strong]"),
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("Entry Direction", "Buy/Sell"),
            ("5m Form", "Perfect→Poor"),
            ("M1 Confirm", "Yes/No")
        ]'''

content = content.replace(old_checklist, new_checklist)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Checklist updated to match Notion column order:")
print("1. Level Types")
print("2. Impulse")
print("3. Emotions")
print("4. Patience Score")
print("5. M5 Pattern")
print("6. Entry Direction")
print("7. 5m Form")
print("8. M1 Confirm")
print("\nExcluded: Name, Date, AI_Analysis, Transcript, Screenshots")
