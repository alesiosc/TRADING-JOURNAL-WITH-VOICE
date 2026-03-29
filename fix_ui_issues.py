# Fix multiple issues

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Make status label text selectable
content = content.replace(
    'self.status_label = tk.Label(right_panel, text="Ready...", font=("Arial", 9), fg="green")',
    'self.status_label = tk.Text(right_panel, height=2, font=("Arial", 9), fg="green", bg="#f0f0f0", relief="flat", wrap="word")\n        self.status_label.insert("1.0", "Ready...")\n        self.status_label.config(state="disabled")'
)

# 2. Fix text wrapping in text area
content = content.replace(
    'self.text_area = scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11))',
    'self.text_area = scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11), wrap="word")'
)

# 3. Fix auto-check patterns
old_checks = '''checks = {
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

new_checks = '''checks = {
            "Emotions": any(word in text for word in ["zen", "calm", "anxious", "fomo", "revenge"]),
            "Impulse": any(word in text for word in ["impulse", "impulsive", "not impulsive", "very impulsive"]),
            "M5 Pattern": any(word in text for word in ["hammer", "shooting star", "engulfing"]),
            "5m Form": any(word in text for word in ["5-minute", "5 minute", "5m", "clean", "messy", "perfect", "poor", "well formed", "looking good"]),
            "Level Types": any(word in text for word in [" lis ", "lis,", "lis.", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"]),
            "M1 Confirm": any(word in text for word in ["confirm", "m1", "yes", "no"]),
            "Entry Direction": any(word in text for word in ["buy", "sell", "long", "short"]),
            "Patience Score": any(word in text for word in ["patience", "patient", "give it a"]),
            "Screenshots": len(self.screenshot_mgr.screenshots) > 0
        }'''

content = content.replace(old_checks, new_checks)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed:")
print("1. Status label now selectable (can copy error messages)")
print("2. Text area wraps words properly (no more 'formatio' + 'n')")
print("3. Better auto-check patterns:")
print("   - Patience: 'patient', 'give it a three'")
print("   - 5m Form: '5-minute', 'looking good'")
print("   - LIS: Fixed to avoid matching 'list'")
print("   - Impulse: 'impulsive', 'not impulsive'")
