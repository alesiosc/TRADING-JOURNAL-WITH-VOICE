import requests
import base64

def upload_to_imgur_anonymous(image_path):
    """Upload image to Imgur anonymously (no API key needed)"""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        headers = {'Authorization': 'Client-ID 546c25a59c58ad7'}  # Public anonymous client ID
        data = {'image': image_data, 'type': 'base64'}
        
        response = requests.post('https://api.imgur.com/3/image', headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()['data']['link']
        else:
            print(f"Upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error uploading: {e}")
        return None

def add_screenshots_to_notion_page(notion_client, page_id, screenshots):
    """Add screenshots as image blocks to Notion page"""
    if not screenshots:
        return
    
    children = []
    
    stage_names = {
        "pre_entry": "📸 Pre-Entry",
        "entry": "📸 Entry",
        "during": "📸 During Trade",
        "close": "📸 Close",
        "post_close": "📸 Post-Close"
    }
    
    for stage, data in screenshots.items():
        filepath = data['path']
        
        # Upload to Imgur
        print(f"Uploading {stage}...")
        image_url = upload_to_imgur_anonymous(filepath)
        
        if image_url:
            # Add heading
            children.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": stage_names.get(stage, stage)}}]
                }
            })
            
            # Add image block
            children.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": image_url}
                }
            })
        else:
            # Fallback: add file path
            children.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": f"{stage_names.get(stage, stage)}: {filepath}"}}],
                    "icon": {"emoji": "📸"}
                }
            })
    
    # Append all blocks to page
    if children:
        notion_client.blocks.children.append(block_id=page_id, children=children)
        print(f"Added {len(screenshots)} screenshots to Notion page")

if __name__ == "__main__":
    print("Screenshot uploader with Imgur integration ready")
