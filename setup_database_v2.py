from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

notion = Client(auth=NOTION_TOKEN)

print("Updating database schema...")

properties = {
    # Strategy
    "M5_Pattern": {
        "select": {
            "options": [
                {"name": "Hammer", "color": "green"},
                {"name": "Shooting Star", "color": "red"},
                {"name": "Bullish Engulfing", "color": "blue"},
                {"name": "Bearish Engulfing", "color": "orange"}
            ]
        }
    },
    "M1_Confirm": {
        "select": {
            "options": [
                {"name": "Yes", "color": "green"},
                {"name": "No", "color": "red"}
            ]
        }
    },
    "Well_Formed": {
        "select": {
            "options": [
                {"name": "Perfect", "color": "green"},
                {"name": "Well-Formed", "color": "blue"},
                {"name": "Decent", "color": "yellow"},
                {"name": "Questionable", "color": "orange"},
                {"name": "Poor", "color": "red"}
            ]
        }
    },
    "Level_Types": {
        "multi_select": {
            "options": [
                {"name": "LIS", "color": "purple"},
                {"name": "2D AVWAP", "color": "blue"},
                {"name": "Lower", "color": "red"},
                {"name": "Upper", "color": "green"},
                {"name": "Mid", "color": "yellow"},
                {"name": "Set 1", "color": "orange"},
                {"name": "Set 2", "color": "pink"},
                {"name": "BK Brown", "color": "brown"},
                {"name": "Extremes", "color": "gray"}
            ]
        }
    },
    
    # Mindset
    "Emotions": {
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
    "Patience_Score": {"number": {"format": "number"}},
    
    # Trade Data
    "Entry_Direction": {
        "select": {
            "options": [
                {"name": "Buy", "color": "green"},
                {"name": "Sell", "color": "red"}
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
    
    # Screenshots
    "Screenshot_PreEntry_Time": {"date": {}},
    "Screenshot_Entry_Time": {"date": {}},
    "Screenshot_During_Time": {"date": {}},
    "Screenshot_Close_Time": {"date": {}},
    "Screenshot_PostClose_Time": {"date": {}},
    
    # Meta
    "Transcript": {"rich_text": {}},
    "AI_Analysis": {"rich_text": {}},
    "Date": {"date": {}}
}

notion.databases.update(database_id=DATABASE_ID, properties=properties)

print("SUCCESS! Database updated with new schema.")
print("\nNew columns:")
for prop in properties.keys():
    print(f"  - {prop}")
