import os
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def delete_all_images():
    try:
        print("Fetching all resources from Cloudinary...")
        resources = cloudinary.api.resources(type="upload", max_results=500)
        total = len(resources["resources"])
        print(f"Found {total} images to delete")
        if total == 0:
            print("No images found")
            return
        
        # Auto-confirm deletion
        print("Auto-deleting all images...")
        deleted = 0
        for resource in resources["resources"]:
            public_id = resource["public_id"]
            try:
                cloudinary.uploader.destroy(public_id)
                deleted += 1
                print(f"Deleted {deleted}/{total}: {public_id}")
            except Exception as e:
                print(f"Failed: {public_id} - {e}")
        print(f"Complete! Deleted: {deleted}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_all_images()