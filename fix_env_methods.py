# Update .env to reflect correct methods

with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the comment
content = content.replace('# Screenshot Upload Method (cloudinary, imgur, or local)', '# Screenshot Upload Method (local, cloudinary, or notion_blocks)')

with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated .env with correct upload methods:")
print("- local: Save locally only (default)")
print("- cloudinary: Upload to Cloudinary (requires account)")
print("- notion_blocks: Save locally + add file paths to Notion page")
