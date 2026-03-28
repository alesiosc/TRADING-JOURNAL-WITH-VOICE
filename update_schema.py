# Update code to match Notion column changes

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update field names in SYSTEM_PROMPT
old_prompt = '''FIELD MAPPINGS:
- M5_Pattern: Hammer, Shooting Star, Bullish Engulfing, Bearish Engulfing
- M1_Confirm: Yes, No
- Well_Formed: Perfect, Well-Formed, Decent, Questionable, Poor
- Level_Types: LIS, 2D AVWAP, Lower, Upper, Mid, Set 1, Set 2, BK Brown, Extremes (can be multiple)
- Entry_Direction: Buy, Sell
- Emotions: Zen, Anxious, FOMO, Revenge
- Impulse: 1-10 (number)
- Patience_Score: 1-10 (number, 1-3=strong, 7-10=weak)
- Status: Watching, Active, Closed'''

new_prompt = '''FIELD MAPPINGS:
- M5_Pattern: Hammer, Shooting Star, Bullish Engulfing, Bearish Engulfing (can be multiple)
- M1_Confirm: Yes, No
- M5_Form: Perfect, Well-Formed, Decent, Questionable, Poor
- Entry_Direction: Buy, Sell
- Emotions: Zen, Anxious, FOMO, Revenge
- Impulse: 1-10 (number)
- Patience_Score: 1-10 (number, 1-3=strong, 7-10=weak)'''

content = content.replace(old_prompt, new_prompt)

# Update JSON return format
old_json = '''{
  "M5_Pattern": "Hammer|Shooting Star|Bullish Engulfing|Bearish Engulfing",
  "M1_Confirm": "Yes|No",
  "Well_Formed": "Perfect|Well-Formed|Decent|Questionable|Poor",
  "Level_Types": ["LIS", "2D AVWAP", ...],
  "Entry_Direction": "Buy|Sell",
  "Emotions": "Zen|Anxious|FOMO|Revenge",
  "Impulse": 1-10,
  "Patience_Score": 1-10,
  "Status": "Watching|Active|Closed",
  "Summary": "Brief summary"
}'''

new_json = '''{
  "M5_Pattern": ["Hammer", "Shooting Star", "Bullish Engulfing", "Bearish Engulfing"],
  "M1_Confirm": "Yes|No",
  "M5_Form": "Perfect|Well-Formed|Decent|Questionable|Poor",
  "Entry_Direction": "Buy|Sell",
  "Emotions": "Zen|Anxious|FOMO|Revenge",
  "Impulse": 1-10,
  "Patience_Score": 1-10,
  "Summary": "Brief summary"
}'''

content = content.replace(old_json, new_json)

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated SYSTEM_PROMPT to match Notion changes")
