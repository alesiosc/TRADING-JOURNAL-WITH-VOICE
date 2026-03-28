from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

notion = Client(auth=NOTION_TOKEN)

print("Fetching Notion database structure...\n")

db = notion.databases.retrieve(database_id=DATABASE_ID)

print("Column Order and Names:")
print("=" * 50)

for i, (prop_name, prop_data) in enumerate(db['properties'].items(), 1):
    prop_type = prop_data['type']
    print(f"{i}. {prop_name} ({prop_type})")

print("\n" + "=" * 50)
print("\nColumns to EXCLUDE from checklist:")
print("  - Name (title)")
print("  - Date")
print("  - AI_Analysis")
print("  - Transcript")
print("  - Screenshots")
