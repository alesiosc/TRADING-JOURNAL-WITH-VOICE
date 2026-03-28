# Fix checklist to EXACT Notion order

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# EXACT order from Notion (excluding AI_Analysis, Transcript, Name, Date)
old_checklist = '''checklist_data = [
            ("Level Types", "LIS/AVWAP/etc"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience Score", "1-10 [1-3=Strong]"),
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("Entry Direction", "Buy/Sell"),
            ("5m Form", "Perfect->Poor"),
            ("M1 Confirm", "Yes/No"),
            ("Screenshots", "Captured")
        ]'''

new_checklist = '''checklist_data = [
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("5m Form", "Perfect->Poor"),
            ("Level Types", "LIS/AVWAP/etc"),
            ("M1 Confirm", "Yes/No"),
            ("Entry Direction", "Buy/Sell"),
            ("Patience Score", "1-10 [1-3=Strong]"),
            ("Screenshots", "Captured")
        ]'''

content = content.replace(old_checklist, new_checklist)

# Update auto-check order to match
old_checks = '''checks = {
            "Level Types": any(word in text for word in ["lis", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Patience Score": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"]),
            "Screenshots": len(self.screenshot_mgr.screenshots) > 0
        }'''

new_checks = '''checks = {
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            "Level Types": any(word in text for word in ["lis", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "Patience Score": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "Screenshots": len(self.screenshot_mgr.screenshots) > 0
        }'''

content = content.replace(old_checks, new_checks)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Checklist order corrected to match Notion EXACTLY:")
print("1. Emotions")
print("2. Impulse")
print("3. M5 Pattern")
print("4. 5m Form")
print("5. Level Types")
print("6. M1 Confirm")
print("7. Entry Direction")
print("8. Patience Score")
print("9. Screenshots")
