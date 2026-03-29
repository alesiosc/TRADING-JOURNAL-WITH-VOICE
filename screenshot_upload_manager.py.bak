"""
Screenshot Upload Manager - 3 Methods
1. Cloudinary (private, reliable - requires account)
2. Local Only (no upload, just save locally)
3. Notion Blocks (hybrid - local files + paths in Notion page content)
"""

import os
from notion_client import Client

# Method 1: Cloudinary Upload
def upload_to_cloudinary(image_path, cloud_name, api_key, api_secret):
    """Upload to Cloudinary (requires account)"""
    try:
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        result = cloudinary.uploader.upload(image_path)
        return result['secure_url']
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None

# Method 2 & 3: Add to Notion
def add_screenshots_as_blocks(notion_client, page_id, screenshots, upload_method="local"):
    """
    Add screenshots to Notion page content
    upload_method: "local", "cloudinary", "notion_blocks"
    """
    if not screenshots:
        return
    
    # Local only - don't add anything to Notion
    if upload_method == "local":
        print(f"Local mode: {len(screenshots)} screenshots saved locally only")
        return
    
    children = []
    stage_names = {
        "pre_entry": "Pre-Entry Screenshot",
        "entry": "Entry Screenshot",
        "during": "During Trade Screenshot",
        "close": "Close Screenshot",
        "post_close": "Post-Close Screenshot"
    }
    
    for stage, data in screenshots.items():
        filepath = data['path']
        
        # Add heading
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": stage_names.get(stage, stage)}}]
            }
        })
        
        if upload_method == "notion_blocks":
            # Add file path reference in Notion
            children.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": f"Local file: {filepath}"}}],
                    "icon": {"emoji": "📁"}
                }
            })
        
        elif upload_method == "cloudinary":
            # Upload to Cloudinary and add image
            cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
            api_key = os.getenv("CLOUDINARY_API_KEY")
            api_secret = os.getenv("CLOUDINARY_API_SECRET")
            
            if cloud_name and api_key and api_secret:
                image_url = upload_to_cloudinary(filepath, cloud_name, api_key, api_secret)
                
                if image_url:
                    children.append({
                        "object": "block",
                        "type": "image",
                        "image": {
                            "type": "external",
                            "external": {"url": image_url}
                        }
                    })
                else:
                    children.append({
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [{"type": "text", "text": {"content": f"Upload failed. Local: {filepath}"}}],
                            "icon": {"emoji": "⚠️"}
                        }
                    })
            else:
                children.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"type": "text", "text": {"content": "Cloudinary not configured. Add credentials to .env"}}],
                        "icon": {"emoji": "⚠️"}
                    }
                })
    
    # Append blocks to page
    if children:
        notion_client.blocks.children.append(block_id=page_id, children=children)
        print(f"Added {len(screenshots)} screenshots to Notion (method: {upload_method})")

if __name__ == "__main__":
    print("Screenshot Upload Manager - 3 Methods Available")
    print("1. Local Only - Save locally, no Notion upload")
    print("2. Cloudinary - Upload to Cloudinary, show images in Notion")
    print("3. Notion Blocks - Save locally + add file paths to Notion page")
