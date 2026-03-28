from notion_client import Client

NOTION_TOKEN = "ntn_n26740308042HrXF93eaCzRbU9isw4oGBDqdsisLoCt45f"

print("Searching for databases...")
notion = Client(auth=NOTION_TOKEN)

# Search for all databases the integration can access
results = notion.search(filter={"property": "object", "value": "database"})

print(f"\nFound {len(results['results'])} database(s):\n")
for db in results['results']:
    title = db.get('title', [{}])[0].get('plain_text', 'Untitled')
    db_id = db['id']
    print(f"  - {title}")
    print(f"    ID: {db_id}\n")
