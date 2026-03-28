from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

print("Testing Notion connection...")
notion = Client(auth=NOTION_TOKEN)
db = notion.databases.retrieve(database_id=DATABASE_ID)
print(f"SUCCESS! Connected to database: {db['title'][0]['plain_text']}")
print(f"\nDatabase has {len(db['properties'])} properties:")
for prop_name, prop_data in db['properties'].items():
    print(f"  - {prop_name} ({prop_data['type']})")
