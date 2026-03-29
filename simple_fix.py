# Simpler fix - just update the auto-check patterns and text wrapping

with open('trading_journal_final_backup.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix text wrapping
content = content.replace(
    'scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11))',
    'scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11), wrap="word")'
)

# 2. Fix auto-check patterns
old_pattern = '"5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"])'
new_pattern = '"5m Form": any(word in text for word in ["5-minute", "5 minute", "5m", "clean", "messy", "perfect", "poor", "well formed", "looking good"])'
content = content.replace(old_pattern, new_pattern)

old_pattern = '"Level Types": any(word in text for word in ["lis", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"])'
new_pattern = '"Level Types": any(word in text for word in [" lis ", "lis,", "lis.", "avwap", "level", "upper", "lower", "mid", "set 1", "set 2", "bk brown", "extremes"])'
content = content.replace(old_pattern, new_pattern)

old_pattern = '"Impulse": any(word in text for word in ["impulse", "impulsive", "not impulsive", "very impulsive"])'
new_pattern_check = '"Impulse": any(word in text for word in ["impulse", "impulsive"])'
if old_pattern not in content:
    content = content.replace(
        '"Impulse": "impulse" in text or any(f"impulse {i}" in text for i in range(1, 11))',
        new_pattern_check
    )

old_pattern = '"Patience Score": "patience" in text or any(f"patience {i}" in text for i in range(1, 11))'
new_pattern = '"Patience Score": any(word in text for word in ["patience", "patient", "give it a"])'
content = content.replace(old_pattern, new_pattern)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed:")
print("- Text wrapping (no more word breaks)")
print("- Better pattern matching for checklist")
