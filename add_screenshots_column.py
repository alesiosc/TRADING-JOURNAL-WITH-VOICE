from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

notion = Client(auth=NOTION_TOKEN)

print("Adding Screenshots media column...")

properties = {
    "Screenshots": {"files": {}}
}

notion.databases.update(database_id=DATABASE_ID, properties=properties)

print("SUCCESS! Screenshots column added (Files & media type)")
