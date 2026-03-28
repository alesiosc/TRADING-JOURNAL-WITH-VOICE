# Test uploading screenshot to Notion
from notion_client import Client
import os

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"
DATABASE_ID = "33109f62-78d4-80f6-9da5-dad7b6591885"

notion = Client(auth=NOTION_TOKEN)

# Check if we have any screenshots
screenshot_folder = "./screenshots"
if os.path.exists(screenshot_folder):
    files = [f for f in os.listdir(screenshot_folder) if f.endswith('.png')]
    if files:
        print(f"Found {len(files)} screenshots")
        print(f"Example: {files[0]}")
        
        # Notion API limitation: Files property only accepts external URLs
        # We need to either:
        # 1. Upload to external hosting (imgur, cloudinary, etc.)
        # 2. Use blocks API to add images to page content
        
        print("\nNOTE: Notion API requires external URLs for file uploads.")
        print("Options:")
        print("1. Keep screenshots local (current)")
        print("2. Upload to free image host (imgur, etc.)")
        print("3. Add as image blocks in page content")
    else:
        print("No screenshots found yet")
else:
    print("Screenshots folder doesn't exist yet")
