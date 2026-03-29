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
    """Upload to Cloudinary (requires account) - returns high quality URL"""
    try:
        import cloudinary
        import cloudinary.uploader
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Upload with quality settings and folder organization
        result = cloudinary.uploader.upload(
            image_path,
            folder="TRADING JOURNAL WITH VOICE",  # Organize in folder
            quality="auto:best",  # Best quality
            fetch_format="auto"   # Optimal format
        )
        
        # Return URL with quality transformation to ensure full quality
        base_url = result['secure_url']
        # Insert quality parameter: /upload/q_100/ for maximum quality
        high_quality_url = base_url.replace('/upload/', '/upload/q_100/')
        return high_quality_url
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None

# Method 2 & 3: Add to Notion
def add_screenshots_as_blocks(notion_client, page_id, screenshots, upload_method="local"):
    """
    Add screenshots to Notion page content
    upload_method: "local", "cloudinary", "notion_blocks"
    """
    print(f"DEBUG add_screenshots_as_blocks: upload_method='{upload_method}', screenshots={list(screenshots.keys()) if screenshots else 'None'}")
    
    if not screenshots:
        return {}
    
    # Local only - don't add anything to Notion
    if upload_method == "local":
        print(f"Local mode: {len(screenshots)} screenshots saved locally only")
        return {}
    
    children = []
    uploaded_urls = {}
    stage_names = {
        "pre_entry": "Pre-Entry",
        "entry": "Entry",
        "during": "During",
        "close": "Close",
        "post_close": "Post-Close"
    }
    
    # Color mapping for Notion text colors (matches button colors)
    stage_colors = {
        "pre_entry": "purple",      # #9C27B0
        "entry": "green",            # #4CAF50
        "during": "orange",          # #FF9800
        "close": "red",              # #F44336
        "post_close": "default"      # White/default text
    }
    
    for stage, data in screenshots.items():
        filepath = data['path']
        stage_label = stage_names.get(stage, stage.replace("_", " ").title())
        
        # Add heading
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": stage_label + " Screenshot"}}]
            }
        })
        
        if upload_method == "notion_blocks":
            # Add file path reference in Notion
            uploaded_urls[stage_label] = filepath  # Store local path for Screenshots column
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
            
            print(f"DEBUG: Attempting Cloudinary upload for {stage_label}")
            print(f"DEBUG: Cloud name: {cloud_name}, API key exists: {bool(api_key)}, Secret exists: {bool(api_secret)}")
            
            if cloud_name and api_key and api_secret:
                print(f"DEBUG: Uploading {filepath} to Cloudinary...")
                image_url = upload_to_cloudinary(filepath, cloud_name, api_key, api_secret)
                print(f"DEBUG: Upload result: {image_url}")
                
                if image_url:
                    uploaded_urls[stage_label] = image_url
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
    
    return uploaded_urls

if __name__ == "__main__":
    print("Screenshot Upload Manager - 3 Methods Available")
    print("1. Local Only - Save locally, no Notion upload")
    print("2. Cloudinary - Upload to Cloudinary, show images in Notion")
    print("3. Notion Blocks - Save locally + add file paths to Notion page")
