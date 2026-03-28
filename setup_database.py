from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

print("Setting up database structure...")
notion = Client(auth=NOTION_TOKEN)

# Define the properties to add
properties = {
    "Entry_Type": {
        "select": {
            "options": [
                {"name": "Trade", "color": "blue"},
                {"name": "Observation", "color": "green"},
                {"name": "Pass", "color": "yellow"},
                {"name": "Mindset Check", "color": "purple"},
                {"name": "Pre-Market", "color": "gray"}
            ]
        }
    },
    "M5_Anchor": {
        "select": {
            "options": [
                {"name": "Hammer", "color": "green"},
                {"name": "Shooting Star", "color": "red"}
            ]
        }
    },
    "Level_Type": {
        "select": {
            "options": [
                {"name": "Ludwig Blue", "color": "blue"},
                {"name": "Ludwig Red", "color": "red"},
                {"name": "LIS", "color": "purple"},
                {"name": "BKBrown", "color": "brown"}
            ]
        }
    },
    "M1_Confirm": {"checkbox": {}},
    "Internal_State": {
        "select": {
            "options": [
                {"name": "Zen", "color": "green"},
                {"name": "Anxious", "color": "yellow"},
                {"name": "FOMO", "color": "orange"},
                {"name": "Revenge", "color": "red"}
            ]
        }
    },
    "Impulse": {"number": {"format": "number"}},
    "Patience_Grade": {
        "select": {
            "options": [
                {"name": "A", "color": "green"},
                {"name": "B", "color": "blue"},
                {"name": "C", "color": "yellow"},
                {"name": "D", "color": "orange"},
                {"name": "F", "color": "red"}
            ]
        }
    },
    "Status": {
        "select": {
            "options": [
                {"name": "Watching", "color": "yellow"},
                {"name": "Active", "color": "blue"},
                {"name": "Closed", "color": "gray"}
            ]
        }
    },
    "Transcript": {"rich_text": {}},
    "AI_Analysis": {"rich_text": {}},
    "Date": {"date": {}}
}

# Update the database
notion.databases.update(
    database_id=DATABASE_ID,
    properties=properties
)

print("SUCCESS! Database structure created.")
print("\nAdded properties:")
for prop_name in properties.keys():
    print(f"  - {prop_name}")
