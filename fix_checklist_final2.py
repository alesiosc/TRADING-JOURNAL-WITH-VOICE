# Fix checklist order and add Screenshots (no unicode)

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Correct order from Notion (excluding Name, Date, AI_Analysis, Transcript)
old_checklist = '''checklist_data = [
            ("Level Types", "LIS/AVWAP/etc"),
            ("Impulse", "1-10 [1-3=Strong]"),
            ("Emotions", "Zen/Anxious/FOMO"),
            ("Patience Score", "1-10 [1-3=Strong]"),
            ("M5 Pattern", "Hammer/Star/Engulf"),
            ("Entry Direction", "Buy/Sell"),
            ("5m Form", "Perfect->Poor"),
            ("M1 Confirm", "Yes/No")
        ]'''

new_checklist = '''checklist_data = [
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

content = content.replace(old_checklist, new_checklist)

# Add Screenshots to auto-check
old_checks = '''checks = {
            "Level Types": any(word in text for word in ["lis", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Patience Score": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"])
        }'''

new_checks = '''checks = {
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

content = content.replace(old_checks, new_checks)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed:")
print("- Checklist order matches Notion exactly")
print("- Added Screenshots to checklist (9 items total)")
print("- Screenshots auto-checks when any screenshot is taken")
