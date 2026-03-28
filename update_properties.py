# Update property handling in process_trade function

with open('trading_journal_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove deleted fields
content = content.replace('if "Level_Types" in data and isinstance(data["Level_Types"], list):\n                properties["Level_Types"] = {"multi_select": [{"name": level} for level in data["Level_Types"]]}', '')
content = content.replace('if "Status" in data:\n                properties["Status"] = {"select": {"name": data["Status"]}}', '')

# Update Well_Formed to M5_Form
content = content.replace('"Well_Formed"', '"M5_Form"')
content = content.replace('properties["Well_Formed"]', 'properties["M5_Form"]')

# Update M5_Pattern to multi_select
content = content.replace('if "M5_Pattern" in data:\n                properties["M5_Pattern"] = {"select": {"name": data["M5_Pattern"]}}', 
                         'if "M5_Pattern" in data and isinstance(data["M5_Pattern"], list):\n                properties["M5_Pattern"] = {"multi_select": [{"name": pattern} for pattern in data["M5_Pattern"]]}')

with open('trading_journal_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated property handling:")
print("  - Removed: Level_Types, Status")
print("  - Renamed: Well_Formed -> M5_Form")
print("  - Changed: M5_Pattern to multi_select")
