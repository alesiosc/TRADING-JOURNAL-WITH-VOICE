# Update checklist to match new schema

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update checklist items
old_checklist = '''checklist_data = [
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("M1 Confirm", "Yes/No"),
            ("Well-Formed", "Perfect→Poor"),
            ("Level Types", "LIS/AVWAP/etc"),
            ("Entry Direction", "Buy/Sell"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience", "1-10 [1-3=Strong]"),
            ("Why trade?", "Reason")
        ]'''

new_checklist = '''checklist_data = [
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("M1 Confirm", "Yes/No"),
            ("M5 Form", "Perfect→Poor"),
            ("Entry Direction", "Buy/Sell"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience", "1-10 [1-3=Strong]"),
            ("Why trade?", "Reason")
        ]'''

content = content.replace(old_checklist, new_checklist)

# Update auto-check logic
content = content.replace('"Well-Formed"', '"M5 Form"')
content = content.replace('"Level Types"', '')
content = content.replace('"Status"', '')

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated checklist:")
print("  - Removed: Level Types, Status")
print("  - Renamed: Well-Formed -> M5 Form")
print("  - Kept: 8 checklist items")
