# Apply ONLY the safe fixes

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Text wrapping
if 'wrap="word"' not in content:
    content = content.replace(
        'scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11))',
        'scrolledtext.ScrolledText(right_panel, width=80, height=18, font=("Arial", 11), wrap="word")'
    )

# Fix 2: Better pattern matching
content = content.replace(
    '"Patience Score": "patience" in text',
    '"Patience Score": any(word in text for word in ["patience", "patient"])'
)

content = content.replace(
    '"5m Form": any(word in text for word in ["clean", "messy", "perfect", "poor", "well formed"])',
    '"5m Form": any(word in text for word in ["5-minute", "5 minute", "clean", "messy", "perfect", "poor", "well formed", "looking good"])'
)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied safe fixes")
