from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

notion = Client(auth=NOTION_TOKEN)

print("Removing screenshot timestamp columns...")

# Remove the timestamp columns (set to null to remove)
properties = {
    "Screenshot_PreEntry_Time": None,
    "Screenshot_Entry_Time": None,
    "Screenshot_During_Time": None,
    "Screenshot_Close_Time": None,
    "Screenshot_PostClose_Time": None
}

try:
    notion.databases.update(database_id=DATABASE_ID, properties=properties)
    print("SUCCESS! Screenshot timestamp columns removed")
except Exception as e:
    print(f"Note: {e}")
    print("(Columns may not exist yet, that's okay)")
