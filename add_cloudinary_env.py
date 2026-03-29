# Add Cloudinary credentials to .env (optional - only if you want to use Cloudinary)

with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Cloudinary section if not exists
if 'CLOUDINARY' not in content:
    cloudinary_config = """
# Cloudinary (Optional - for private screenshot uploads)
# Sign up at cloudinary.com to get these
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here

# Screenshot Upload Method (cloudinary, imgur, or local)
SCREENSHOT_UPLOAD_METHOD=local
"""
    
    with open('.env', 'a', encoding='utf-8') as f:
        f.write(cloudinary_config)
    
    print(".env updated with Cloudinary config (optional)")
    print("\nDefault method: local (no upload)")
    print("\nTo use Cloudinary:")
    print("1. Sign up at cloudinary.com (free)")
    print("2. Get your credentials from dashboard")
    print("3. Update .env file")
    print("4. Change SCREENSHOT_UPLOAD_METHOD to 'cloudinary'")
else:
    print("Cloudinary config already in .env")
