# Update auto-check logic to match new checklist

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the check_text_and_update_checklist function's checks dictionary
old_checks = '''checks = {
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"]),
            "M5 Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Patience": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "Why trade?": len(text) > 20
        }'''

new_checks = '''checks = {
            "Level Types": any(word in text for word in ["lis", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"]),
            "Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11)),
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Patience Score": "patience" in text or any(f"patience {i}" in text for i in range(1, 11)),
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"])
        }'''

content = content.replace(old_checks, new_checks)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Auto-check logic updated to match new checklist order!")
